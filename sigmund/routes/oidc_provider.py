"""A minimal OpenID Connect (OIDC) provider, so that other applications (in
particular LibreChat) can use Sigmund's existing login as single sign-on.

This module is only loaded when SIGMUND_OIDC_ENABLED=1 (see server.py). It adds
the following routes and does not touch any existing route:

    /.well-known/openid-configuration   discovery document
    /oidc/jwks                          public signing key
    /oidc/authorize                     authorization endpoint
    /oidc/token                         token endpoint
    /oidc/userinfo                      userinfo endpoint
    /oidc/logout                        end-session endpoint (RP-Initiated
                                        Logout)

Scope and deliberate limitations
--------------------------------
- There is exactly one client, which is configured through the environment
  (see config.py). There is no dynamic client registration.
- Only the authorization code flow is supported, with optional PKCE (S256).
- No refresh tokens are issued. RP-Initiated Logout is supported through
  /oidc/logout: when the user logs out of the client, the user is also logged
  out of Sigmund and his or her access tokens are revoked. The reverse is not
  implemented: logging out of Sigmund does not end the client's session.
- prompt=login and max_age are ignored. prompt=none is honored.
- Authorization codes and access tokens are stored in Redis (hashed) and
  expire automatically. Access tokens are also indexed by user, so that they
  can be revoked at logout. ID tokens are signed with RS256.
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
from flask_login import current_user, logout_user
from .. import config
from .. import utils
from .. import librechat
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
# An id_token_hint is an ID token (at most a few kB) and not an attack
# surface, but the length is limited to avoid parsing absurd input.
MAX_HINT_LENGTH = 4096


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
        'end_session_endpoint': issuer + '/oidc/logout',
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
            'Invalid request',
            'The application that sent you here is not configured correctly.',
            400)

    def fail(error, description):
        return _redirect_with(redirect_uri, error=error,
                              error_description=description, state=state)

    if response_type != 'code':
        return fail('unsupported_response_type',
                    'only response_type=code is supported')
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
        return redirect(url_for('app.oidc_login'))
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
    # The user is allowed in, so LibreChat's subscription gate should be
    # given the same state that was just verified here.
    _sync_librechat_subscription(username)
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


@oidc_blueprint.route('/oidc/logout')
def end_session():
    """RP-Initiated Logout (OpenID Connect). The client navigates the user's
    browser here when the user logs out of the client:

        /oidc/logout?id_token_hint=<id token>&post_logout_redirect_uri=<uri>

    The ID token serves as a hint that identifies the user. It is verified
    (signature, issuer, audience), but an expired token is accepted, because
    a client's session can outlive the ID tokens that Sigmund issues (one
    hour). The current Sigmund session is only ended when the hint belongs
    to the user behind this browser; a hint for another user merely revokes
    that user's access tokens. Without a valid hint, the current user is
    logged out, like on Sigmund's own /logout route. Afterwards the user is
    sent back to the client, but only if the post-logout URI is whitelisted
    (see config.oidc_post_logout_redirect_uris).
    """
    id_token_hint = request.args.get('id_token_hint')
    claims = _verify_id_token(id_token_hint) if id_token_hint else None
    if id_token_hint and claims is None:
        logger.info('oidc: ignoring invalid id_token_hint')
    subject = claims.get('sub') if claims is not None else None
    username = current_user.get_id() if current_user.is_authenticated else None
    if subject is not None:
        _revoke_access_tokens(subject)
    if username is not None:
        _revoke_access_tokens(username)
    session.clear()
    logout_user()
    post_logout_redirect_uri = request.args.get('post_logout_redirect_uri')
    if post_logout_redirect_uri in config.oidc_post_logout_redirect_uris:
        return _no_store(_redirect_with(post_logout_redirect_uri,
                                        state=request.args.get('state')))
    return _no_store(redirect(url_for('app.oidc_login')))


# -- Signing -----------------------------------------------------------------

def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode('ascii')


def _b64url_decode(data: str) -> bytes:
    return base64.urlsafe_b64decode(data + '=' * (-len(data) % 4))


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
        self.public_key = private_key.public_key()
        numbers = self.public_key.public_numbers()
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


def _verify_id_token(id_token):
    """Verifies that an ID token was signed by this provider and issued to
    the configured client, and returns its claims. Malformed tokens, invalid
    signatures, and tokens from other issuers or for other clients return
    None. An expired token is accepted: ID tokens are used here only as a
    hint that identifies the user, and a client's session can outlive them
    (the OpenID Connect RP-Initiated Logout specification recommends
    accepting expired ID tokens as hints).
    """
    try:
        if len(id_token) > MAX_HINT_LENGTH:
            return None
        header_b64, payload_b64, signature_b64 = id_token.split('.')
        header = json.loads(_b64url_decode(header_b64))
        if header.get('alg') != 'RS256':
            return None
        signature = _b64url_decode(signature_b64)
        _signer().public_key.verify(
            signature, f'{header_b64}.{payload_b64}'.encode('ascii'),
            padding.PKCS1v15(), hashes.SHA256())
        claims = json.loads(_b64url_decode(payload_b64))
        if not isinstance(claims, dict) or claims.get('iss') != config.oidc_issuer:
            return None
        aud = claims.get('aud')
        audiences = aud if isinstance(aud, list) else [aud]
        if config.oidc_client_id not in audiences:
            return None
        return claims
    except Exception:
        logger.info('oidc: could not verify id_token_hint')
        return None


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
    for uri in config.oidc_post_logout_redirect_uris:
        if not _is_secure_or_local(uri):
            problems.append(f'post-logout redirect URI must use https: {uri}')
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


def _user_index_key(username: str) -> str:
    return KEY_PREFIX + 'user_tokens:' + username


def _store(kind: str, secret: str, payload: dict, ttl: int):
    key = _key(kind, secret)
    redis_client.setex(key, ttl, json.dumps(payload))
    if kind == 'access':
        # Secondary index from username to token keys, so that all access
        # tokens of a user can be revoked at logout. The set is given the TTL
        # of the newest token; members that outlive their token (only
        # possible if the TTLs would ever differ) are harmless, because
        # deleting an expired key does nothing.
        index_key = _user_index_key(payload['username'])
        redis_client.sadd(index_key, key)
        redis_client.expire(index_key, ttl)


def _revoke_access_tokens(username: str):
    """Deletes all outstanding access tokens of a user, so that requests
    presenting them fail immediately. Called by the end-session endpoint.
    """
    index_key = _user_index_key(username)
    keys = redis_client.smembers(index_key)
    if not keys:
        return
    pipe = redis_client.pipeline()
    for key in keys:
        pipe.delete(key)
    pipe.delete(index_key)
    pipe.execute()


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


def _sync_librechat_subscription(username):
    """Pushes the user's current subscription state to LibreChat, so that
    LibreChat's subscription gate always sees the same state that this
    authorization request just verified. This also covers users who
    subscribed before they ever logged into LibreChat: the Stripe webhook
    cannot sync those, because LibreChat does not know them yet (it answers
    404 user_not_found), so the first login is the moment their state
    arrives. Failures are logged and never block the login.
    """
    if not librechat.enabled():
        return
    try:
        user = DbUser.query.filter_by(username=username).one()
        record = (Subscription.query
                  .filter(Subscription.user_id == user.user_id)
                  .order_by(Subscription.to_date.desc(),
                            Subscription.from_date.desc())
                  .first())
        now = datetime.utcnow()
        active = (record is not None and record.from_date is not None
                  and record.to_date is not None
                  and record.from_date <= now < record.to_date)
        librechat.sync_subscription(
            user.email,
            record.to_date if active else None,
            status='active' if active else None)
    except Exception as e:
        logger.error(f'oidc: failed to sync the LibreChat subscription '
                     f'of {username}: {e}')


def _display_name(username: str) -> str:
    # This mirrors Sigmund.username(): Google usernames look like
    # 'Name (google)::unique_id', and the suffix is replaced by '(Google)'.
    # The Sigmund class itself is not instantiated here, because that has
    # side effects, such as creating the user.
    if '(google)::' in username:
        return username.split('(google)::')[0] + '(Google)'
    return username


def _email(username: str) -> str:
    """Returns the user's registered email address (see
    DatabaseManager.set_email). Every user has one. LibreChat matches users
    by this claim, and the Stripe webhook identifies them by the same
    address (see sigmund/librechat.py).
    """
    user = DbUser.query.filter_by(username=username).first()
    return user.email


def _user_claims(username: str, scope: str) -> dict:
    """Builds the claims for the ID token and userinfo. The display name is
    derived from the username (see _display_name), and the email address is
    taken from the database if one has been registered on login (see _email).
    Otherwise, a stable address is derived from the username.
    """
    scopes = scope.split()
    claims = {'sub': username}
    if 'profile' in scopes:
        claims['name'] = _display_name(username)
        claims['preferred_username'] = username
    if 'email' in scopes:
        claims['email'] = _email(username)
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
