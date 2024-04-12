import base64
from heymans.heymans import Heymans
from .expensive_test_utils import BaseExpensiveTest


class TestToolSearchDocumentation(BaseExpensiveTest):
    
    def setUp(self):
        super().setUp()
        self.heymans = Heymans(user_id='pytest', search_first=True)
    
    def _test_tool(self):
        query = 'What is the first header line of the OpenSesame topic documentation?'
        for reply, metadata in self.heymans.send_user_message(query):
            print(reply)
        assert 'important' in reply.lower()
