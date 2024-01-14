import unittest
import base64
import os
from .expensive_test_utils import BaseExpensiveTest


# @unittest.skipIf(not os.getenv('EXPENSIVE_TESTS'), 'Skipped')
class TestToolsAttachments(BaseExpensiveTest):
    
    def test_tools_attachments(self):
        attachment_data = {
            'filename': 'artist_name.txt',
            'content': base64.b64encode(b'Rick Ross').decode('utf-8'),
            'description': 'Contains the name of an artist'
        }
        self.heymans.database.add_attachment(attachment_data)
        assert len(self.heymans.database.list_attachments()) == 1
        query = 'Which artist name does the attachment contain?'
        for reply, metadata in self.heymans.send_user_message(query):
            if 'Rick Ross' in reply:
                break
        else:
            assert False
