import logging
import json
import zlib
import uuid
import time
from pathlib import Path
from .model import model
from . import prompt, config, utils, attachments
from langchain.schema import HumanMessage, AIMessage, SystemMessage
logger = logging.getLogger('heymans')


class Messages:
    
    def __init__(self, heymans, persistent=False):
        self._heymans = heymans
        self._persistent = persistent
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
        metadata['search_model'] = 'Welcome message'
        self._conversation_title = config.default_conversation_title
        self._message_history = [('assistant', self.welcome_message(), 
                                  metadata)]
        self._condensed_message_history = [
            (role, content) for role, content, metadata
            in self._message_history[:]]        
            
    def metadata(self):
        return {'timestamp': utils.current_datetime(),
                'sources': self._heymans.documentation.to_json(),
                'search_model': config.search_model,
                'condense_model': config.condense_model,
                'answer_model': config.answer_model}
        
    def append(self, role, message):
        metadata = self.metadata()
        self._message_history.append((role, message, metadata))
        self._condensed_message_history.append((role, message))
        self._condense_message_history()
        if self._persistent:
            self.save()
        return metadata
    
    def prompt(self):
        """The prompt consists of the system prompt followed by a sequence of
        AI and user messages. Transient messages are special messages that are
        hidden except when they are the last message. This allows the AI to 
        feed some information to itself to respond to without confounding the
        rest of the conversation.
        """
        model_prompt = [SystemMessage(content=self._system_prompt())]
        for i, (role, content) in enumerate(self._condensed_message_history):
            transient = prompt.TRANSIENT_MARKER in content
            last_message = i + 1 == len(self._condensed_message_history)
            if transient and not last_message:
                logger.info('hiding transient message in prompt')
                continue
            if role == 'assistant':
                model_prompt.append(AIMessage(content=content))
            elif role == 'user':
                model_prompt.append(HumanMessage(content=content))
            else:
                raise ValueError(f'Invalid role: {role}')
        return model_prompt

    def welcome_message(self):
        return config.welcome_message
        
    def _condense_message_history(self):
        system_prompt = self._system_prompt()
        messages = [{"role": "system", "content": system_prompt}]
        prompt_length = sum(len(content) for role, content
                            in self._condensed_message_history)
        logger.info(f'system prompt length: {len(system_prompt)}')
        logger.info(f'prompt length (without system prompt): {prompt_length}')
        if prompt_length <= config.max_prompt_length:
            logger.info('no need to condense')
            return
        condense_length = 0
        condense_messages = []
        while condense_length < config.condense_chunk_length:
            role, content = self._condensed_message_history.pop(0)
            condense_length += len(content)
            condense_messages.insert(0, (role, content))
        logger.info(f'condensing {len(condense_messages)} messages')
        condense_prompt = prompt.render(
            prompt.CONDENSE_HISTORY,
            history=''.join(
                f'You said: {content}' if role == 'system' else f'User said: {content}'
                for role, content in condense_messages))
        self._condensed_text = self._heymans.condense_model.predict(
            condense_prompt)
        
    def _system_prompt(self):
        system_prompt = [prompt.render(
            self._heymans.system_prompt,
            current_datetime=utils.current_datetime())]
        for tool in self._heymans.tools.values():
            if tool.prompt:
                system_prompt.append(tool.prompt)
        system_prompt.append(
            attachments.attachments_prompt(self._heymans.database))
        if len(self._heymans.documentation):
            system_prompt.append(self._heymans.documentation.prompt())
        if self._condensed_text:
            logger.info('appending condensed text to system prompt')
            system_prompt.append(prompt.render(
                prompt.SYSTEM_PROMPT_CONDENSED,
                summary=self._condensed_text))
        return '\n\n'.join(system_prompt)
        
    def _update_title(self):
        """The conversation title is updated when there are at least two 
        messages, excluding the system prompt and AI welcome message. Based on
        the last messages, a summary title is then created.
        """
        if len(self) <= 2 or \
                self._conversation_title != config.default_conversation_title:
            return
        title_prompt = [SystemMessage(content=prompt.TITLE_PROMPT)]
        title_prompt += self.prompt()[2:]
        self._conversation_title = self._heymans.condense_model.predict(
            title_prompt).strip('"\'')
        if len(self._conversation_title) > 100:
            self._conversation_title = self._conversation_title[:100] + '…'
        print(f'new conversation title: {self._conversation_title}')

    def load(self):
        conversation = self._heymans.database.get_active_conversation()
        if not conversation['message_history']:
            self.init_conversation()
            return
        self._conversation_title = conversation['title']
        self._message_history = conversation['message_history']
        self._condensed_text = conversation['condensed_text']
        self._condensed_message_history = \
            conversation['condensed_message_history']
    
    def save(self):
        self._update_title()
        conversation = {
            'condensed_text': self._condensed_text,
            'message_history': self._message_history,
            'condensed_message_history': self._condensed_message_history,
            'title': self._conversation_title,
        }
        self._heymans.database.update_active_conversation(conversation)
