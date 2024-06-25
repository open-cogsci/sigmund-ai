import json
from .test_app import BaseRoutesTestCase
from sigmund import config


class TestApiSearch(BaseRoutesTestCase):
    
    def setUp(self):
        super().setUp()
                
    def test_setting(self):
        response = self.client.get('/api/search/canvas%20python')
