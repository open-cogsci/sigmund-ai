"""Tests for the LibreChat subscription client (sigmund/librechat.py) and
the database methods it relies on.

Like the other tests in this directory, these need Redis to be running.
The HTTP calls to LibreChat are mocked, so no LibreChat server is required.
"""
import unittest
from datetime import datetime, timedelta
from unittest import mock

from sigmund import config
from sigmund import librechat
from sigmund.database.manager import DatabaseManager
from sigmund.server import create_app, SigmundConfig

LIBRECHAT_SETTINGS = ('librechat_enabled', 'librechat_url',
                      'librechat_secret')


class LibreChatTestConfig(SigmundConfig):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    SECRET_KEY = 'a-secret-key-for-unit-tests-only'


class BaseLibreChatTestCase(unittest.TestCase):

    def setUp(self):
        self._saved = {name: getattr(config, name)
                       for name in LIBRECHAT_SETTINGS}
        config.librechat_enabled = True
        config.librechat_url = 'http://librechat.example.org'
        config.librechat_secret = 'unit-test-secret'
        self.app = create_app(config_class=LibreChatTestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        self.app_context.pop()
        for name, value in self._saved.items():
            setattr(config, name, value)

    def response(self, status_code=200, json_data=None):
        response = mock.Mock()
        response.status_code = status_code
        response.json.return_value = json_data if json_data is not None else {}
        return response


class TestLibreChatClient(BaseLibreChatTestCase):
    """Tests for the HTTP client, with requests.post mocked out."""

    def test_disabled_client_is_a_noop(self):
        config.librechat_enabled = False
        with mock.patch('sigmund.librechat.requests.post') as post:
            assert librechat.sync_subscription('a@example.org', None) is False
            assert librechat.add_balance('a@example.org', 100) is False
            post.assert_not_called()

    def test_missing_secret_is_a_noop(self):
        config.librechat_secret = None
        with mock.patch('sigmund.librechat.requests.post') as post:
            assert librechat.sync_subscription('a@example.org', None) is False
            post.assert_not_called()

    def test_sync_subscription(self):
        with mock.patch('sigmund.librechat.requests.post') as post:
            post.return_value = self.response(json_data={'active': True})
            expires_at = datetime(2026, 3, 1)
            # The email is normalized, and the naive UTC datetime is
            # formatted as ISO 8601 with a Z suffix.
            assert librechat.sync_subscription(
                '  A@Example.ORG ', expires_at, status='active') is True
            post.assert_called_once_with(
                'http://librechat.example.org/api/subscription/sync',
                json={'email': 'a@example.org',
                      'expiresAt': '2026-03-01T00:00:00Z',
                      'status': 'active'},
                headers={'Authorization': 'Bearer unit-test-secret'},
                timeout=librechat.REQUEST_TIMEOUT)

    def test_sync_subscription_deactivation(self):
        with mock.patch('sigmund.librechat.requests.post') as post:
            post.return_value = self.response(json_data={'active': False})
            assert librechat.sync_subscription('a@example.org', None) is True
            assert post.call_args.kwargs['json']['expiresAt'] is None

    def test_unknown_user_is_not_an_error(self):
        # A user that has not logged into LibreChat yet is skipped, not an
        # error: the state is synced when the user does log in.
        with mock.patch('sigmund.librechat.requests.post') as post:
            post.return_value = self.response(
                status_code=404, json_data={'code': 'user_not_found'})
            assert librechat.sync_subscription('a@example.org', None) is False
            assert librechat.add_balance('a@example.org', 100) is False

    def test_error_responses_are_false(self):
        with mock.patch('sigmund.librechat.requests.post') as post:
            post.return_value = self.response(
                status_code=500, json_data={'code': 'add_balance_failed'})
            assert librechat.add_balance('a@example.org', 100) is False

    def test_connection_errors_are_false(self):
        import requests
        with mock.patch('sigmund.librechat.requests.post') as post:
            post.side_effect = requests.ConnectionError('refused')
            assert librechat.add_balance('a@example.org', 100) is False

    def test_add_balance(self):
        with mock.patch('sigmund.librechat.requests.post') as post:
            post.return_value = self.response(
                json_data={'userId': 'u', 'added': 100, 'tokenCredits': 150})
            # The context is truncated to the 64 characters LibreChat accepts.
            assert librechat.add_balance(
                'a@example.org', 100, context='x' * 100) is True
            post.assert_called_once_with(
                'http://librechat.example.org/api/subscription/add-balance',
                json={'email': 'a@example.org', 'amount': 100,
                      'context': 'x' * 64},
                headers={'Authorization': 'Bearer unit-test-secret'},
                timeout=librechat.REQUEST_TIMEOUT)


class TestDatabaseManager(BaseLibreChatTestCase):
    """Tests for the two DatabaseManager methods that the webhook uses to
    build the sync payloads.
    """

    def test_get_email_returns_the_registered_address(self):
        database = DatabaseManager(None, 'testuser', email='test@example.org')
        assert database.get_email() == 'test@example.org'

    def test_get_subscription_end_date(self):
        database = DatabaseManager(None, 'subuser')
        assert database.get_subscription_end_date() is None
        to_date = datetime.utcnow() + timedelta(days=50)
        database.add_subscription_record(
            'cus_123', 'sub_123', to_date=to_date)
        assert database.get_subscription_end_date() == to_date
