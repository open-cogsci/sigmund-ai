from . import BaseModel
from .. import config


class AnthropicModel(BaseModel):
    
    max_retry = 3
    
    def __init__(self, heymans, model):
        from langchain_anthropic import ChatAnthropic
        super().__init__(heymans)
        self._model = ChatAnthropic(
            model=model, anthropic_api_key=config.anthropic_api_key)
        
    def predict(self, messages):
        if isinstance(messages, list):
            messages = utils.prepare_messages(messages, allow_ai_first=False,
                                              allow_ai_last=False,
                                              merge_consecutive=True)
        # Claude seems to crash occasionally, in which case a retry will do the
        # trick
        for i in range(self.max_retry):
            try:
                return super().predict(messages)
            except Exception as e:
                logger.warning(f'error in prediction (retrying): {e}')
        return super().predict(messages)
        
