from .expensive_test_utils import BaseExpensiveTest
from sigmund import config


class TestCondenseMessageHistory(BaseExpensiveTest):
    
    def _test_tool(self):
        
        default_max_prompt_length = config.max_prompt_length
        config.max_prompt_length = 300
        for city, country in [
            ('paris', 'france'),
            ('berlin', 'germany'),
            ('amsterdam', 'netherlands'),
            ('madrid', 'spain')
        ]:
            query = f'What is the capital of {country}. Reply only with the name. Don\'t add any other content.'
            for reply in self.sigmund.send_user_message(query):
                pass
            assert reply.msg.lower() == city
        config.max_prompt_length = default_max_prompt_length
