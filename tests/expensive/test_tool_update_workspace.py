from .expensive_test_utils import BaseExpensiveTest
from sigmund import config


class TestUpdateWorkspace(BaseExpensiveTest):
    
    def setUp(self):
        config.settings_default['tool_update_workspace_content'] = 'true'
        super().setUp(disable_all_tools=False)
    
    def _test_tool(self):
        query = 'Can you add a hello-world Python script to the workspace?'
        for reply in self.sigmund.send_user_message(query):
            print(reply.msg)
        assert 'hello' in self.sigmund.messages.workspace_content.lower()
