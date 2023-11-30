import logging
import jinja2
from . import config, library
from .documentation import Documentation, OpenSesameDocumentationSource, \
    FAISSDocumentationSource
from .messages import Messages
from .model import Model
logger = logging.getLogger('heymans')


class Heymans:
    
    def __init__(self, user_id):
        self.user_id = user_id
        self.documentation = Documentation(
            self, sources=[OpenSesameDocumentationSource(self),
                           FAISSDocumentationSource(self)])
        self.messages = Messages(self)
        self.model = Model(self)
    
    def send_user_message(self, message):
        self.messages.append('user', message)
        while True:
            reply = self.model.predict(self.messages.prompt())
            if isinstance(reply, str):
                break
            if reply['action'] == 'search':
                self.documentation.search(reply.get('queries', []))
        self.messages.append('assistant', reply)
        self.documentation.clear()
        return reply
