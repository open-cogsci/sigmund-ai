import unittest
from heymans.server import create_app, HeymansConfig
from heymans import config


class UnitTestConfig(HeymansConfig):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    

class BaseRoutesTestCase(unittest.TestCase):

    def setUp(self):
        config.subscription_required = False
        self.app = create_app(config_class=UnitTestConfig)
        self.client = self.app.test_client(use_cookies=True)
        self.app_context = self.app.app_context()
        self.app_context.push()
        
    def login(self):
        response = self.client.post('/login', data=dict(
            username='test',
            password='test'
        ), follow_redirects=True)
        assert response.status_code == 200
        
    def tearDown(self):
        self.app_context.pop()


class TestApp(BaseRoutesTestCase):
        
    def when_unauthenticated(self):
        response = self.client.get('/chat')
        assert response.status_code == 302
        response = self.client.get('/about')
        assert response.status_code == 200
        response = self.client.get('/login')
        assert response.status_code == 200
        response = self.client.get('/login_failed')
        assert response.status_code == 200
        response = self.client.get('/logout', follow_redirects=True)
        assert response.status_code == 200
        
    def when_authenticated(self):
        response = self.client.get('/')
        assert response.status_code == 200
        response = self.client.get('/chat')
        assert response.status_code == 200
        response = self.client.get('/logout', follow_redirects=True)
        assert response.status_code == 200
        
    def test_app(self):
        self.when_unauthenticated()
        self.login()
        self.when_authenticated()
        response = self.client.get('/logout', follow_redirects=True)
        assert response.status_code == 200
        self.when_unauthenticated()


if __name__ == '__main__':
    unittest.main()
