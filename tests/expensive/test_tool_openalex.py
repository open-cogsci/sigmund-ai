from .expensive_test_utils import BaseExpensiveTest
from sigmund import config


class TestToolsOpenAlex(BaseExpensiveTest):
    
    def setUp(self):
        config.settings_default['tool_search_openalex'] = 'true'
        config.settings_default['tool_download_from_openalex'] = 'true'
        super().setUp()
    
    def _test_tool(self):
        query = 'Can you search OpenAlex for articles about pupillometry in psychology? What is the title of the review article by Mathôt?'
        for reply in self.sigmund.send_user_message(query):
            print(reply.msg)
        assert 'pupillometry' in reply.msg.lower()
        query = 'Can you now download the article?'
        for reply in self.sigmund.send_user_message(query):
            print(reply.msg)

