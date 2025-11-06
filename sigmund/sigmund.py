import logging
import json
from types import GeneratorType
from . import config
from .reply import Reply, ActionReply
from .documentation import Documentation
from .messages import Messages
from .model import model
from . import tools as mod_tools
from .database.manager import DatabaseManager
from . import utils
logger = logging.getLogger('sigmund')


class Sigmund:
    """The main chatbot class.
    
    Parameters
    ----------
    user_id: A user name
    persistent: Indicates whether the current session should be persistent in
        the sense of using the database.
    encryption_key: A key to encrypt the database.
    model_config: Indicates the model configuration. If none, the config
        default will be used.
    tools: A list of tools to use. If None, the config default will be used.
    transient_settings: A dictionary of settings that will be used for the
        current session only.
    transient_system_prompt: A system prompt that will be added to the default
        system prompt for the current session only.
    foundation_document_topics: A list of topics. Foundation documents matching 
        these topics are always included in the context.
    """
    def __init__(self, user_id: str, persistent: bool = False,
                 encryption_key: str = None,
                 model_config: str = None,
                 tools: list = None,
                 transient_settings: dict = None,
                 transient_system_prompt: str = None,
                 foundation_document_topics: list = None):
        self.user_id = user_id
        self.database = DatabaseManager(self, user_id, encryption_key)
        if transient_settings:
            logger.info(f'using transient settings: {transient_settings}')
            self.database.transient_settings = transient_settings
        self.transient_system_prompt = transient_system_prompt
        # Available model configs may change with updates, but the user settings
        # are not updated along with this. Therefore, if a model config doesn't
        # exist, we reset to the default.
        if model_config is None:
            model_config = self.database.get_setting('model_config')
        if model_config not in config.model_config:
            logger.warning(
                f'model_config {model_config} not found, resetting to default')
            model_config = config.settings_default['model_config']
            self.database.set_setting('model_config', model_config)
        self.model_config = config.model_config[model_config]
        self.documentation = Documentation(
            self, foundation_document_topics=foundation_document_topics)
        self.messages = Messages(self, persistent)
        if tools is None:
            tools = [t for t in config.tools
                     if self.database.get_setting(f'tool_{t}') == 'true']
        # Tools are class names from the tools module, which need to be
        # instantiated with sigmund (self) as first argument
        self.tools = [getattr(mod_tools, t)(self) for t in tools]
        # If there are answer tools, the mode can choose freely
        if tools:
            tool_choice = 'auto'
        else:
            tool_choice = None
        self.answer_model = model(self, self.model_config['answer_model'],
                                  tools=self.tools,
                                  tool_choice=tool_choice)
        self.condense_model = model(self, self.model_config['condense_model'])
        self.public_model = model(self, self.model_config['public_model'])
    
    def send_user_message(self, message: str, workspace_content: str = None,
                          workspace_language: str = 'text',
                          attachments: list = None,
                          message_id: str = None) -> GeneratorType:
        """The main function that takes a user message and returns one or 
        replies. This is a generator function where each yield gives a tuple.
        
        This tuple can be (dict, dict, str) in which case the first dict 
        contains an action and a message key. This communicates to the client 
        that an action should be taking, such that the loading indicator should
        change. This tuple can also be (str, dict, str) in which case the first
        str contains an AI message and the dict contains metadata for the 
        message. The third element corresponds to the content of the workspace,
        and can be None if empty.
        """
        # A temporary hack to prune messages for accounts
        if message == 'prune_detached_messages()':
            yield ActionReply(
                f'{config.ai_name} is pruning detached messages ')
            self.database.prune_detached_messages()
            return Reply('Done', None, None, None)
        if config.log_replies:
            logger.info(f'[user message] {message}')
        if self._rate_limit_exceeded():
            yield Reply(config.max_tokens_per_hour_exceeded_message,
                        self.messages.metadata())
            return
        self.messages.workspace_content = workspace_content
        self.messages.workspace_language = workspace_language
        self.messages.append('user', 
                             message=message,
                             workspace_content=workspace_content,
                             workspace_language=workspace_language,
                             message_id=message_id)
        if config.search_enabled and self.documentation.enabled:
            # Search queries work best if they'r not too short. That's why we
            # include preceding messages until the search query reaches the
            # minimum length, or until there are no more messages. (The welcome
            # message is always excluded.)
            query_messages = []
            query_len = 0
            # Inversely loop through the message history, ignoring the very first
            # message, because it is a welcome message.
            for _, msg, _ in self.messages._message_history[-1:0:-1]:
                query_messages.insert(0, msg)
                query_len += len(msg)
                if query_len > config.search_min_query_length:
                    break
            logger.info(f'using {len(query_messages)} message(s) for search query')
            logger.info(f'query length: {query_len}')
            query = '\n\n'.join(query_messages)
            query = query[:config.search_max_query_length]
            for reply in self._search(query):
                yield reply
        for reply in self._answer(attachments):
            yield reply
            
    def _rate_limit_exceeded(self):
        tokens_consumed_past_hour = self.database.get_activity()
        logger.info(
            f'tokens consumed in past hour: {tokens_consumed_past_hour}')
        return tokens_consumed_past_hour > config.max_tokens_per_hour
    
    def _search(self, message: str) -> GeneratorType:
        """Implements the documentation search phase."""
        yield ActionReply(f'{config.ai_name} is searching ')
        logger.info('[search state] entering')
        self.documentation.clear()
        # First seach based on the user question
        logger.info('[search state] searching based on user message')
        self.documentation.search(message)
        logger.info(
            f'[search state] {len(self.documentation._documents)} documents, {len(self.documentation)} characters')
    
    def _answer(self, attachments: [] = None,
                state: str = 'answer') -> GeneratorType:
        """Implements the answer phase."""
        yield ActionReply(f'{config.ai_name} is thinking and typing ')
        logger.info(f'[{state} state] entering')
        # We first collect a regular reply to the user message. While doing so
        # we also keep track of the number of tokens consumed.
        tokens_consumed_before = self.answer_model.total_tokens_consumed
        reply = self.answer_model.predict(self.messages.prompt(),
                                          attachments=attachments)
        if isinstance(reply, str) and self.documentation.poor_match:
            reply = '''<div class="message-info" markdown="1">Expert knowledge is enabled, but Sigmund was unable to find useful documentation to answer your question. To get a more useful answer:
            
- Provide more details and relevant keywords
- Or: Enable expert knowledge that is relevant to your question (see Menu)
- Or: Disable all expert knowledge to discuss general subjects (see Menu)
</div>\n\n''' + reply
        tokens_consumed = self.answer_model.total_tokens_consumed \
            - tokens_consumed_before
        logger.info(f'tokens consumed: {tokens_consumed}')
        self.database.add_activity(tokens_consumed)        
        if config.log_replies:
            logger.info(f'[{state} state] reply: {reply}')
        # If the reply is a callable, then it's a tool that we need to run
        if callable(reply):
            tool_message, tool_result, tool_language, needs_feedback = reply()
            if needs_feedback:
                logger.info(f'[{state} state] tools need feedback')
                if not self.answer_model.supports_tool_feedback:
                    logger.info(
                        f'[{state} state] model does not support feedback')
                    needs_feedback = False
            tool_message, workspace_content, workspace_language = \
                utils.extract_workspace(tool_message)
            # If the tool has a result and no workspace content was included in
            # the message itself, use the result as the workspace message. Also
            # remember the tool result it in the mssage history.
            if tool_result:
                if workspace_content is None:
                    workspace_content = tool_result['content']
                    workspace_language = tool_language
                metadata = self.messages.append(
                    'assistant', message=tool_message,
                    workspace_content=workspace_content,
                    workspace_language=workspace_language)
                self.messages.append('tool', message=json.dumps(tool_result))
            else:
                metadata = self.messages.append('assistant', tool_message)
            yield Reply(tool_message, metadata, workspace_content,
                        workspace_language)
        # Otherwise the reply is a regular AI message
        else:
            reply, workspace_content, workspace_language = \
                utils.extract_workspace(reply)
            metadata = self.messages.append(
                'assistant',
                message=reply,
                workspace_content=workspace_content,
                workspace_language=workspace_language)
            yield Reply(reply, metadata, workspace_content, workspace_language)
            needs_feedback = False
        # If feedback is required by a tool, go for another round.
        if needs_feedback and not self._rate_limit_exceeded():
            if workspace_content is not None:
                logger.info('workspace content has been updated for feedback')
                self.messages.workspace_content = workspace_content
                self.messages.workspace_language = workspace_language
            for reply in self._answer(attachments, state='feedback'):
                yield reply
