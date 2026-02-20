from .expensive_test_utils import BaseExpensiveTest
from sigmund import config


class TestGenerateImageDallE3(BaseExpensiveTest):
    
    def setUp(self):
        config.settings_default['tool_generate_image_dalle3'] = 'true'
        super().setUp()    
    
    def _test_tool(self):
        query = 'Can you generate a small image of a black cat?'
        for reply in self.sigmund.send_user_message(query):
            print(reply.msg)
