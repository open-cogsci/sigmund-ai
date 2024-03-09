import unittest
from heymans.heymans import Heymans
from heymans import config
import logging
logger = logging.getLogger('heymans')
logging.basicConfig(level=logging.INFO, force=True)


class BaseExpensiveTest(unittest.TestCase):
    
    def setUp(self):
        from heymans.database.models import drop_db, init_db
        drop_db()
        init_db()
        self.heymans = Heymans(user_id='pytest', search_first=False)
        config.max_tokens_per_hour = float('inf')
        
    def _test_tool(self):
        pass

    def test_openai(self):
        config.settings_default['model_config'] = 'openai'
        self._test_tool()
    
    def test_anthropic(self):
        config.settings_default['model_config'] = 'anthropic'
        self._test_tool()
    
    def test_mistral(self):
        config.settings_default['model_config'] = 'mistral'
        self._test_tool()
