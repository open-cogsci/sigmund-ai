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
        """
        if system_prompt is None:
            system_prompt = self._system_prompt()
        model_prompt = [dict(role='system', content=system_prompt)]
        for msg_nr, (role, content) in enumerate(
                self._condensed_message_history):
            content = utils.remove_masked_elements(content)
            if role == 'user':
                # Prefix the last message with the current workspace
                if self.workspace_content and \
                        msg_nr == len(self._condensed_message_history) - 1:
                    content = prompt.render(
                        prompt.CURRENT_WORKSPACE,
                        workspace_content=self.workspace_content,
                        workspace_language=self.workspace_language) + content
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
        
    def _condense_message_history(self):
        system_prompt = self._system_prompt()
        # Determine the effective length of the condensed prompt while
        # excluding masked content. Makes content corresponds for example to
        # image data, and other kinds of data that are shown to the user but not
        # passed to the model.
        prompt_length = sum([
            len(utils.remove_masked_elements(content))
            for role, content in self._condensed_message_history
        ])
        logger.info(f'system prompt length: {len(system_prompt)}')
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
        """The system prompt that is used for question answering consists of
        several fragments.
        """
        system_prompt = [prompt.SYSTEM_PROMPT_IDENTITY]
        if self._sigmund.transient_system_prompt:
            system_prompt.append(self._sigmund.transient_system_prompt)
        # If available, documentation is also included in the prompt
        if len(self._sigmund.documentation):
            system_prompt.append(self._sigmund.documentation.prompt())
        # And finally, if the message history has been condensed, this is also
        # included.
        if self._condensed_text:
            logger.info('appending condensed text to system prompt')
            system_prompt.append(prompt.render(
                prompt.SYSTEM_PROMPT_CONDENSED,
                summary=self._condensed_text))
        # Combine all non-empty prompt chunks
        return '\n\n'.join(chunk for chunk in system_prompt if chunk.strip())    

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
        if self._persistent and modified:
            self.save()
    
    def save(self):
        conversation = {
            'condensed_text': self._condensed_text,
            'message_history': self._message_history,
            'condensed_message_history': self._condensed_message_history,
            'title': self._conversation_title,
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
        title_prompt = [dict(role='system', content=prompt.TITLE_PROMPT)]
        title_prompt += self.prompt()[2:]
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
