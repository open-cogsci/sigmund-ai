from .expensive_test_utils import BaseExpensiveTest


class TestGenerateImage(BaseExpensiveTest):
    
    def _test_tool(self):
        query = 'Can you generate a small image of a black cat?'
        for reply in self.sigmund.send_user_message(query):
            print(reply.msg)
