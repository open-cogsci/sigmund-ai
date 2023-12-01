import logging
import jinja2
from . import config, library
from .documentation import Documentation, OpenSesameDocumentationSource, \
    FAISSDocumentationSource
from .messages import Messages
from .model import model
logger = logging.getLogger('heymans')


class Heymans:
    
    def __init__(self, user_id):
        self.user_id = user_id
        self.documentation = Documentation(
            self, sources=[OpenSesameDocumentationSource(self),
                           FAISSDocumentationSource(self)])
        self.messages = Messages(self)
        self.search_model = model(self, config.search_model)
        self.answer_model = model(self, config.answer_model)
    
    def send_user_message(self, message):
        self.messages.append('user', message)
        while True:
            if len(self.documentation) == 0:
                model = self.search_model
            else:
                model = self.answer_model
            reply = model.predict(self.messages.prompt())
            if isinstance(reply, str):
                break
            if reply['action'] == 'search':
                self.documentation.search([message] + reply.get('queries', []))
        self.messages.append('assistant', reply)
        self.documentation.clear()
        return reply

    def welcome_message(self):
        return self.messages.welcome_message()
