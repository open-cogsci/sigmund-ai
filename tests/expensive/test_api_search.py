import json
from .test_app import BaseRoutesTestCase
from sigmund import config


class TestApiSearch(BaseRoutesTestCase):
    
    def setUp(self):
        super().setUp()
                
    def test_setting(self):
        response = self.client.post('/public/search', json={'query': 'test'})
        self.assertEqual(response.status_code, 200)
