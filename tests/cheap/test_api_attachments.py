import json
import os
from .test_app import BaseRoutesTestCase
from heymans import config


class TestApiAttachments(BaseRoutesTestCase):
    
    def setUp(self):
        super().setUp()
        config.settings_default['model_config'] = 'dummy'
        self.login()
        
    def add_attachment(self):
        # Verify that initially there are no attachments
        response = self.client.get('/api/attachments/list')
        self.assertEqual(response.status_code, 200)
        initial_attachments = response.json
        self.assertEqual(len(initial_attachments), 0)
        # Simulate file upload
        self.attachment_path = os.path.join(os.path.dirname(__file__),
                                            'testdata',
                                            'attachment.txt')
        with open(self.attachment_path, 'rb') as attachment_file:
            data = {
                'file': (attachment_file, 'attachment.txt'),
                'description': 'Test File'
            }
            response = self.client.post('/api/attachments/add',
                                        data=data,
                                        content_type='multipart/form-data')
            self.assertEqual(response.status_code, 200)
            # Additional assertions based on your application's response
        # Check that the number of attachments has increased to 1
        response = self.client.get('/api/attachments/list')
        self.assertEqual(response.status_code, 200)
        new_attachments = response.json
        self.assertEqual(len(new_attachments), 1)

    def test_get_attachment(self):
        self.add_attachment()
        # Get the ID of the first attachment
        list_response = self.client.get('/api/attachments/list')
        attachments = json.loads(list_response.data)
        attachment_id = next(iter(attachments))
        # Get the attachment detail
        get_response = self.client.get(f'/api/attachments/get/{attachment_id}')
        self.assertEqual(get_response.status_code, 200)
        # Process the stream and verify the content
        streamed_content = get_response.data.decode('utf-8')
        self.assertEqual(streamed_content.strip(), 'test attachment')

    def test_delete_attachment(self):
        self.add_attachment()
        # Get the ID of the first attachment
        list_response = self.client.get('/api/attachments/list')
        attachments = list_response.json
        attachment_id = next(iter(attachments))
        # Delete the attachment
        delete_response = self.client.delete(
            f'/api/attachments/delete/{attachment_id}')
        self.assertEqual(delete_response.status_code, 200)
        # Verify that the attachment has been deleted
        list_response = self.client.get('/api/attachments/list')
        attachments_after_delete = list_response.json
        self.assertNotIn(attachment_id, attachments_after_delete)
