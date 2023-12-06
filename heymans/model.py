from . import config
import re
import json
import logging
import asyncio
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
    
    def predict_multiple(self, prompts):
        """Predicts multiple simple (non-message history) prompts using asyncio
        if possible.
        """
        try:
            loop = asyncio.get_event_loop()
            if not loop.is_running():
                logger.info('re-using async event loop')
                use_async = True
            else:
                logger.info('async event loop is already running')
                use_async = False
        except RuntimeError as e:
            logger.info('creating async event loop')
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            use_async = True
            
        if not use_async:
            logger.info('predicting multiple without async')
            return [self._model.predict(prompt) for prompt in prompts]
            
        async def wrap_gather():
            tasks = [self._model.apredict(prompt) for prompt in prompts]
            return await asyncio.gather(*tasks)
            
        logger.info('predicting multiple using async')
        return loop.run_until_complete(wrap_gather())


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
