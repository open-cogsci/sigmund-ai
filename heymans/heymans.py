import logging
import jinja2
from . import config, library
from .documentation import Documentation, FAISSDocumentationSource
from .messages import Messages
from .model import model
from .tools import TopicsTool, SearchTool, CodeInterpreterTool
logger = logging.getLogger('heymans')


class Heymans:
    
    def __init__(self, user_id, persistent=False, encryption_key=None,
                 search_first=True):
        self.user_id = user_id
        self._search_first = search_first
        self.encryption_key = encryption_key
        if isinstance(self.encryption_key, str):
            self.encryption_key = self.encryption_key.encode()
        logger.info(f'user {user_id} with encryption_key {encryption_key}')
        self.documentation = Documentation(
            self, sources=[FAISSDocumentationSource(self)])
        self.search_model = model(self, config.search_model)
        self.answer_model = model(self, config.answer_model)
        self.condense_model = model(self, config.condense_model)
        self.messages = Messages(self, persistent)
        self._tools = {'topics': TopicsTool(self),
                       'search': SearchTool(self),
                       'execute_code': CodeInterpreterTool(self)}
    
    def send_user_message(self, message):
        self.reply_extras = []
        self.messages.append('user', message)
        # Documentation search. This state continues until a tool action has
        # been replied.
        if self._search_first:
            self.documentation.clear()
            while len(self.documentation) == 0:
                reply = self.search_model.predict(self.messages.prompt())
                logger.info(f'[search state] reply: {reply}')
                reply = self._run_tools(reply)
        self.documentation.strip_irrelevant(message)
        logger.info(
            f'[search state] documentation length: {len(self.documentation._documents)}')
        # Answer. This state continues until a regular (str) reply has been
        # replied or a tool action with a reply field has been replied.
        reply = self.answer_model.predict(self.messages.prompt())
        logger.info(f'[answer state] reply: {reply}')
        metadata = self.messages.append('assistant', reply)
        reply = self._run_tools(reply)
        reply = '\n\n'.join([reply] + self.reply_extras)
        return reply, metadata
    
    def send_feedback_message(self, message):
        self.messages.append('assistant', message)
        logger.info(
            f'[feedback state] documentation length: {len(self.documentation._documents)}')
        reply = self.answer_model.predict(self.messages.prompt())
        logger.info(f'[feedback state] reply: {reply}')
        self.messages.append('assistant', reply)
        self._run_tools(reply)
        self.reply_extras.append(reply)

    def _run_tools(self, reply):
        logger.info(f'running tools')
        for tool in self._tools.values():
            reply = tool.run(reply)
        return reply
