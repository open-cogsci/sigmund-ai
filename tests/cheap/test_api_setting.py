import json
from .test_app import BaseRoutesTestCase
from heymans import config


class TestApiSetting(BaseRoutesTestCase):
    
    def setUp(self):
        super().setUp()
        config.settings_default['model_config'] = 'dummy'
        self.login()
                
    def test_setting(self):
        response = self.client.get('/api/setting/get/test_setting')
        assert not response.json['success']
        response = self.client.post('/api/setting/set', json={
            'test_setting': 'test_value'
        })
        assert response.json['success']
        response = self.client.get('/api/setting/get/test_setting')
        assert response.json['success']
        assert response.json['value'] == 'test_value'
        response = self.client.post('/api/setting/set', json={
            'test_setting': 'test_value2',
            'test_setting_b': 'test_value_b'
        })
        assert response.json['success']
        response = self.client.get('/api/setting/get/test_setting')
        assert response.json['success']
        assert response.json['value'] == 'test_value2'
        response = self.client.get('/api/setting/get/test_setting_b')
        assert response.json['success']
        assert response.json['value'] == 'test_value_b'
