from .. import config
from . import BaseModel
from langchain.schema import SystemMessage, AIMessage, HumanMessage, \
    FunctionMessage


class OpenAIModel(BaseModel):

    supports_not_done_yet = True

    def __init__(self, heymans, model, **kwargs):
        from openai import Client, AsyncClient
        super().__init__(heymans, **kwargs)
        self._model = model
        if self._tool_choice not in (None, 'auto'):
            self._tool_choice = {"type": "function",
                                 "function": {"name": self._tool_choice}}
        self._client = Client(api_key=config.openai_api_key)
        self._async_client = AsyncClient(api_key=config.openai_api_key)
        
    def convert_message(self, message):
        # OpenAI expects messages as dict objects
        if isinstance(message, str):
            return dict(role='user', content=message)
        if isinstance(message, SystemMessage):
            role = 'system'
        elif isinstance(message, AIMessage):
            role = 'assistant'
        elif isinstance(message, HumanMessage):
            role = 'user'
        elif isinstance(message, FunctionMessage):
            role = 'tool'
        else:
            raise ValueError(f'Unknown message type: {message}')
        return dict(role=role, content=message.content)
        
    def predict(self, messages):
        # Strings need to be converted a list of length one with a single
        # message dict
        if isinstance(messages, str):
            messages = [self.convert_message(messages)]
        else:
            messages = [self.convert_message(message) for message in messages]
            # OpenAI requires the tool message to be linked to the previous AI
            # message with a tool_call_id. The actual content doesn't appear to
            # matter, so here we dummy-link the messages
            for i, message in enumerate(messages):
                if i == 0 or message['role'] != 'tool':
                    continue
                tool_call_id = f'call_{i}'
                prev_message = messages[i - 1]
                prev_message['tool_calls'] = [
                    {
                        'id': tool_call_id,
                        'type': 'function',
                        'function': {
                            'name': 'dummy',
                            'arguments': ''
                        }
                    }]
                message['tool_call_id'] = tool_call_id        
        return super().predict(messages)
        
    def predict_multiple(self, prompts):
        prompts = [[self.convert_message(prompt)] for prompt in prompts]
        return super().predict_multiple(prompts)
        
    def get_response(self, response):
        tool_calls = response.choices[0].message.tool_calls
        if tool_calls:
            function = tool_calls[0].function
            for tool in self._tools:
                if tool.name == function.name:
                    return tool.bind(function.arguments)
            return self.invalid_tool
        return response.choices[0].message.content
    
    def _tool_args(self):
        if not self._tools:
            return {}
        return {'tools': self.tools(), 'tool_choice': self._tool_choice}
        
    def invoke(self, messages):
        return self._client.chat.completions.create(
            model=self._model, messages=messages, **self._tool_args())
        
    def async_invoke(self, messages):
        return self._async_client.chat.completions.create(
            model=self._model, messages=messages, **self._tool_args())
