from .expensive_test_utils import BaseExpensiveTest


class TestToolsGoogleScholar(BaseExpensiveTest):
    
    def test_tools_google_scholar(self):
        query = 'Can you search Google Scholar for articles about pupillometry in psychology? What is the title of the review article by Mathôt?'
        for reply, metadata in self.heymans.send_user_message(query):
            if 'Pupillometry: Psychology, physiology, and function' in reply:
                break
        else:
            assert False
