from . import config, utils
import re
import json
import logging
import asyncio
from langchain_community.callbacks import get_openai_callback
import time
logger = logging.getLogger('heymans')


class BaseModel:
    
    supports_not_done_yet = False
    characters_per_token = 4
    
    def __init__(self, heymans):
        self._heymans = heymans
        self.total_tokens_consumed = 0
        self.prompt_tokens_consumed = 0
        self.completion_tokens_consumed = 0

    def predict(self, messages, track_tokens=True):
        t0 = time.time()
        logger.info(f'predicting with {self.__class__} model')
        if isinstance(messages, str):
            prompt_tokens = len(messages) // self.characters_per_token
            reply = self._model.invoke(messages).content
            dt = time.time() - t0
            logger.info(f'predicting {len(reply) + len(messages)} took {dt} s')
        else:
            reply = self._model.invoke(messages).content
            dt = time.time() - t0
            msg_len = sum([len(m.content) for m in messages])
            prompt_tokens = msg_len // self.characters_per_token
            logger.info(f'predicting {len(reply) + msg_len} took {dt} s')
        if track_tokens:
            completion_tokens = len(reply) // self.characters_per_token
            total_tokens = prompt_tokens + completion_tokens
            self.total_tokens_consumed += total_tokens
            self.prompt_tokens_consumed += prompt_tokens
            self.completion_tokens_consumed += completion_tokens
            logger.info(f'total tokens (approx.): {total_tokens}')
            logger.info(f'prompt tokens (approx.): {prompt_tokens}')
            logger.info(f'completion tokens (approx.): {completion_tokens}')
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
            return [self._model.invoke(prompt).content for prompt in prompts]
            
        async def wrap_gather():
            tasks = [self._model.ainvoke(prompt) for prompt in prompts]
            predictions = await asyncio.gather(*tasks)
            return [p.content for p in predictions]
            
        logger.info('predicting multiple using async')
        return loop.run_until_complete(wrap_gather())


class OpenAIModel(BaseModel):

    supports_not_done_yet = True

    def __init__(self, heymans, model):
        from langchain_openai.chat_models import ChatOpenAI
        super().__init__(heymans)
        self._model = ChatOpenAI(
            model=model,
            openai_api_key=config.openai_api_key)
        
    def predict(self, messages):
        with get_openai_callback() as cb:
            retval = super().predict(messages, track_tokens=False)
        logger.info(cb)
        self.total_tokens_consumed += cb.total_tokens
        self.prompt_tokens_consumed += cb.prompt_tokens
        self.completion_tokens_consumed += cb.completion_tokens
        return retval
    
    def predict_multiple(self, prompts):
        with get_openai_callback() as cb:
            retval = super().predict_multiple(prompts)
        logger.info(cb)
        self.total_tokens_consumed += cb.total_tokens
        self.prompt_tokens_consumed += cb.prompt_tokens
        self.completion_tokens_consumed += cb.completion_tokens
        return retval
        
        
class ClaudeModel(BaseModel):
    
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
        
        
class MistralModel(BaseModel):

    def __init__(self, heymans, model):
        from langchain_mistralai.chat_models import ChatMistralAI
        super().__init__(heymans)
        self._model = ChatMistralAI(
            model=model,
            openai_api_key=config.mistral_api_key)
        
    def predict(self, messages):
        if isinstance(messages, list):
            messages = utils.prepare_messages(messages, allow_ai_first=False,
                                              allow_ai_last=False,
                                              merge_consecutive=True)
        return super().predict(messages)
        
        
class DummyModel(BaseModel):
    def predict(self, messages):
        return 'dummy reply'
            
        
def model(heymans, model):
    
    if model == 'gpt-4':
        return OpenAIModel(heymans, 'gpt-4-1106-preview')
    if model == 'gpt-3.5':
        return OpenAIModel(heymans, 'gpt-3.5-turbo-1106')
    if model == 'claude-2.1':
        return ClaudeModel(heymans, 'claude-2.1')
    if model == 'claude-3-opus':
        return ClaudeModel(heymans, 'claude-3-opus-20240229')
    if model == 'claude-3-sonnet':
        return ClaudeModel(heymans, 'claude-3-sonnet-20240229')
    if model.startswith('mistral-'):
        if not model.endswith('-latest'):
            model += '-latest'
        return MistralModel(heymans, model)
    if model == 'dummy':
        return DummyModel(heymans)
    raise ValueError(f'Unknown model: {model}')
