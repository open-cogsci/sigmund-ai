import unittest
from sigmund.sigmund import Sigmund
from sigmund import config
import logging
logger = logging.getLogger('sigmund')
logging.basicConfig(level=logging.INFO, force=True)


class BaseExpensiveTest(unittest.TestCase):
    
    def setUp(self):
        from sigmund.database.models import drop_db, init_db
        drop_db()
        init_db()
        self.sigmund = Sigmund(user_id='pytest', search_first=False)
        config.max_tokens_per_hour = float('inf')
        config.log_replies = True
        
    def _test_tool(self):
        pass

    def test_openai(self):
        config.settings_default['model_config'] = 'openai'
        self._test_tool()
        
    def test_openai_o1(self):
        config.settings_default['model_config'] = 'openai_o1'
        self._test_tool()
    
    def test_anthropic(self):
        config.settings_default['model_config'] = 'anthropic'
        self._test_tool()
    
    def test_mistral(self):
        config.settings_default['model_config'] = 'mistral'
        self._test_tool()
