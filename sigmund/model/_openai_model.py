import json
import logging
from .. import config
from . import BaseModel


logger = logging.getLogger('sigmund')


class OpenAIModel(BaseModel):

    def __init__(self, sigmund, model, **kwargs):
        from openai import Client, AsyncClient
        super().__init__(sigmund, **kwargs)
        self._model = model
        if self._tool_choice not in (None, 'auto'):
            self._tool_choice = {"type": "function",
                                 "function": {"name": self._tool_choice}}
        self._client = Client(api_key=config.openai_api_key)
        self._async_client = AsyncClient(api_key=config.openai_api_key)
        
    def predict(self, messages, attachments=None, track_tokens=True):
        # Strings need to be converted a list of length one with a single
        # message dict
        if isinstance(messages, str):
            messages = [self.convert_message(messages)]
        else:
            messages = [self.convert_message(message) for message in messages]
            messages = self._prepare_tool_messages(messages)
        # Attachments are included with the last message. The content is now
        # no longer a single str, but a list of dict            
        if attachments:
            logger.info('adding attachments to last message')
            content = [{'type': 'text', 'text': messages[-1]['content']}]
            for attachment in attachments:
                if attachment['type'] == 'image':
                    content.append({
                        'type': 'image_url',
                        'image_url': {'url': attachment['url']}
                        })
                elif attachment['type'] == 'document':
                    content.append({
                        'type': 'file',
                        'file': {
                            'filename': attachment['file_name'],
                            'file_data': attachment['url']
                        }})
            messages[-1]['content'] = content            
        return super().predict(messages, attachments, track_tokens)
        
    def _tool_call_id(self, nr):
        return f'call_{nr}'
        
    def _prepare_tool_messages(self, messages):
        # OpenAI requires the tool message to be linked to the previous AI
        # message with a tool_call_id. The actual content doesn't appear to
        # matter, so here we dummy-link the messages
        # The system message cannot have tool_calls information, so in that 
        # case we add a dummy message. 
        # import pprint
        # print('=== preparing tool messages')
        # pprint.pprint(messages)
        # print('---')
        if len(messages) > 1 and messages[1]['role'] == 'tool':
            logger.info('insert dummy assistant message before tool')
            messages.insert(1, {'role': 'assistant'})
        for i, message in enumerate(messages):
            if i == 0 or message['role'] != 'tool':
                continue
            tool_info = json.loads(message['content'])
            tool_call_id = self._tool_call_id(i)
            prev_message = messages[i - 1]
            # an assistant message should not have both content and tool calls
            prev_message['content'] = ''
            prev_message['tool_calls'] = [
                {
                    'id': tool_call_id,
                    'type': 'function',
                    'function': {
                        'name': tool_info['name'],
                        'arguments': tool_info['args']
                    }
                }]
            message['tool_call_id'] = tool_call_id       
            message['name'] = tool_info['name']
            message['content'] = tool_info['content']
            if message['content'] is None:
                message['content'] = ''
        # pprint.pprint(messages)
        # print('=== end preparing tool messages')                
        return messages
        
    def get_response(self, response):
        tool_calls = response.choices[0].message.tool_calls
        if tool_calls:
            function = tool_calls[0].function
            for tool in self._tools:
                if tool.name == function.name:
                    return tool.bind(function.arguments)
            logger.warning(f'invalid tool called: {function}')
            return self.invalid_tool
        return response.choices[0].message.content
    
    def _tool_args(self):
        if not self._tools:
            return {}
        return {'tools': self.tools(), 'tool_choice': self._tool_choice}
        
    def _openai_invoke(self, fnc, messages):
        kwargs = self._tool_args()
        kwargs.update(config.openai_kwargs)
        if self.json_mode:
            kwargs['response_format'] = {"type": "json_object"}        
        return fnc(model=self._model, messages=messages, **kwargs)
        
    def invoke(self, messages):
        return self._openai_invoke(
            self._client.chat.completions.create, messages=messages)
        
    def async_invoke(self, messages):
        return self._openai_invoke(
            self._async_client.chat.completions.create, messages=messages)
