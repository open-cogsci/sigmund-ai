from .expensive_test_utils import BaseExpensiveTest
from sigmund import config


class TestGenerateImage(BaseExpensiveTest):
    
    def setUp(self):
        config.settings_default['tool_generate_image'] = 'true'
        super().setUp()    
    
    def _test_tool(self):
        query = 'Can you generate a small image of a black cat?'
        for reply in self.sigmund.send_user_message(query):
            print(reply.msg)
