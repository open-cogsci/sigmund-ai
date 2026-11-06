"""Tests for the admin dashboard (routes/admin.py).

Like the other tests in this directory, these need Redis to be running.
The tests cover the user overview, the manual (admin) subscription
extension, the manual addition of extra credits, and access control.
"""
import unittest
from datetime import datetime, timedelta
from sigmund import config
from .test_app import BaseRoutesTestCase


class BaseAdminTestCase(BaseRoutesTestCase):

    def setUp(self):
        self._saved_admin_user_ids = config.admin_user_ids
        self._saved_subscription_required = config.subscription_required
        super().setUp()
        # These imports are deferred here to make sure the database isn't
        # initialized before the app is available.
        global BufferActivity, Subscription, User, DatabaseManager, \
            CREDITS_PER_UNIT
        from sigmund.database.models import BufferActivity, Subscription, User
        from sigmund.database.manager import DatabaseManager
        from sigmund.routes.store import CREDITS_PER_UNIT
        # Create an admin and a regular user. User ids are assigned by the
        # database, so they are looked up instead of assumed.
        DatabaseManager(None, 'admin')
        DatabaseManager(None, 'user')
        self.admin_id = User.query.filter_by(username='admin').one().user_id
        self.user_id = User.query.filter_by(username='user').one().user_id
        config.admin_user_ids = [self.admin_id]        

    def tearDown(self):
        super().tearDown()
        config.admin_user_ids = self._saved_admin_user_ids
        config.subscription_required = self._saved_subscription_required
        

class TestAdminAccessControl(BaseAdminTestCase):

    def test_unauthenticated_requests_are_forbidden(self):
        assert self.client.get('/admin/').status_code == 403
        assert self.client.get(
            f'/admin/user/{self.user_id}').status_code == 403
        assert self.client.post(
            f'/admin/user/{self.user_id}/extend-subscription',
            data={'days': 30}).status_code == 403
        assert self.client.post(
            f'/admin/user/{self.user_id}/add-credits',
            data={'units': 1}).status_code == 403

    def test_non_admin_users_are_forbidden(self):
        self.login('user')
        assert self.client.get('/admin/').status_code == 403
        assert self.client.get(
            f'/admin/user/{self.admin_id}').status_code == 403
        assert self.client.post(
            f'/admin/user/{self.admin_id}/extend-subscription',
            data={'days': 30}).status_code == 403
        assert self.client.post(
            f'/admin/user/{self.admin_id}/add-credits',
            data={'units': 1}).status_code == 403


class TestAdminDashboard(BaseAdminTestCase):

    def setUp(self):
        super().setUp()
        self.login('admin')

    def test_dashboard_lists_all_users(self):
        # The all-users table includes every user, with links to the user
        # overview.
        response = self.client.get('/admin/')
        assert response.status_code == 200
        assert f'/admin/user/{self.user_id}'.encode() in response.data
        assert b'>user</a>' in response.data
        assert f'/admin/user/{self.admin_id}'.encode() in response.data
        assert b'>admin</a>' in response.data

    def test_unknown_user_is_not_found(self):
        assert self.client.get('/admin/user/99999').status_code == 404

    def test_user_overview_shows_user_details(self):
        DatabaseManager(None, 'user').add_activity_buffer(
            CREDITS_PER_UNIT, 'test purchase')
        response = self.client.get(f'/admin/user/{self.user_id}')
        assert response.status_code == 200
        assert b'Account details' in response.data
        assert b'Extra credits buffer' in response.data


class TestAdminExtendSubscription(BaseAdminTestCase):

    def setUp(self):
        super().setUp()
        self.login('admin')

    def test_extend_subscription(self):
        # A manual extension starts from now, like a Stripe renewal, and
        # appends a new subscription record.
        response = self.client.post(
            f'/admin/user/{self.user_id}/extend-subscription',
            data={'days': 30}, follow_redirects=True)
        assert response.status_code == 200
        assert b'Subscription extended by 30 days' in response.data
        records = Subscription.query.filter_by(user_id=self.user_id).all()
        assert len(records) == 1
        record = records[0]
        now = datetime.utcnow()
        assert record.from_date <= now
        assert record.to_date > now
        assert timedelta(days=29) < record.to_date - record.from_date \
            <= timedelta(days=30)
        # The subscription is active and the user is subscribed.
        database = DatabaseManager(None, 'user')
        assert database.check_subscription() is True
        assert database.get_subscription_end_date() == record.to_date

    def test_extend_subscription_reuses_stripe_customer_id(self):
        # The stripe customer id of the latest subscription record is carried
        # over, so that Stripe webhook lookups keep working.
        database = DatabaseManager(None, 'user')
        now = datetime.utcnow()
        database.add_subscription_record(
            'cus_test', 'sub_test',
            from_date=now - timedelta(days=100),
            to_date=now - timedelta(days=50))
        response = self.client.post(
            f'/admin/user/{self.user_id}/extend-subscription',
            data={'days': 30}, follow_redirects=True)
        assert response.status_code == 200
        records = Subscription.query.filter_by(user_id=self.user_id) \
            .order_by(Subscription.from_date).all()
        assert len(records) == 2
        assert records[1].stripe_customer_id == 'cus_test'
        assert DatabaseManager.from_stripe_customer_id('cus_test') \
            .user_id == self.user_id

    def test_extend_subscription_rejects_invalid_days(self):
        response = self.client.post(
            f'/admin/user/{self.user_id}/extend-subscription',
            data={'days': 0})
        assert response.status_code == 400
        assert Subscription.query.filter_by(user_id=self.user_id).count() == 0


class TestAdminAddCredits(BaseAdminTestCase):

    def setUp(self):
        super().setUp()
        self.login('admin')

    def test_add_credits(self):
        # Credits are added in the same units that the store uses.
        response = self.client.post(
            f'/admin/user/{self.user_id}/add-credits',
            data={'units': 2}, follow_redirects=True)
        assert response.status_code == 200
        assert b'Added 20,000,000 extra credits' in response.data
        entries = BufferActivity.query.filter_by(user_id=self.user_id).all()
        assert len(entries) == 1
        assert entries[0].tokens == 2 * CREDITS_PER_UNIT
        assert entries[0].description.startswith('Manually added')
        database = DatabaseManager(None, 'user')
        assert database.get_activity_buffer() == 2 * CREDITS_PER_UNIT

    def test_add_credits_rejects_invalid_units(self):
        response = self.client.post(
            f'/admin/user/{self.user_id}/add-credits',
            data={'units': 0})
        assert response.status_code == 400
        assert BufferActivity.query.filter_by(user_id=self.user_id).count() \
            == 0


if __name__ == '__main__':
    unittest.main()
