import logging
import jinja2
from .model import Model
logger = logging.getLogger('heymans')


SYSTEM_PROMPT_NO_DOC = '''You are Sigmund, an assistant for users of OpenSesame, a program for building psychology and neuroscience experiments.

Do not answer the user's question. Instead, search for relevant documentation by replying with the following JSON query: {"action": "search", "queries": ["search query 1", "search query 2"]}

Do not include additional text in your reply. You can search for multiple things at once.
'''

SYSTEM_PROMPT_WITH_DOC = '''You are Sigmund, an assistant for users of OpenSesame, a program for building psychology and neuroscience experiments.

You have retrieved the following documentation to answer the user's question:

<documentation>
{{ documentation }}
</documentation>

If you need additional documentation, reply with a JSON string as shown below without any additional text. You can search for multiple things at once.

```json
{"action": "search", "queries": ["search query 1", "search query 2"]}
```
'''

SYSTEM_PROMPT_CONDENSED = '''

Here is a summary of the start of the conversation. The rest of the messages follow up on this.

<summary>
{{ summary }}
</summary>
'''


class Messages:
    
    def __init__(self, heymans):
        self._heymans = heymans
        self._max_prompt_length = 5000
        self._condense_chunk_length = 2500
        self._condense_model = Model(heymans, model='gpt-3.5-turbo')
        self._condensed_text = None
        self._message_history = []
        self._condensed_message_history = []
        
    def append(self, role, message):
        self._message_history.append((role, message))
        self._condensed_message_history.append((role, message))
        self._condense_message_history()
        
    def _condense_message_history(self):
        system_prompt = self._system_prompt()
        messages = [{"role": "system", "content": system_prompt}]
        prompt_length = sum(len(content) for role, content
                            in self._condensed_message_history)
        logger.info(f'prompt length (without system prompt): {prompt_length} characters')
        if prompt_length <= self._max_prompt_length:
            logger.info('no need to condense')
            return
        condense_length = 0
        condense_messages = []
        while condense_length < self._condense_chunk_length:
            role, content = self._condensed_message_history.pop(0)
            condense_length += len(content)
            condense_messages.insert(0, (role, content))
        logger.info(f'condensing {len(condense_messages)} messages')
        condense_text = '\n\n'.join(
            f'You said: {content}' if role == 'system' else f'User said: {content}'
            for role, content in condense_messages)
        self._condensed_text = self._condense_model.predict(condense_text)
        
    def prompt(self):
        return [{'role': 'system', 'content': self._system_prompt()}] + \
            [{'role': role, 'content': content} for role, content
             in self._condensed_message_history]
    
    def _system_prompt(self):
        if len(self._heymans.documentation):
            logger.info('using system prompt with documentation')
            prompt = jinja2.Template(SYSTEM_PROMPT_WITH_DOC).render(
                documentation=str(self._heymans.documentation))
        else:
            logger.info('using system prompt without documentation')
            prompt = SYSTEM_PROMPT_NO_DOC
        if self._condensed_text:
            logger.info('appending condensed text to system prompt')
            prompt = prompt + jinja2.Template(SYSTEM_PROMPT_CONDENSED).render(
                summary=self._condensed_text)
        return prompt
