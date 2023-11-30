import openai
from langchain.chat_models import ChatOpenAI
from . import config
import re
import json
import logging
logger = logging.getLogger('heymans')


class Model:
    
    def __init__(self, heymans, model=None):
        self._heymans = heymans
        if model is None:
            self._model = config.model
        else:
            self._model = model

    def predict(self, messages):
        if isinstance(messages, str):
            return ChatOpenAI(
                model=self._model,
                openai_api_key=config.openai_api_key).predict(messages)
        openai.api_key = config.openai_api_key
        response = openai.ChatCompletion.create(
            model=self._model, messages=messages)
        reply = response.choices[0].message['content']
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
