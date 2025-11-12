from ..cheap.test_app import BaseRoutesTestCase


class TestApiSearch(BaseRoutesTestCase):
    
    def setUp(self):
        super().setUp()
                
    def test_setting(self):
        response = self.client.post('/public/search', json={'query': 'test'})
        self.assertEqual(response.status_code, 200)
