import logging
import uuid
from cryptography.fernet import InvalidToken
import multiprocessing as mp
from . import prompt, config, utils
logger = logging.getLogger('sigmund')


class Messages:

    def __init__(self, sigmund, persistent=False):
        self._sigmund = sigmund
        self._persistent = persistent
        self._conversation_id = None
        self.workspace_content = None
        self.workspace_language = None
        if self._persistent:
            self.load()
        else:
            self.init_conversation()

    def __len__(self):
        return len(self._message_history)

    def __iter__(self):
        for msg in self._message_history:
            yield msg

    def init_conversation(self):
        self._condensed_text = None
        self._notes = {}
        metadata = self.metadata()
        metadata['answer_model'] = 'welcome-bot'
        self._conversation_title = config.default_conversation_title
        self._message_history = [['assistant', self.welcome_message(), 
                                  metadata]]
        self._condensed_message_history = [
            [role, content] for role, content, metadata
            in self._message_history[:]]        

    def metadata(self, workspace_content: str = None,
                 workspace_language: str = None, message_id: str = None):
        return {'message_id': str(uuid.uuid4()) 
                    if message_id is None else message_id,
                'workspace_content': workspace_content,
                'workspace_language': workspace_language,
                'timestamp': utils.current_datetime(),
                'sources': self._sigmund.documentation.to_json(),
                'condense_model': self._sigmund.model_config['condense_model'],
                'answer_model': self._sigmund.model_config['answer_model']}

    def append(self, role: str, message: str, workspace_content: str = None,
               workspace_language: str = None, message_id: str = None):
        metadata = self.metadata(workspace_content=workspace_content,
                                 workspace_language=workspace_language,
                                 message_id=message_id)
        self._message_history.append([role, message, metadata])
        self._condensed_message_history.append([role, message])
        self._condense_message_history()
        if self._persistent:
            self.save()
        return metadata

    def delete(self, message_id):
        message_to_remove = None
        condensed_message_to_remove = None
        for role, message, metadata in self._message_history:
            if metadata['message_id'] == message_id:
                message_to_remove = [role, message, metadata]
                condensed_message_to_remove = [role, message]
                break
        else:
            logger.info(f'message not found for deletion: {message_id}')
            return
        if message_to_remove:
            logger.info(f'deleting message: {message_id}')
            self._message_history.remove(message_to_remove)
        if condensed_message_to_remove:
            try:
                self._condensed_message_history.remove(
                    condensed_message_to_remove)
            except ValueError:
                logger.error(
                    f'Could not find condensed message to remove for {message_id}')
        if self._persistent:
            self.save()

    def prompt(self, system_prompt=None):
        """The prompt consists of the system prompt followed by a sequence of
        AI, user, and tool/ function messages.

        If no system prompt is provided, one is automatically constructed.
        Typically, an explicit system_prompt is provided during the search
        phase, but not during the answer phase.
        
        Dynamic context (documentation, notes, condensed history) is prepended
        to the last user message rather than included in the system prompt so
        that the system prompt remains static and cacheable.
        """
        auto_prompt = system_prompt is None
        if auto_prompt:
            system_prompt = self._system_prompt()
        model_prompt = [dict(role='system', content=system_prompt)]
        for msg_nr, (role, content) in enumerate(
                self._condensed_message_history):
            content = utils.remove_masked_elements(content)
            if role == 'user' and \
                    msg_nr == len(self._condensed_message_history) - 1:
                # Prefix the last user message with dynamic context and
                # the current workspace
                prefix_parts = []
                if auto_prompt:
                    context = self._user_message_context()
                    if context:
                        prefix_parts.append(context)
                if self.workspace_content:
                    prefix_parts.append(prompt.render(
                        prompt.CURRENT_WORKSPACE,
                        workspace_content=self.workspace_content,
                        workspace_language=self.workspace_language))
                if prefix_parts:
                    content = ''.join(prefix_parts) + content
            model_prompt.append(dict(role=role, content=content))
        return model_prompt

    def visible_messages(self):
        """Yields role, message, metadata while ignoring messages and 
        converting tool messages into user messages with tool result as 
        content. This is mainly for display in the web interface.
        """
        for role, message, metadata in self:
            if role == 'tool':
                continue
            if not message.strip():
                continue
            yield role, message, metadata

    def welcome_message(self):
        return config.welcome_message

    # Notes management

    def set_note(self, label, content):
        """Add or update a persistent note."""
        self._notes[label] = content

    def remove_note(self, label):
        """Remove a persistent note. Does nothing if label doesn't exist."""
        self._notes.pop(label, None)

    def get_notes(self):
        """Return a copy of the current notes dict."""
        return dict(self._notes)

    def _condense_message_history(self):
        system_prompt = self._system_prompt()
        user_message_context = self._user_message_context()
        # Determine the effective length of the condensed prompt while
        # excluding masked content. Masked content corresponds for example to
        # image data, and other kinds of data that are shown to the user but
        # not passed to the model. The user_message_context is included in the
        # length calculation because it will be prepended to the last user 
        # message.
        prompt_length = sum([
            len(utils.remove_masked_elements(content))
            for role, content in self._condensed_message_history
        ]) + len(user_message_context)
        logger.info(f'system prompt length: {len(system_prompt)}')
        logger.info(
            f'user message context length: {len(user_message_context)}')
        logger.info(
            f'condensed prompt length (without system prompt): {prompt_length}')
        if prompt_length <= config.max_prompt_length:
            logger.info('no need to condense')
            return
        condense_length = 0
        condense_messages = []
        while self._condensed_message_history and \
                condense_length < config.condense_chunk_length:
            if len(self._condensed_message_history) <= 2:
                break
            role, content = self._condensed_message_history.pop(0)
            content = utils.remove_masked_elements(content)
            condense_length += len(content)
            condense_messages.insert(0, (role, content))
        logger.info(f'condensing {len(condense_messages)} messages')
        condense_prompt = prompt.render(
            prompt.CONDENSE_HISTORY,
            history=''.join(
                f'You said: {content}' if role == 'system' 
                else f'User said: {content}'
                for role, content in condense_messages))
        result = self._sigmund.condense_model.predict(condense_prompt)
        # Just in case a model gets confused and returns a tool call.
        if not isinstance(result, str):
            logger.error(f'condense model returned non-string result: {result}')
            return
        self._condensed_text = result.strip()

    def _system_prompt(self):
        """The system prompt only contains the static identity to maximize
        cache effectiveness. All dynamic content (documentation, notes,
        condensed history) is moved to _user_message_context().
        """
        return prompt.SYSTEM_PROMPT_IDENTITY

    def _user_message_context(self):
        """Builds dynamic context that is prepended to the last user message
        in a <user_message_context> section. This keeps the system prompt 
        static for caching purposes.
        
        Includes: transient system prompt, documentation, persistent notes,
        and condensed conversation history.
        """
        context_parts = []
        if self._sigmund.transient_system_prompt:
            context_parts.append(self._sigmund.transient_system_prompt)
        # If available, documentation is also included in the context
        if len(self._sigmund.documentation):
            context_parts.append(self._sigmund.documentation.prompt())
        # If there are persistent notes, include them
        if self._notes:
            if config.log_replies:
                for label in self._notes:
                    logger.info(f'[note] {label}')
            context_parts.append(prompt.render(
                prompt.SYSTEM_PROMPT_NOTES,
                notes=self._notes))
        # If the message history has been condensed, include the summary
        if self._condensed_text:
            logger.info('appending condensed text to user message context')
            context_parts.append(prompt.render(
                prompt.SYSTEM_PROMPT_CONDENSED,
                summary=self._condensed_text))
        if not context_parts:
            return ''
        context = '\n\n'.join(part for part in context_parts if part.strip())
        return f'<user_message_context>\n{context}\n</user_message_context>\n\n'

    def load(self):
        try:
            conversation = self._sigmund.database.get_active_conversation()
        except InvalidToken as e:
            self.init_conversation()
            self.save()
            logger.error(f'failed to get active conversation: {e}')
            return
        if not conversation['message_history']:
            self.init_conversation()
            return
        modified = False
        for _, _, metadata in conversation['message_history']:
            if 'message_id' not in metadata:
                metadata['message_id'] = str(uuid.uuid4())
                modified = True
        self._conversation_title = conversation['title']
        self._message_history = conversation['message_history']
        self._condensed_text = conversation['condensed_text']
        self._condensed_message_history = \
            conversation['condensed_message_history']
        self._notes = conversation.get('notes', {})
        if self._persistent and modified:
            self.save()

    def save(self):
        conversation = {
            'condensed_text': self._condensed_text,
            'message_history': self._message_history,
            'condensed_message_history': self._condensed_message_history,
            'title': self._conversation_title,
            'notes': self._notes,
        }
        self._conversation_id = self._sigmund.database.update_active_conversation(conversation)
        # We update the title in a background process so that we don't block
        # the conversation
        mp.Process(target=self._update_title).start()

    def _update_title(self):
        """The conversation title is updated when there are at least two 
        messages, excluding the system prompt and AI welcome message. Based on
        the last messages, a summary title is then created.

        This method is run in a separate process to avoid blocking the main thread.
        """
        if len(self) <= 2 or \
                self._conversation_title != config.default_conversation_title:
            return
        logger.info('updating conversation title')
        # To make sure that all models understand that the conversation should
        # be summarized into the title, we add the title prompt to the system
        # prompt as well as the last user message. If the prompt already ends
        # with a user message, we strip it.
        title_prompt = [dict(role='system', content=prompt.TITLE_PROMPT)]
        title_prompt += self.prompt()[2:]
        if title_prompt[-1]['role'] == 'user':
            title_prompt.pop()
        title_prompt.append(dict(role='user', content=prompt.TITLE_PROMPT))
        suggested_title = self._sigmund.condense_model.predict(title_prompt)
        # The prediction may be a tool call, so we need to check if it is a str.
        # This should not ordinarily happen, but sometimes models get confused.
        if not isinstance(suggested_title, str):
            logger.error(f'suggested conversation title is not str, but: {suggested_title}')
            return
        self._conversation_title = suggested_title.strip('"\'')
        if len(self._conversation_title) > 100:
            self._conversation_title = self._conversation_title[:100] + '…'
        self._sigmund.database.set_conversation_title(
            self._conversation_id, self._conversation_title)
        logger.info('completed updating conversation title')