import logging
import jinja2
from types import GeneratorType
from typing import Tuple, Optional
from . import config, library
from .documentation import Documentation, FAISSDocumentationSource
from .messages import Messages
from .model import model
from .database.manager import DatabaseManager
from . import prompt
from . import tools
logger = logging.getLogger('heymans')


class Heymans:
    """The main chatbot class.
    
    Parameters
    ----------
    user_id: A user name
    persistent: Indicates whether the current session should be persistent in
        the sense of using the database.
    search_first: Indicates whether the answer phase should be preceded by a
        documentation search phase. If None, the config default will be used.
    search_tools: A list of tools to be used by the documentation search (if
        enabled). Values are class names from heymans.tools. If None, the
        config default will be used.
    answer_tools: A list of tools to be used during the answer phase (if
        enabled). Values are class names from heymans.tools. If None, the
        config default will be used.
    """
    def __init__(self, user_id: str, persistent: bool = False,
                 encryption_key: Optional[str] = None,
                 search_first: Optional[bool] = None,
                 search_tools: Optional[list] = None,
                 answer_tools: Optional[list] = None):
        self.user_id = user_id
        self.system_prompt = prompt.SYSTEM_PROMPT_ANSWER
        self._search_first = \
            config.search_first if search_first is None else search_first
        self.database = DatabaseManager(user_id, encryption_key)
        self.documentation = Documentation(
            self, sources=[FAISSDocumentationSource(self)])
        self.search_model = model(self, config.search_model)
        self.answer_model = model(self, config.answer_model)
        self.condense_model = model(self, config.condense_model)
        self.messages = Messages(self, persistent)
        if search_tools is None:
            search_tools = config.search_tools
        if answer_tools is None:
            answer_tools = config.answer_tools
        # Tools are class names from the tools module, which need to be
        # instantiated with heymans (self) as first argument
        self.search_tools = [getattr(tools, t)(self) for t in search_tools]
        self.answer_tools = [getattr(tools, t)(self) for t in answer_tools]
        self.tools = self.answer_tools
    
    def send_user_message(self, message: str) -> GeneratorType:
        """The main function that takes a user message and returns one or 
        replies. This is a generator function where each yield gives a tuple.
        
        This tuple can be (dict, dict) in which case the first dict contains an 
        action and a message key. This communicates to the client that an 
        action should be taking, such that the loading indicator should change.
        This tuple can also be (str, dict) in which case the str contains an
        AI message and the dict contains metadata for the message.
        """
        self.messages.append('user', message)
        if self._search_first:
            for reply, metadata in self._search(message):
                yield reply, metadata
        for reply, metadata in self._answer():
            yield reply, metadata
    
    def _search(self, message: str) -> GeneratorType:
        """Implements the documentation search phase."""
        yield {'action': 'set_loading_indicator',
               'message': f'{config.ai_name} is searching '}, {}
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
    
    def _answer(self, state: str = 'answer') -> GeneratorType:
        """Implements the answer phase."""
        yield {'action': 'set_loading_indicator',
               'message': f'{config.ai_name} is thinking and typing '}, {}        
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
        for tool in self.tools:
            reply, tool_results, tool_needs_reply = tool.run(reply)
            if tool_results:
                results += tool_results
            needs_reply.append(tool_needs_reply)
        return reply, '\n\n'.join(results), any(needs_reply)
