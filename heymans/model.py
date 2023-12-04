from . import config
import re
import json
import logging
from langchain.schema import AIMessage
import time
logger = logging.getLogger('heymans')


class BaseModel:
    
    def __init__(self, heymans):
        self._heymans = heymans

    def predict(self, messages):
        t0 = time.time()
        logger.info(f'predicting with {self.__class__} model')
        if isinstance(messages, str):
            reply = self._model.predict(messages)
            dt = time.time() - t0
            logger.info(f'predicting {len(reply) + len(messages)} took {dt} s')
        else:
            reply = self._model.predict_messages(messages).content
            dt = time.time() - t0
            msg_len = sum([len(m.content) for m in messages])
            logger.info(f'predicting {len(reply) + msg_len} took {dt} s')
            if reply.startswith('```json\n') and reply.endswith('```'):
                reply = reply.strip().lstrip('```json\n').rstrip('```')
            try:
                request = json.loads(reply)
            except json.JSONDecodeError:
                logger.info('received regular reply')
                return reply
            if isinstance(request, dict):
                logger.info(f'reply is JSON request: {request}')
                return request
            logger.info('reply is JSON but not a request, treating as regular')
        return reply


class GPT4Model(BaseModel):

    def __init__(self, heymans):
        from langchain.chat_models import ChatOpenAI
        super().__init__(heymans)
        self._model = ChatOpenAI(
            model='gpt-4-1106-preview',
            openai_api_key=config.openai_api_key)
        
        
class GPT35Model(BaseModel):

    def __init__(self, heymans):
        from langchain.chat_models import ChatOpenAI
        super().__init__(heymans)
        self._model = ChatOpenAI(
            model='gpt-3.5-turbo-1106',
            openai_api_key=config.openai_api_key)
        
        
class Claude21Model(BaseModel):
    
    def __init__(self, heymans):
        from langchain.chat_models import ChatAnthropic
        super().__init__(heymans)
        self._model = ChatAnthropic(
            model='claude-2.1', anthropic_api_key=config.anthropic_api_key)
        
    def predict(self, messages):
        if isinstance(messages, list) and isinstance(messages[1], AIMessage):
            logger.info('removing first assistant mesage')
            messages.pop(1)
        return super().predict(messages)
            
        
def model(heymans, model):
    
    if model == 'gpt-4':
        return GPT4Model(heymans)
    if model == 'gpt-3.5':
        return GPT35Model(heymans)
    if model == 'claude-2.1':
        return Claude21Model(heymans)
    raise ValueError(f'Unknown model: {model}')
