from .expensive_test_utils import BaseExpensiveTest
from sigmund import config


class TestMultipleTools(BaseExpensiveTest):

    def setUp(self):
        config.settings_default['tool_add_note'] = 'true'
        super().setUp(disable_all_tools=False)

    def _test_tool(self):
        # Step 1: Ask the model to create a note
        query = ('I would like to test your tool use abilities. Can you create '
                 'two separate notes in a single message please?')
        for reply in self.sigmund.send_user_message(query):
            print(reply.msg)
        notes = self.sigmund.messages.get_notes()
        assert len(notes) == 2
