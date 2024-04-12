from .. import config, utils
from . import OpenAIModel, BaseModel
from langchain.schema import SystemMessage, AIMessage, HumanMessage, \
    FunctionMessage


class MistralModel(OpenAIModel):
    
    supports_not_done_yet = False

    def __init__(self, heymans, model, **kwargs):
        from mistralai.async_client import MistralAsyncClient
        from mistralai.client import MistralClient
        BaseModel.__init__(self, heymans, **kwargs)
        self._model = model
        if self._tool_choice is not None:
            self._tool_choice = 'any'
        self._client = MistralClient(api_key=config.mistral_api_key)
        self._async_client = MistralAsyncClient(api_key=config.mistral_api_key)
        
    def convert_message(self, message):
        from mistralai.models.chat_completion import ChatMessage
        message = super().convert_message(message)
        return ChatMessage(**message)
        
    def predict(self, messages):
        if isinstance(messages, str):
            messages = [self.convert_message(messages)]
        else:
            messages = utils.prepare_messages(messages, allow_ai_first=False,
                                              allow_ai_last=False,
                                              merge_consecutive=True)
            messages = [self.convert_message(message) for message in messages]        
        return BaseModel.predict(self, messages)
    
    def invoke(self, messages):
        return self._client.chat(model=self._model, messages=messages,
                                 **self._tool_args())
        
    def async_invoke(self, messages):
        return self._async_client.chat(model=self._model, messages=messages,
                                       **self._tool_args())
