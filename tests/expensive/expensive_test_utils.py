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
        config.max_tokens_per_hour = float('inf')
        config.log_replies = True
        config.search_enabled = False
        self.sigmund = Sigmund(user_id='pytest')
        
    def _test_tool(self):
        pass

    def test_openai(self):
        config.settings_default['model_config'] = 'openai'
        self._test_tool()
        
    def test_openai_o1(self):
        config.settings_default['model_config'] = 'openai_o1'
        self._test_tool()
    
    def test_anthropic_regular(self):
        config.settings_default['model_config'] = 'anthropic'
        self._test_tool()
        
    def test_anthropic_thinking(self):
        config.settings_default['model_config'] = 'anthropic_thinking'
        self._test_tool()
    
    def test_mistral(self):
        config.settings_default['model_config'] = 'mistral'
        self._test_tool()
