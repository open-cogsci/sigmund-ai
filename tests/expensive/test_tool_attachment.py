import base64
from .expensive_test_utils import BaseExpensiveTest


class TestToolsAttachments(BaseExpensiveTest):
    
    def _test_tool(self):
        attachment_data = {
            'filename': 'artist_name.txt',
            'content': 'Rick Ross',
            # 'content': base64.b64encode(b'Rick Ross').decode('utf-8'),
            'description': 'Contains the name of an artist'
        }
        self.sigmund.database.add_attachment(attachment_data)
        assert len(self.sigmund.database.list_attachments()) == 1
        query = 'Which artist name does the attachment contain?'
        for reply in self.sigmund.send_user_message(query):
            if 'Rick Ross' in reply:
                break
        else:
            assert False
        query = 'Can you download the following readme: https://raw.githubusercontent.com/open-cogsci/OpenSesame/milgram/readme.md'
        for reply in self.sigmund.send_user_message(query):
            print(reply.msg)
        query = 'Can you read and summarize the readme for me?'
        for reply in self.sigmund.send_user_message(query):
            print(reply.msg)
