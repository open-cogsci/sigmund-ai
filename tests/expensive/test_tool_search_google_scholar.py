from .expensive_test_utils import BaseExpensiveTest
from sigmund import config


class TestToolsGoogleScholar(BaseExpensiveTest):
    
    def setUp(self):
        config.settings_default['tool_search_google_scholar'] = 'true'
        super().setUp()        
    
    def _test_tool(self):
        query = 'Can you search Google Scholar for articles about pupillometry in psychology? What is the title of the review article by Mathôt?'
        for reply in self.sigmund.send_user_message(query):
            print(reply.msg)
        assert 'pupillometry' in reply.msg.lower()
