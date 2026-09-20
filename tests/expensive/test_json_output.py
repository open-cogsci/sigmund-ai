import logging
import json
import pytest
from .expensive_test_utils import BaseExpensiveTest
logger = logging.getLogger('sigmund')
logging.basicConfig(level=logging.INFO, force=True)


class TestJsonOutput(BaseExpensiveTest):

    def _test_tool(self):
        messages = [
            dict(role='system', content='You"re Sigmund!"'),
            dict(role='user', content='What is your favorite color? Please respond with a JSON string like {"color": "red"}. Don\'t add anything else, just the JSON string.')
        ]
        self.sigmund.answer_model.json_mode = True
        reply = self.sigmund.answer_model.predict(messages)
        json.loads(reply)
        
    def test_extract_json(self):
        
        reply = '''The user asks what my favorite color is, and wants a JSON string response like {"color": "red"}.

I should respond with a JSON string. Let me pick a color. As an AI, I don't have preferences, but I can play along and give a JSON response. I could just respond with the JSON directly.

The user wants me to respond with a JSON string. I could just reply with the JSON string in my message. No tool calls needed here—this is a simple question. Although... I could use the workspace to share the JSON? The update_workspace_content tool is for sharing text or code with the user. But the user just asked a simple question and wants a JSON string response. I think a plain text response with the JSON is fine.

Let me pick a color—maybe blue, or something thoughtful. Since my name is Sigmund (Freud reference?), maybe a deep purple (associated with introspection?) or black/white. I'll just pick something. Let me say blue, classic. Or since I'm Sigmund (Freud), maybe "violet" — Freud wrote about dreams and colors. Doesn't matter much. I'll go with blue.

Response: {"color": "blue"}

I should keep the response simple, just the JSON string as requested. Maybe a brief note, but the user specifically said "Please respond with a JSON string like {"color": "red"}". So I should respond with just the JSON string.
{"color": "blue"}'''
        assert self.sigmund.answer_model.extract_json(reply) == '{"color": "blue"}'
        reply = 'invalid reply'
        pytest.raises(ValueError, self.sigmund.answer_model.extract_json, reply)
