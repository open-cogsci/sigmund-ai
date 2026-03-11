import asyncio
import logging
from .expensive_test_utils import BaseExpensiveTest
logger = logging.getLogger('sigmund')
logging.basicConfig(level=logging.INFO, force=True)


class TestInvoke(BaseExpensiveTest):

    def _test_tool(self):
        messages = [dict(role='user', content='Hi there!')]
        # First test the regular invoke, which should return a response object
        # that can be converted to str
        reply = self.sigmund.answer_model.invoke(messages)
        reply = self.sigmund.answer_model.get_response(reply)
        assert isinstance(reply, str)
        # The stream invoke should return tuples with fragments, complete 
        # status. Incomplete fragments are str, complete fragments need to be
        # converted
        stream = self.sigmund.answer_model.stream_invoke(messages)
        for reply, complete in stream:
            if complete:
                reply = self.sigmund.answer_model.get_response(reply)        
            assert isinstance(reply, str)            
        # The async invoke should be like the regular invoke except that it's
        # async
        reply = asyncio.run(self.sigmund.answer_model.async_invoke(messages))
        reply = self.sigmund.answer_model.get_response(reply)
        assert isinstance(reply, str)
