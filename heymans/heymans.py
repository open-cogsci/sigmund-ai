import logging
import jinja2
from . import config, library
from .documentation import Documentation, FAISSDocumentationSource
from .messages import Messages
from .model import model
from . import prompt
from .tools import TopicsTool, SearchTool, CodeInterpreterTool
logger = logging.getLogger('heymans')


class Heymans:
    
    def __init__(self, user_id, persistent=False, encryption_key=None,
                 search_first=True):
        self.user_id = user_id
        self.system_prompt = prompt.SYSTEM_PROMPT_ANSWER
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
        """The main function that takes a user message and returns a reply.
        The reply also has metadata which is a dict that contains information
        about time, sources, etc.
        """
        self.messages.append('user', message)
        if self._search_first:
            self._search(message)
        return self._answer()
    
    def _search(self, message):
        self.system_prompt = prompt.SYSTEM_PROMPT_SEARCH
        self.documentation.clear()
        if self._search_first:
            reply = self.search_model.predict(self.messages.prompt())
            logger.info(f'[search state] reply: {reply}')
            self._run_tools(reply)
        self.documentation.strip_irrelevant(message)
        logger.info(
            f'[search state] {len(self.documentation._documents)} documents, {len(self.documentation)} characters')
    
    def _answer(self, state='answer'):
        self.system_prompt = prompt.SYSTEM_PROMPT_ANSWER
        reply = self.answer_model.predict(self.messages.prompt())
        logger.info(f'{state} state] reply: {reply}')
        metadata = self.messages.append('assistant', reply)
        reply, result, needs_feedback = self._run_tools(reply)
        if result:
            reply += '\n\n' + result
        if needs_feedback:
            self.messages.append('assistant', result)
            reply += '\n\n' + self._answer(state='feedback')[0]
        return reply, metadata

    def _run_tools(self, reply: str) -> tuple[str, str, bool]:
        """Runs all tools on a reply. Returns the modified reply, a string
        that concatenates all output (an empty string if no output was 
        produced) and a bool indicating whether the AI should in turn repond
        to the produced output.
        """
        logger.info(f'running tools')
        results = []
        needs_reply = []
        for tool in self._tools.values():
            reply, tool_results, tool_needs_reply = tool.run(reply)
            results += tool_results
            needs_reply.append(tool_needs_reply)
        return reply, '\n\n'.join(results), any(needs_reply)
