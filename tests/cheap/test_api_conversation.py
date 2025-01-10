import json
from .test_app import BaseRoutesTestCase
from sigmund import config


class TestApiConversation(BaseRoutesTestCase):
    
    def setUp(self):
        super().setUp()
        config.settings_default['model_config'] = 'dummy'
        self.login()
                
    def test_new_conversation(self):
        # Add some content to the conversation to make it count
        self.client.post('/api/setting/set', json={'mode': 'academic'})
        response = self.client.post('/api/chat/start', json={
            'message': 'dummy'
        })
        for response in self.client.get('/api/chat/stream').iter_encoded():
            pass
        response = self.client.get('/api/conversation/list')
        original_count = len(response.json)
        response = self.client.get('/api/conversation/new',
                                   follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        response = self.client.get('/api/conversation/list')
        new_count = len(response.json)
        self.assertEqual(new_count, original_count + 1)

    def test_clear_conversation(self):
        response = self.client.get('/api/conversation/clear',
                                   follow_redirects=True)
        self.assertEqual(response.status_code, 200)

    def test_delete_conversation(self):
        # Add some content to the conversation to make it count
        self.client.post('/api/setting/set', json={'mode': 'opensesame'})
        response = self.client.post('/api/chat/start', json={
            'message': 'dummy'
        })
        for response in self.client.get('/api/chat/stream').iter_encoded():
            pass        
        self.client.get('/api/conversation/new', follow_redirects=True)
        list_resp = self.client.get('/api/conversation/list')
        conversation_id = list(list_resp.json)[0]
        original_count = len(list_resp.json)
        # Delete the conversation
        delete_resp = self.client.delete(
            f'/api/conversation/delete/{conversation_id}')
        self.assertEqual(delete_resp.status_code, 204)
        # Check that the number of conversations has decreased by one
        list_resp = self.client.get('/api/conversation/list')
        new_count = len(list_resp.json)
        self.assertEqual(new_count, original_count - 1)

    def test_activate_conversation(self):
        list_resp = self.client.get('/api/conversation/list')
        conversation_id = list(list_resp.json)[0]
        activate_resp = self.client.get(
            f'/api/conversation/activate/{conversation_id}',
            follow_redirects=True)
        self.assertEqual(activate_resp.status_code, 200)


if __name__ == '__main__':
    unittest.main()
