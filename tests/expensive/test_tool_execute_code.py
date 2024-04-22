import base64
from .expensive_test_utils import BaseExpensiveTest


class TestExecuteCode(BaseExpensiveTest):
    
    def _test_tool(self):
        query = 'Can you calculate the square root of 7 using Python code?'
        for reply, metadata in self.sigmund.send_user_message(query):
            print(reply)