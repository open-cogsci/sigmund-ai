import unittest
from heymans.heymans import Heymans
from heymans import config
import logging
logger = logging.getLogger('heymans')
logging.basicConfig(level=logging.INFO, force=True)


class BaseExpensiveTest(unittest.TestCase):
    
    def setUp(self):
        from heymans.database.models import init_db
        init_db()
        self.heymans = Heymans(user_id='pytest', search_first=False)
        config.max_tokens_per_hour = float('inf')
        
    def _test_tool(self):
        pass

    def test_gpt4(self):
        config.search_model = 'gpt-3.5'
        config.condense_model = 'gpt-3.5'
        config.answer_model = 'gpt-4'
        self._test_tool()
    
    def test_claude3opus(self):
        config.search_model = 'claude-3-sonnet'
        config.condense_model = 'claude-3-sonnet'
        config.answer_model = 'claude-3-opus'
        self._test_tool()
    
    def test_mistral(self):
        config.search_model = 'mistral-small'
        config.condense_model = 'mistral-small'
        config.answer_model = 'mistral-medium'
        self._test_tool()
