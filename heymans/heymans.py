import logging
import jinja2
from . import config, library
from .documentation import Documentation, FAISSDocumentationSource
from .messages import Messages
from .model import model
from .tools import TopicsTool, SearchTool
logger = logging.getLogger('heymans')


class Heymans:
    
    def __init__(self, user_id, persistent=False):
        self.user_id = user_id
        self.documentation = Documentation(
            self, sources=[FAISSDocumentationSource(self)])
        self.messages = Messages(self, persistent)
        self.search_model = model(self, config.search_model)
        self.answer_model = model(self, config.answer_model)
        self.condense_model = model(self, config.condense_model)
        self._tools = {'topics': TopicsTool(self),
                       'search': SearchTool(self)}
    
    def send_user_message(self, message):
        self.messages.append('user', message)
        while True:
            if len(self.documentation) == 0:
                model = self.search_model
            else:
                model = self.answer_model
            reply = model.predict(self.messages.prompt())
            if isinstance(reply, str):
                logger.info(f'reply: {reply}')
                break
            logger.info(f'tool action: {reply}')
            self._run_tools(message, reply)
            self.documentation.strip_irrelevant(message)
        self.messages.append('assistant', reply)
        sources = self.documentation.to_json()
        self.documentation.clear()
        return reply, sources

    def _run_tools(self, message, reply):
        if not isinstance(reply, dict):
            logger.warning(f'expecting dict, not {reply}')
            return
        logger.info(f'running tools')
        for key, value in reply.items():
            if key in self._tools:
                self._tools[key].use(message, value)
