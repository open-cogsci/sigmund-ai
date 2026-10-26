import base64
import hashlib
import json
import time
import unittest
from urllib.parse import urlsplit, parse_qs
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from sigmund.server import create_app, SigmundConfig
from sigmund import config

CLIENT_ID = 'librechat'
CLIENT_SECRET = 'a-client-secret-that-is-long-enough-for-tests'
REDIRECT_URI = 'https://lc.example.org/oauth/openid/callback'
POST_LOGOUT_URI = 'https://lc.example.org/login'
ISSUER = 'https://sigmund.example.org'
OIDC_SETTINGS = ('oidc_enabled', 'oidc_issuer', 'oidc_client_id',
                 'oidc_client_secret', 'oidc_redirect_uris',
                 'oidc_post_logout_redirect_uris', 'oidc_private_key',
                 'oidc_private_key_file', 'oidc_email_domain',
                 'subscription_required')


class OIDCTestConfig(SigmundConfig):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    # The default secret key is refused by the OIDC provider
    SECRET_KEY = 'a-secret-key-for-unit-tests-only'


def b64url_decode(data):
    return base64.urlsafe_b64decode(data + '=' * (-len(data) % 4))


def b64url(data):
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode()


class BaseOIDCTestCase(unittest.TestCase):

    enabled = True

    def setUp(self):
        self._saved = {name: getattr(config, name) for name in OIDC_SETTINGS}
        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        config.oidc_enabled = self.enabled
        config.oidc_issuer = ISSUER
        config.oidc_client_id = CLIENT_ID
        config.oidc_client_secret = CLIENT_SECRET
        config.oidc_redirect_uris = [REDIRECT_URI]
        config.oidc_post_logout_redirect_uris = [POST_LOGOUT_URI]
        config.oidc_private_key_file = None
        config.oidc_private_key = key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption()).decode()
        config.oidc_email_domain = 'sigmund.invalid'
        config.subscription_required = False
        self.app = create_app(config_class=OIDCTestConfig)
        self.client = self.app.test_client(use_cookies=True)
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        self.app_context.pop()
        for name, value in self._saved.items():
            setattr(config, name, value)

    def login(self, follow_redirects=False):
        # We don't follow the redirect by default. It would lead to the chat
        # page, which creates the user in the database as a side effect.
        return self.client.post(
            '/login', data=dict(username='test', password='test'),
            follow_redirects=follow_redirects)

    def authorize_params(self, **overrides):
        params = dict(client_id=CLIENT_ID, redirect_uri=REDIRECT_URI,
                      response_type='code', scope='openid profile email',
                      state='state-123', nonce='nonce-456')
        params.update(overrides)
        return {k: v for k, v in params.items() if v is not None}

    def authorize(self, **overrides):
        return self.client.get('/oidc/authorize',
                               query_string=self.authorize_params(**overrides))

    def get_code(self, **overrides):
        self.login()
        response = self.authorize(**overrides)
        assert response.status_code == 302
        query = parse_qs(urlsplit(response.headers['Location']).query)
        assert query['state'] == ['state-123']
        return query['code'][0]

    def exchange(self, code, secret=CLIENT_SECRET, **extra):
        credentials = base64.b64encode(
            f'{CLIENT_ID}:{secret}'.encode()).decode()
        data = dict(grant_type='authorization_code', code=code,
                    redirect_uri=REDIRECT_URI)
        data.update(extra)
        return self.client.post(
            '/oidc/token', data=data,
            headers={'Authorization': f'Basic {credentials}'})

    def verify_id_token(self, id_token):
        header_b64, payload_b64, signature_b64 = id_token.split('.')
        header = json.loads(b64url_decode(header_b64))
        jwks = self.client.get('/oidc/jwks').get_json()
        jwk, = [k for k in jwks['keys'] if k['kid'] == header['kid']]
        public_key = rsa.RSAPublicNumbers(
            int.from_bytes(b64url_decode(jwk['e']), 'big'),
            int.from_bytes(b64url_decode(jwk['n']), 'big')).public_key()
        # Raises InvalidSignature if the signature doesn't match
        public_key.verify(b64url_decode(signature_b64),
                          f'{header_b64}.{payload_b64}'.encode(),
                          padding.PKCS1v15(), hashes.SHA256())
        assert header['alg'] == 'RS256'
        return json.loads(b64url_decode(payload_b64))


class TestOIDCProvider(BaseOIDCTestCase):

    def test_discovery(self):
        response = self.client.get('/.well-known/openid-configuration')
        assert response.status_code == 200
        doc = response.get_json()
        assert doc['issuer'] == ISSUER
        assert doc['authorization_endpoint'] == ISSUER + '/oidc/authorize'
        assert doc['token_endpoint'] == ISSUER + '/oidc/token'
        assert doc['userinfo_endpoint'] == ISSUER + '/oidc/userinfo'
        assert doc['end_session_endpoint'] == ISSUER + '/oidc/logout'
        assert doc['jwks_uri'] == ISSUER + '/oidc/jwks'
        assert 'S256' in doc['code_challenge_methods_supported']

    def test_login_redirect_round_trip(self):
        # Not logged in: we are sent to the regular login page
        response = self.authorize()
        assert response.status_code == 302
        assert urlsplit(response.headers['Location']).path == '/oidc/login'
        # After the regular login we end up at the authorization endpoint
        response = self.login(follow_redirects=False)
        assert response.status_code == 302
        location = urlsplit(response.headers['Location'])
        assert location.path == '/oidc/authorize'
        # And from there the code is sent to the client
        response = self.client.get(
            location.path + '?' + location.query)
        assert response.status_code == 302
        assert response.headers['Location'].startswith(REDIRECT_URI + '?')

    def test_regular_login_is_unchanged(self):
        response = self.login(follow_redirects=False)
        assert response.status_code == 302
        assert urlsplit(response.headers['Location']).path == '/'

    def test_next_is_only_honored_for_oidc(self):
        with self.client.session_transaction() as sess:
            sess['oidc_next'] = 'https://evil.example.org/'
        response = self.login(follow_redirects=False)
        assert urlsplit(response.headers['Location']).path == '/'

    def test_prompt_none_when_logged_out(self):
        response = self.authorize(prompt='none')
        query = parse_qs(urlsplit(response.headers['Location']).query)
        assert query['error'] == ['login_required']
        assert query['state'] == ['state-123']

    def test_full_flow(self):
        code = self.get_code()
        response = self.exchange(code)
        assert response.status_code == 200
        assert response.headers['Cache-Control'] == 'no-store'
        tokens = response.get_json()
        assert tokens['token_type'] == 'Bearer'
        claims = self.verify_id_token(tokens['id_token'])
        assert claims['iss'] == ISSUER
        assert claims['aud'] == CLIENT_ID
        assert claims['sub'] == 'test'
        assert claims['nonce'] == 'nonce-456'
        assert claims['email'].endswith('@sigmund.invalid')
        assert claims['exp'] > claims['iat']
        response = self.client.get(
            '/oidc/userinfo',
            headers={'Authorization': 'Bearer ' + tokens['access_token']})
        assert response.status_code == 200
        info = response.get_json()
        assert info['sub'] == 'test'
        assert info['email'] == claims['email']
        assert info['preferred_username'] == 'test'

    def test_scope_limits_claims(self):
        code = self.get_code(scope='openid')
        tokens = self.exchange(code).get_json()
        claims = self.verify_id_token(tokens['id_token'])
        assert 'email' not in claims
        assert 'name' not in claims

    def test_client_secret_post(self):
        code = self.get_code()
        response = self.client.post('/oidc/token', data=dict(
            grant_type='authorization_code', code=code,
            redirect_uri=REDIRECT_URI, client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET))
        assert response.status_code == 200

    def test_code_is_single_use(self):
        code = self.get_code()
        assert self.exchange(code).status_code == 200
        response = self.exchange(code)
        assert response.status_code == 400
        assert response.get_json()['error'] == 'invalid_grant'

    def test_wrong_client_secret(self):
        code = self.get_code()
        response = self.exchange(code, secret='wrong')
        assert response.status_code == 401
        assert response.get_json()['error'] == 'invalid_client'

    def test_redirect_uri_mismatch_at_token_endpoint(self):
        code = self.get_code()
        response = self.exchange(code, redirect_uri=REDIRECT_URI + '/other')
        assert response.status_code == 400
        assert response.get_json()['error'] == 'invalid_grant'

    def test_unknown_redirect_uri_is_not_redirected_to(self):
        self.login()
        response = self.authorize(redirect_uri='https://evil.example.org/cb')
        assert response.status_code == 400
        assert 'Location' not in response.headers

    def test_unknown_client(self):
        self.login()
        response = self.authorize(client_id='someone-else')
        assert response.status_code == 400

    def test_wrong_response_type(self):
        self.login()
        response = self.authorize(response_type='token')
        query = parse_qs(urlsplit(response.headers['Location']).query)
        assert query['error'] == ['unsupported_response_type']

    def test_openid_scope_required(self):
        self.login()
        response = self.authorize(scope='profile')
        query = parse_qs(urlsplit(response.headers['Location']).query)
        assert query['error'] == ['invalid_scope']

    def test_pkce(self):
        verifier = b64url(b'v' * 48)
        challenge = b64url(hashlib.sha256(verifier.encode()).digest())
        code = self.get_code(code_challenge=challenge,
                             code_challenge_method='S256')
        response = self.exchange(code, code_verifier=verifier)
        assert response.status_code == 200

    def test_pkce_wrong_verifier(self):
        verifier = b64url(b'v' * 48)
        challenge = b64url(hashlib.sha256(verifier.encode()).digest())
        code = self.get_code(code_challenge=challenge,
                             code_challenge_method='S256')
        response = self.exchange(code, code_verifier=b64url(b'w' * 48))
        assert response.status_code == 400
        assert response.get_json()['error'] == 'invalid_grant'

    def test_pkce_plain_is_refused(self):
        self.login()
        response = self.authorize(code_challenge=b64url(b'c' * 48),
                                  code_challenge_method='plain')
        query = parse_qs(urlsplit(response.headers['Location']).query)
        assert query['error'] == ['invalid_request']

    def test_userinfo_requires_valid_token(self):
        assert self.client.get('/oidc/userinfo').status_code == 401
        response = self.client.get(
            '/oidc/userinfo', headers={'Authorization': 'Bearer nope'})
        assert response.status_code == 401

    def test_suspended_user_is_refused(self):
        from sigmund.database.models import db, User
        self.login()
        db.session.add(User(username='test', suspended=True))
        db.session.commit()
        response = self.authorize()
        assert response.status_code == 403
        assert 'Location' not in response.headers

    def test_subscription_required(self):
        from datetime import datetime, timedelta
        from sigmund.database.models import db, User, Subscription
        config.subscription_required = True
        self.login()
        assert self.authorize().status_code == 403
        user = User(username='test')
        db.session.add(user)
        db.session.commit()
        assert self.authorize().status_code == 403
        now = datetime.utcnow()
        db.session.add(Subscription(user_id=user.user_id,
                                    from_date=now - timedelta(days=1),
                                    to_date=now + timedelta(days=1)))
        db.session.commit()
        assert self.authorize().status_code == 302


class TestEndSession(BaseOIDCTestCase):

    def login_as(self, username):
        return self.client.post('/login', data=dict(
            username=username, password='password'))

    def userinfo(self, access_token):
        return self.client.get('/oidc/userinfo', headers={
            'Authorization': 'Bearer ' + access_token})

    def test_logout_with_valid_hint(self):
        # A complete login flow, as LibreChat would do it
        code = self.get_code()
        tokens = self.exchange(code).get_json()
        assert self.userinfo(tokens['access_token']).status_code == 200
        # LibreChat navigates the browser to the end-session endpoint
        response = self.client.get('/oidc/logout', query_string=dict(
            id_token_hint=tokens['id_token'],
            post_logout_redirect_uri=POST_LOGOUT_URI))
        assert response.status_code == 302
        assert response.headers['Location'] == POST_LOGOUT_URI
        # The Sigmund session is gone: the main page redirects to the login
        # page instead of showing the chat page
        response = self.client.get('/')
        assert response.status_code == 302
        assert urlsplit(response.headers['Location']).path == '/login'
        # And so are the access tokens: the userinfo endpoint refuses them
        assert self.userinfo(tokens['access_token']).status_code == 401

    def test_logout_with_expired_hint(self):
        # A client's session can outlive the one-hour ID tokens, so an
        # expired hint must still identify the user
        self.login()
        from sigmund.routes.oidc_provider import _signer
        now = int(time.time())
        expired_token = _signer().sign({
            'iss': ISSUER, 'aud': CLIENT_ID, 'sub': 'test',
            'iat': now - 10_000, 'exp': now - 1_000,
            'auth_time': now - 10_000})
        response = self.client.get('/oidc/logout', query_string=dict(
            id_token_hint=expired_token))
        assert response.status_code == 302
        assert self.client.get('/').status_code == 302

    def test_logout_without_hint(self):
        # Without a hint the current user is logged out, as on /logout
        self.login()
        response = self.client.get('/oidc/logout')
        assert response.status_code == 302
        assert urlsplit(response.headers['Location']).path == '/oidc/login'
        assert self.client.get('/').status_code == 302

    def test_logout_with_tampered_hint(self):
        # A token that we did not sign must not control who is logged out,
        # but the current user is logged out nonetheless, as on /logout
        self.login()
        forged = '.'.join(['a' * 40, 'b' * 40, 'c' * 40])
        response = self.client.get('/oidc/logout', query_string=dict(
            id_token_hint=forged))
        assert response.status_code == 302
        assert self.client.get('/').status_code == 302

    def test_unlisted_post_logout_uri_is_refused(self):
        self.login()
        response = self.client.get('/oidc/logout', query_string=dict(
            id_token_hint='irrelevant',
            post_logout_redirect_uri='https://evil.example.org/'))
        assert response.status_code == 302
        assert urlsplit(response.headers['Location']).path == '/oidc/login'

    def test_logout_when_not_logged_in(self):
        response = self.client.get('/oidc/logout', query_string=dict(
            post_logout_redirect_uri=POST_LOGOUT_URI))
        assert response.status_code == 302
        assert response.headers['Location'] == POST_LOGOUT_URI


class TestOIDCMisconfigured(BaseOIDCTestCase):
    """A broken OIDC configuration must disable the provider, but not Sigmund.
    """

    def setUp(self):
        super().setUp()
        config.oidc_client_secret = 'too-short'
        self.app = create_app(config_class=OIDCTestConfig)
        self.client = self.app.test_client(use_cookies=True)

    def test_provider_is_skipped(self):
        response = self.client.get('/.well-known/openid-configuration')
        assert response.status_code == 404
        # Regular Sigmund keeps working
        assert self.client.get('/login').status_code == 200


class TestOIDCDisabled(BaseOIDCTestCase):

    enabled = False

    def test_routes_do_not_exist(self):
        for path in ('/.well-known/openid-configuration', '/oidc/jwks',
                     '/oidc/authorize', '/oidc/userinfo', '/oidc/logout'):
            assert self.client.get(path).status_code == 404
        assert self.client.post('/oidc/token').status_code == 404
        assert self.client.get('/login').status_code == 200


if __name__ == '__main__':
    unittest.main()
