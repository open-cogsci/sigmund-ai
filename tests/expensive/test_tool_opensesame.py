from .expensive_test_utils import BaseExpensiveTest
from sigmund import config
from sigmund.tools import opensesame_get_syntax_documentation

class TestToolsOpenSesame(BaseExpensiveTest):
    
    def setUp(self):
        config.settings_default['opensesame_get_syntax_documentation'] = 'true'
        super().setUp()
    
    def _test_tool(self):
        self._test_get_syntax_documentation()
        
    def _test_get_syntax_documentation(self):
        tool = opensesame_get_syntax_documentation(self.sigmund)
        tool_message, tool_result, needs_feedback = tool()
