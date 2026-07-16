import logging
import json
from .expensive_test_utils import BaseExpensiveTest
logger = logging.getLogger('sigmund')
logging.basicConfig(level=logging.INFO, force=True)


class TestJsonOutput(BaseExpensiveTest):

    def _test_tool(self):
        messages = [
            dict(role='system', content='You"re Sigmund!"'),
            dict(role='user', content='What is your favorite color? Please respond with a JSON string like {"color": "red"}')
        ]
        self.sigmund.answer_model.json_mode = True
        reply = self.sigmund.answer_model.predict(messages)
        json.loads(reply)