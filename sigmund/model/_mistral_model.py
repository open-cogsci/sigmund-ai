from .. import config, utils
from . import BaseModel
from ._openai_model import OpenAIModel
import logging
from langchain.schema import SystemMessage, AIMessage, HumanMessage, \
    FunctionMessage
logger = logging.getLogger('sigmund')


class MistralModel(OpenAIModel):
    
    supports_not_done_yet = False

    def __init__(self, sigmund, model, **kwargs):
        from mistralai.async_client import MistralAsyncClient
        from mistralai.client import MistralClient
        BaseModel.__init__(self, sigmund, **kwargs)
        self._model = model
        if self._tool_choice is not None:
            self._tool_choice = 'any'
        self._client = MistralClient(api_key=config.mistral_api_key)
        self._async_client = MistralAsyncClient(api_key=config.mistral_api_key)
        
    def predict(self, messages):
        if isinstance(messages, str):
            messages = [self.convert_message(messages)]
        else:
            messages = utils.prepare_messages(messages, allow_ai_first=False,
                                              allow_ai_last=False,
                                              merge_consecutive=True)
            messages = [self.convert_message(message) for message in messages]
            messages = self._prepare_tool_messages(messages)
        # Mistral requires an assistant message after a tool message
        while True:
            for i, message in enumerate(messages[:-1]):
                next_message = messages[i + 1]
                if message['role'] == 'tool' and \
                        next_message['role'] == 'user':
                    break
            else:
                break
            logger.info('adding assistant message between tool and user')
            messages.insert(i + 1, {'role': 'assistant',
                                'content': 'Tool was executed.'})
        return BaseModel.predict(self, messages)
        
    def _mistral_invoke(self, fnc, messages):
        # Mistral tends to get stuck in a loop where the same tool is called
        # over and over again. To fix this, we temporarily disallow tools when
        # the last message was a tool.
        if messages[-1]['role'] == 'tool':
            kwargs = {}
        else:
            kwargs = self._tool_args()        
        kwargs.update(config.mistral_kwargs)
        if self.json_mode:
            kwargs['response_format'] = {"type": "json_object"}
        return fnc(model=self._model, messages=messages, **kwargs)
    
    def invoke(self, messages):
        return self._mistral_invoke(self._client.chat, messages)
        
    def async_invoke(self, messages):
        return self._mistral_invoke(self._async_client.chat, messages)
