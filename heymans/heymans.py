import logging
import jinja2
from . import config, library
from .documentation import Documentation, FAISSDocumentationSource
from .messages import Messages
from .model import model
from .tools import TopicsTool, SearchTool, CodeInterpreterTool
logger = logging.getLogger('heymans')


class Heymans:
    
    def __init__(self, user_id, persistent=False, encryption_key=None):
        self.user_id = user_id
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
        self.documentation.clear()
        while True:
            reply, json_data = self.search_model.predict(
                self.messages.prompt())
            logger.info(f'[search state] reply: {reply}')
            logger.info(f'[search state] tool action: {json_data}')
            if isinstance(json_data, dict):
                break
            logger.info('[search state] invalid tool action, retrying')
        self._run_tools(message, json_data)
        self.documentation.strip_irrelevant(message)
        logger.info(
            f'[search state] documentation length: {len(self.documentation._documents)}')
        # Answer. This state continues until a regular (str) reply has been
        # replied or a tool action with a reply field has been replied.
        reply, json_data = self.answer_model.predict(
            self.messages.prompt())
        logger.info(f'[answer state] reply: {reply}')
        metadata = self.messages.append('assistant', reply)
        if isinstance(json_data, dict):
            logger.info(f'[answer state] tool action: {json_data}')
            self._run_tools(message, json_data)
        reply = '\n\n'.join([reply] + self.reply_extras)
        return reply, metadata
    
    def send_feedback_message(self, message):
        self.messages.append('assistant', message)
        logger.info(
            f'[feedback state] documentation length: {len(self.documentation._documents)}')
        reply, json_data = self.answer_model.predict(
            self.messages.prompt())
        logger.info(f'[feedback state] reply: {reply}')
        metadata = self.messages.append('assistant', reply)
        if isinstance(json_data, dict):
            logger.info(f'[feedback state] tool action: {json_data}')
            self._run_tools(message, json_data)
        self.reply_extras.append(reply)

    def _run_tools(self, message, reply):
        if not isinstance(reply, dict):
            logger.warning(f'expecting dict, not {reply}')
            return
        logger.info(f'running tools')
        for key, value in reply.items():
            if key in self._tools:
                self._tools[key].use(message, value)
