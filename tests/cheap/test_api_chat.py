import json
from .test_app import BaseRoutesTestCase
from heymans import config


class TestApiChat(BaseRoutesTestCase):
    
    def setUp(self):
        super().setUp()
        config.settings_default['model_config'] = 'dummy'
        # Check that before login we are not allowed to use the API
        response = self.client.post('/api/chat/start', json={
            'message': 'hello'
        })
        assert response.status_code == 401
        self.login()
        
    def test_chat_without_search(self):
        self.client.post('/api/setting/set', json={'search_first': 'false'})
        response = self.client.post('/api/chat/start', json={
            'message': 'hello'
        })
        assert response.status_code == 200
        response = self.client.get('/api/chat/stream')
        assert response.status_code == 200
        for i, line in enumerate(response.iter_encoded()):
            data = json.loads(line.decode().lstrip('data:'))
            if i == 0:
                assert data['action'] == 'set_loading_indicator'
            elif i == 1:
                assert data['response'] == '<p>Sigmund: dummy reply</p>'
            elif i == 2:
                assert data['action'] == 'close'
                
    def test_chat_with_search(self):
        self.client.post('/api/setting/set', json={'search_first': 'true'})
        response = self.client.post('/api/chat/start', json={
            'message': 'hello'
        })
        assert response.status_code == 200
        response = self.client.get('/api/chat/stream')
        assert response.status_code == 200
        for i, line in enumerate(response.iter_encoded()):
            data = json.loads(line.decode().lstrip('data:'))
            if i == 0:
                assert data['action'] == 'set_loading_indicator'
            elif i == 1:
                assert data['action'] == 'set_loading_indicator'
            elif i == 2:
                assert data['response'] == '<p>Sigmund: dummy reply</p>'
            elif i == 3:
                assert data['action'] == 'close'


if __name__ == '__main__':
    unittest.main()
