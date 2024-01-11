import logging
import jinja2
from typing import Tuple
from . import config, library
from .documentation import Documentation, FAISSDocumentationSource
from .messages import Messages
from .model import model
from .database.manager import DatabaseManager
from . import prompt
from .tools import TopicsTool, SearchTool, CodeExcutionTool, \
    GoogleScholarTool, AttachmentsTool
logger = logging.getLogger('heymans')


class Heymans:
    
    def __init__(self, user_id, persistent=False, encryption_key=None,
                 search_first=True):
        self.user_id = user_id
        self.system_prompt = prompt.SYSTEM_PROMPT_ANSWER
        self._search_first = search_first
        self.database = DatabaseManager(user_id, encryption_key)
        self.documentation = Documentation(
            self, sources=[FAISSDocumentationSource(self)])
        self.search_model = model(self, config.search_model)
        self.answer_model = model(self, config.answer_model)
        self.condense_model = model(self, config.condense_model)
        self.messages = Messages(self, persistent)
        self.search_tools = {'topics': TopicsTool(self),
                             'search': SearchTool(self)}
        self.answer_tools = {'execute_code': CodeExcutionTool(self),
                             'search_google_scholar': GoogleScholarTool(self),
                             'attachments_tool': AttachmentsTool(self)}
        self.tools = self.answer_tools
    
    def send_user_message(self, message):
        """The main function that takes a user message and returns a reply.
        The reply also has metadata which is a dict that contains information
        about time, sources, etc.
        """
        self.messages.append('user', message)
        if self._search_first:
            yield {'action': 'set_loading_indicator',
                   'message': f'{config.ai_name} is searching '}, {}
            yield self._search(message)
        for reply, metadata in self._answer():
            yield reply, metadata
    
    def _search(self, message):
        logger.info('[search state] entering')
        self.documentation.clear()
        self.system_prompt = prompt.SYSTEM_PROMPT_SEARCH
        self.tools = self.search_tools
        reply = self.search_model.predict(self.messages.prompt())
        logger.info(f'[search state] reply: {reply}')
        self._run_tools(reply)
        self.documentation.strip_irrelevant(message)
        logger.info(
            f'[search state] {len(self.documentation._documents)} documents, {len(self.documentation)} characters')
        return {'action': 'set_loading_indicator',
                'message': f'{config.ai_name} is thinking and typing '}, {}
    
    def _answer(self, state='answer'):
        logger.info(f'[{state} state] entering')
        self.system_prompt = prompt.SYSTEM_PROMPT_ANSWER
        self.tools = self.answer_tools
        # We first collect a regular reply to the user message
        reply = self.answer_model.predict(self.messages.prompt())
        logger.info(f'{state} state] reply: {reply}')
        # We then run tools based on the AI reply. This may modify the reply,
        # mainly by stripping out any JSON commands in the reply
        reply, result, needs_feedback = self._run_tools(reply)
        # If the reply contains a NOT_DONE_YET marker, this is a way for the AI
        # to indicate that it wants to perform additional actions. This makes 
        # it easier to perform tasks consisting of multiple responses and 
        # actions. The marker is stripped from the reply so that it's hidden
        # from the user. We also check for a number of common linguistic 
        # indicators that the AI isn't done yet, such "I will now". This is
        # necessary because the explicit marker isn't reliably sent.
        if prompt.NOT_DONE_YET_MARKER in reply or any(
                indicator in reply.lower()
                for indicator in prompt.NOT_DONE_YET_INDICATORS):
            reply = reply.replace(prompt.NOT_DONE_YET_MARKER, '')
            needs_feedback = True
        # If there is still a non-empty reply after running the tools (i.e.
        # stripping the JSON hasn't cleared the reply entirely, then yield and
        # remember it.
        if reply:
            metadata = self.messages.append('assistant', reply)
            yield reply, metadata
        else:
            metadata = self.messages.metadata()
        # If the tools have a result, yield and remember it
        if result:
            self.messages.append('assistant', result)
            yield result, metadata
        # If feedback is required, either because the tools require it or 
        # because the AI sent a NOT_DONE_YET marker, go for another round.
        if needs_feedback:
            for reply, metadata in self._answer(state='feedback'):
                yield reply, metadata

    def _run_tools(self, reply: str) -> Tuple[str, str, bool]:
        """Runs all tools on a reply. Returns the modified reply, a string
        that concatenates all output (an empty string if no output was 
        produced) and a bool indicating whether the AI should in turn repond
        to the produced output.
        """
        logger.info(f'running tools')
        results = []
        needs_reply = []
        for tool in self.tools.values():
            reply, tool_results, tool_needs_reply = tool.run(reply)
            if tool_results:
                results += tool_results
            needs_reply.append(tool_needs_reply)
        return reply, '\n\n'.join(results), any(needs_reply)
