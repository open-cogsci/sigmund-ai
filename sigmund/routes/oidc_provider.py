"""A minimal OpenID Connect (OIDC) provider, so that other applications (in
particular LibreChat) can use Sigmund's existing login as single sign-on.

This module is only loaded when SIGMUND_OIDC_ENABLED=1 (see server.py). It adds
the following routes and does not touch any existing route:

    /.well-known/openid-configuration   discovery document
    /oidc/jwks                          public signing key
    /oidc/authorize                     authorization endpoint
    /oidc/token                         token endpoint
    /oidc/userinfo                      userinfo endpoint

Scope and deliberate limitations
--------------------------------
- There is exactly one client, which is configured through the environment
  (see config.py). There is no dynamic client registration.
- Only the authorization code flow is supported, with optional PKCE (S256).
- No refresh tokens are issued, and there is no end-session (logout) endpoint.
  Logging out of the client does not log the user out of Sigmund and vice versa.
- prompt=login and max_age are ignored. prompt=none is honored.
- Authorization codes and access tokens are stored in Redis (hashed) and expire
  automatically. ID tokens are signed with RS256.
- Access is checked when the authorization request is made. A suspension or
  expired subscription therefore does not end sessions that the client has
  already established.
"""
import base64
import hashlib
import hmac
import json
import logging
import re
import secrets
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import parse_qsl, unquote_plus, urlencode, urlsplit, \
    urlunsplit
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from flask import Blueprint, current_app, jsonify, redirect, request, \
    session, url_for
from flask_login import current_user
from .. import config
from .. import utils
from ..redis_client import redis_client
from ..database.models import db, User as DbUser, Subscription
from .app import get_theme

logger = logging.getLogger('sigmund')
oidc_blueprint = Blueprint('oidc', __name__)

CODE_TTL = 60
ACCESS_TOKEN_TTL = 3600
ID_TOKEN_TTL = 3600
KEY_PREFIX = 'sigmund:oidc:'
DEFAULT_SECRET_KEY = '0123456789ABCDEF'
LOCAL_HOSTS = ('localhost', '127.0.0.1')
PKCE_PATTERN = re.compile(r'[A-Za-z0-9\-._~]{43,128}')
MAX_PARAM_LENGTH = 512


# -- Endpoints ---------------------------------------------------------------

@oidc_blueprint.route('/.well-known/openid-configuration')
def discovery():
    """LibreChat first inspects this endpoint to learn how the OIDC provider
    is configured.
    """
    issuer = config.oidc_issuer
    response = jsonify({
        'issuer': issuer,
        'authorization_endpoint': issuer + '/oidc/authorize',
        'token_endpoint': issuer + '/oidc/token',
        'userinfo_endpoint': issuer + '/oidc/userinfo',
        'jwks_uri': issuer + '/oidc/jwks',
        'response_types_supported': ['code'],
        'grant_types_supported': ['authorization_code'],
        'subject_types_supported': ['public'],
        'id_token_signing_alg_values_supported': ['RS256'],
        'scopes_supported': ['openid', 'profile', 'email'],
        'token_endpoint_auth_methods_supported': [
            'client_secret_basic', 'client_secret_post'],
        'code_challenge_methods_supported': ['S256'],
        'claims_supported': ['sub', 'iss', 'aud', 'exp', 'iat', 'auth_time',
                             'nonce', 'name', 'preferred_username', 'email',
                             'email_verified'],
    })
    response.headers['Cache-Control'] = 'public, max-age=3600'
    return response


@oidc_blueprint.route('/oidc/jwks')
def jwks():
    """Publishes the public key."""
    response = jsonify({'keys': [_signer().jwk]})
    response.headers['Cache-Control'] = 'public, max-age=3600'
    return response


@oidc_blueprint.route('/oidc/authorize')
def authorize():
    """Is called by LibreChat to initiate the authorization process.    
    If the user is already logged in, this redirects back to the callback
    provided by LibreChat. If the user is not yet logged in, the user is 
    first redirected to Sigmund's login endpoints, from where he or she
    will be redirected to the LibreChat callback.
    
    JSON Content of the request:
    {
        "client_id": "must_match_allowed_client_in_config",
        "redirect_uri": "must_match_allowed_redirect_uri_in_config",
        "response_type": "code",
        "scope": "must_contain_openid",
        "state": "random_state_string",
        "code_challenge": "random_code_challenge_string",
        "code_challenge_method": "S256",
        "nonce": "random_nonce_string"
    }
    """
    args = request.args
    redirect_uri = args.get('redirect_uri', '')
    state = args.get('state')
    scope = args.get('scope', '')
    nonce = args.get('nonce')
    response_type = args.get('response_type')
    code_challenge = args.get('code_challenge')
    client_id = args.get('client_id')
    prompt = args.get('prompt', '')
    # Until the client and redirect URI are verified, errors must not be sent
    # to the redirect URI, because that would make this an open redirect.
    if client_id != config.oidc_client_id or \
            redirect_uri not in config.oidc_redirect_uris:
        logger.warning('oidc: rejected request with unknown client or redirect_uri')
        return _error_page(
            'Invalid request. The application that sent you here is not configured correctly.',
            400)

    def fail(error, description):
        return _redirect_with(redirect_uri, error=error,
                              error_description=description, state=state)

    if response_type != 'code':
        return fail('unsupported_response_type only response_type=code is supported')
    if 'openid' not in scope.split():
        return fail('invalid_scope', 'the openid scope is required')
    if any(len(v) > MAX_PARAM_LENGTH for v in (scope, state or '', nonce or '')):
        return fail('invalid_request', 'parameter too long')
    if code_challenge is not None:
        if args.get('code_challenge_method') != 'S256':
            return fail('invalid_request',
                        'code_challenge_method must be S256')
        if not PKCE_PATTERN.fullmatch(code_challenge):
            return fail('invalid_request', 'malformed code_challenge')
    if not current_user.is_authenticated:
        if 'none' in prompt.split():
            return fail('login_required', 'the user is not logged in')
        # Sigmund's existing login (forum or Google) takes over, and sends the
        # user back here afterwards. See post_login_redirect() in app.py.
        session['oidc_next'] = request.full_path
        return redirect(url_for('app.login'))
    username = current_user.get_id()
    reason = _access_denied_reason(username)
    if reason == 'suspended':
        logger.info(f'oidc: refused suspended user {username}')
        return _error_page(
            'Access denied',
            'Your account is currently suspended. Please visit the '
            '[suspension page](/suspended) to learn more.', 403)
    if reason == 'subscription':
        logger.info(f'oidc: refused user without subscription {username}')
        return _error_page(
            'Subscription required',
            'An active subscription is required. You can '
            f'[subscribe here]({url_for("store.subscription_page")}).', 403)
    code = secrets.token_urlsafe(32)
    _store('code', code, {
        'client_id': config.oidc_client_id,
        'redirect_uri': redirect_uri,
        'username': username,
        'scope': scope,
        'nonce': nonce,
        'code_challenge': code_challenge,
        'auth_time': int(time.time())
    }, CODE_TTL)
    logger.info(f'oidc: issued authorization code for {username}')
    return _redirect_with(redirect_uri, code=code, state=state)


@oidc_blueprint.route('/oidc/token', methods=['POST'])
def token():
    """Returns a token signed with the private key. LibreChat can verify it
    with the public key published by /oidc/jwks.
    """
    # Client authentication (client_secret_basic or client_secret_post)
    auth = request.authorization
    if auth is not None and getattr(auth, 'type', 'basic') == 'basic':
        # RFC 6749 requires the credentials to be form-urlencoded first
        client_id = unquote_plus(auth.username or '')
        client_secret = unquote_plus(auth.password or '')
    else:
        client_id = request.form.get('client_id')
        client_secret = request.form.get('client_secret')
    if client_id != config.oidc_client_id or \
            client_secret != config.oidc_client_secret:
        logger.warning('oidc: token request with invalid client credentials')
        return _token_error('invalid_client', 'client authentication failed',
                            401, basic=auth is not None)
    if request.form.get('grant_type') != 'authorization_code':
        return _token_error('unsupported_grant_type',
                            'only authorization_code is supported')
    code = request.form.get('code')
    if not code:
        return _token_error('invalid_request', 'missing code')
    payload = _consume('code', code)
    if payload is None:
        return _token_error('invalid_grant',
                            'the code is invalid, expired or already used')
    if payload['client_id'] != config.oidc_client_id or \
            payload['redirect_uri'] != request.form.get('redirect_uri'):
        return _token_error('invalid_grant', 'client or redirect_uri mismatch')
    if payload.get('code_challenge'):
        verifier = request.form.get('code_verifier', '')
        computed = _b64url(hashlib.sha256(verifier.encode()).digest())
        if not PKCE_PATTERN.fullmatch(verifier) or \
                not _safe_eq(computed, payload['code_challenge']):
            return _token_error('invalid_grant', 'PKCE verification failed')
    username, scope = payload['username'], payload['scope']
    now = int(time.time())
    id_claims = {
        'iss': config.oidc_issuer,
        'aud': config.oidc_client_id,
        'iat': now,
        'exp': now + ID_TOKEN_TTL,
        'auth_time': payload['auth_time']
    }
    if payload.get('nonce'):
        id_claims['nonce'] = payload['nonce']
    id_claims.update(_user_claims(username, scope))
    access_token = secrets.token_urlsafe(32)
    _store('access', access_token, {'username': username, 'scope': scope},
           ACCESS_TOKEN_TTL)
    logger.info(f'oidc: issued tokens for {username}')
    return _no_store(jsonify({
        'access_token': access_token,
        'token_type': 'Bearer',
        'expires_in': ACCESS_TOKEN_TTL,
        'scope': scope,
        'id_token': _signer().sign(id_claims)
    }))


@oidc_blueprint.route('/oidc/userinfo', methods=['GET', 'POST'])
def userinfo():
    scheme, _, access_token = request.headers.get(
        'Authorization', '').partition(' ')
    data = None
    if scheme.lower() == 'bearer' and access_token.strip():
        data = _lookup('access', access_token.strip())
    if data is None:
        response = jsonify(error='invalid_token')
        response.status_code = 401
        response.headers['WWW-Authenticate'] = 'Bearer error="invalid_token"'
        return _no_store(response)
    return _no_store(jsonify(_user_claims(data['username'], data['scope'])))




# -- Signing -----------------------------------------------------------------

def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode('ascii')


def _b64url_uint(value: int) -> str:
    return _b64url(value.to_bytes((value.bit_length() + 7) // 8, 'big'))


def _json_bytes(data: dict) -> bytes:
    return json.dumps(data, separators=(',', ':')).encode('utf-8')


class _Signer:
    """Signs JWTs with RS256 and exposes the matching public key as a JWK."""

    def __init__(self, private_key):
        if not isinstance(private_key, rsa.RSAPrivateKey):
            raise ValueError('the OIDC signing key must be an RSA key')
        if private_key.key_size < 2048:
            raise ValueError('the OIDC signing key must be at least 2048 bits')
        self._private_key = private_key
        numbers = private_key.public_key().public_numbers()
        n, e = _b64url_uint(numbers.n), _b64url_uint(numbers.e)
        # The key id is the RFC 7638 thumbprint of the public key
        thumbprint_input = json.dumps({'e': e, 'kty': 'RSA', 'n': n},
                                      separators=(',', ':'), sort_keys=True)
        self.kid = _b64url(hashlib.sha256(thumbprint_input.encode()).digest())
        self.jwk = {'kty': 'RSA', 'use': 'sig', 'alg': 'RS256',
                    'kid': self.kid, 'n': n, 'e': e}

    def sign(self, claims: dict) -> str:
        header = {'alg': 'RS256', 'typ': 'JWT', 'kid': self.kid}
        signing_input = '{}.{}'.format(_b64url(_json_bytes(header)),
                                       _b64url(_json_bytes(claims)))
        signature = self._private_key.sign(
            signing_input.encode('ascii'), padding.PKCS1v15(), hashes.SHA256())
        return '{}.{}'.format(signing_input, _b64url(signature))


def _load_private_key():
    pem = config.oidc_private_key
    if not pem and config.oidc_private_key_file:
        pem = Path(config.oidc_private_key_file).read_text()
    if not pem:
        raise ValueError('no OIDC signing key configured '
                         '(SIGMUND_OIDC_PRIVATE_KEY_FILE)')
    # Allow a PEM key in a single-line environment variable
    pem = pem.replace('\\n', '\n')
    return serialization.load_pem_private_key(pem.encode(), password=None)


def _is_secure_or_local(url: str) -> bool:
    parts = urlsplit(url)
    return parts.scheme == 'https' or (
        parts.scheme == 'http' and parts.hostname in LOCAL_HOSTS)


def init_oidc(app):
    """Validates the configuration and prepares the signing key. Raises a
    ValueError describing all problems if the provider cannot be run safely.
    Called from server.py, which then skips the provider (but keeps running
    Sigmund) if this fails.
    """
    problems = []
    if not config.oidc_client_secret or len(config.oidc_client_secret) < 32:
        problems.append('SIGMUND_OIDC_CLIENT_SECRET must be set and at least '
                        '32 characters long')
    if not config.oidc_redirect_uris:
        problems.append('SIGMUND_OIDC_REDIRECT_URIS must be set')
    for uri in config.oidc_redirect_uris:
        if not _is_secure_or_local(uri):
            problems.append(f'redirect URI must use https: {uri}')
    if not _is_secure_or_local(config.oidc_issuer):
        problems.append('the issuer (SIGMUND_OIDC_ISSUER or FLASK_SERVER_URL) '
                        'must use https')
    if app.config.get('SECRET_KEY') in (None, '', DEFAULT_SECRET_KEY):
        problems.append('FLASK_SECRET_KEY must be set to a non-default value')
    signer = None
    try:
        signer = _Signer(_load_private_key())
    except Exception as e:
        problems.append(f'signing key: {e}')
    if problems:
        raise ValueError('; '.join(problems))
    app.extensions['sigmund_oidc'] = signer


def _signer() -> _Signer:
    return current_app.extensions['sigmund_oidc']


# -- Storage of codes and tokens ---------------------------------------------

def _key(kind: str, secret: str) -> str:
    # Only a hash of the secret is stored, so that a Redis dump doesn't reveal
    # valid codes or tokens
    return KEY_PREFIX + kind + ':' + hashlib.sha256(
        secret.encode()).hexdigest()


def _store(kind: str, secret: str, payload: dict, ttl: int):
    redis_client.setex(_key(kind, secret), ttl, json.dumps(payload))


def _lookup(kind: str, secret: str):
    value = redis_client.get(_key(kind, secret))
    return json.loads(value) if value else None


def _consume(kind: str, secret: str):
    """Fetches and deletes in one atomic step, so that a code can be used only
    once."""
    pipe = redis_client.pipeline()
    pipe.get(_key(kind, secret))
    pipe.delete(_key(kind, secret))
    value, _ = pipe.execute()
    return json.loads(value) if value else None


# -- Users and claims --------------------------------------------------------

def _access_denied_reason(username: str):
    """Returns None if the user may use the client application, or a short
    reason string. This mirrors the checks in chat_page() without creating a
    Sigmund instance, which would have side effects (creating the user).
    """
    user = DbUser.query.filter_by(username=username).first()
    if user is not None and user.suspended:
        return 'suspended'
    if config.subscription_required:
        if user is None:
            return 'subscription'
        now = datetime.utcnow()
        active = db.session.query(db.exists().where(
            (Subscription.user_id == user.user_id) &
            (Subscription.from_date <= now) &
            (Subscription.to_date > now))).scalar()
        if not active:
            return 'subscription'
    return None


def _display_name(username: str) -> str:
    # Google usernames look like 'Name (google)::unique_id'
    match = re.match(r'^(.*) \(google\)::', username)
    return match.group(1) if match else username


def _email(username: str) -> str:
    """Sigmund doesn't store email addresses, and users can be known by Google
    or by forum accounts. We therefore derive a stable, unique, but
    non-deliverable address from the username. This is the one place to change
    if real email addresses become available.
    """
    slug = re.sub(r'[^a-z0-9]+', '-', username.lower()).strip('-')[:40]
    digest = hashlib.sha256(username.encode()).hexdigest()[:8]
    return f'{slug or "user"}.{digest}@{config.oidc_email_domain}'


def _user_claims(username: str, scope: str) -> dict:
    scopes = scope.split()
    claims = {'sub': username}
    if 'profile' in scopes:
        claims['name'] = _display_name(username)
        claims['preferred_username'] = username
    if 'email' in scopes:
        claims['email'] = _email(username)
        # Not a real mailbox, but we do vouch for its uniqueness
        claims['email_verified'] = True
    return claims


# -- Helpers -----------------------------------------------------------------

def _safe_eq(a, b) -> bool:
    return hmac.compare_digest((a or '').encode(), (b or '').encode())


def _redirect_with(redirect_uri: str, **params):
    parts = urlsplit(redirect_uri)
    query = parse_qsl(parts.query, keep_blank_values=True)
    query += [(k, v) for k, v in params.items() if v is not None]
    return redirect(urlunsplit(parts._replace(query=urlencode(query))))


def _error_page(title: str, text: str, status: int):
    return utils.render('info-page.html',
                        content=utils.md(f'**{title}**\n\n{text}'),
                        theme=get_theme()), status


def _no_store(response):
    response.headers['Cache-Control'] = 'no-store'
    response.headers['Pragma'] = 'no-cache'
    return response


def _token_error(error: str, description: str, status: int = 400,
                 basic: bool = False):
    response = jsonify(error=error, error_description=description)
    response.status_code = status
    if basic:
        response.headers['WWW-Authenticate'] = 'Basic realm="sigmund"'
    return _no_store(response)
