from zai import ZaiClient
from ._openai_model import OpenAIModel
from .. import config
import logging

logger = logging.getLogger('sigmund')

BASE_URL = "https://api.z.ai/api/paas/v4/"

class ZModel(OpenAIModel):


    def __init__(self, sigmund, model, **kwargs):
        from openai import Client, AsyncClient
        super().__init__(sigmund, model, **kwargs)
        if self._tool_choice not in (None, 'auto'):
            self._tool_choice = {"type": "function",
                                 "function": {"name": self._tool_choice}}
        self._client = Client(api_key=config.z_api_key, base_url=BASE_URL)
        self._async_client = AsyncClient(api_key=config.z_api_key,
                                         base_url=BASE_URL)
        self._z_client = ZaiClient(api_key=config.z_api_key)
        self._default_model = model
        self._vision_model = config.model_config['z']['vision_model']
        
    def predict(self, messages, attachments=None, stream=False):
        # We need to convert all document attachments to text, because the z-api
        # doesn't appear to accept them. It does accept image attachments though
        # so we just pass these on. However, in this case we do need to switch
        # to a vision-capable model, because the default GLM models only process
        # text.
        self._model = self._default_model
        image_attachments = []
        if attachments:
            text_attachments = {}
            for attachment in attachments:
                if attachment['type'] == 'image':
                    image_attachments.append(attachment)
                    self._model = self._vision_model
                    logger.info(f'switching to vision model: {self._model}')
                elif attachment['type'] == 'document':
                    logger.info(f'converting {attachment["file_name"]} to text')
                    response = self._z_client.layout_parsing.create(
                        model="glm-ocr",
                        file=attachment['url']
                    )
                    text_content = response.model_dump()['md_results']
                    text_attachments[attachment['file_name']] = text_content
            # The text attachments are inserted as XML elements into the last
            # message
            for file_name, text_content in text_attachments.items():
                messages[-1]['content'] += f'\n<document filename="{file_name}">\n{text_content}\n</document>'            
        return super().predict(messages, image_attachments, stream)

    def _openai_kwargs(self):
        """Builds the common kwargs for OpenAI chat completion calls."""
        kwargs = super()._openai_kwargs()
        if self._thinking:
            kwargs['extra_body'] = {
                'thinking': {
                    'type': 'enabled'
                },
                'reasoning_effort': 'max'
            }
        else:
            kwargs['extra_body'] = {
                'thinking': {
                    'type': 'disabled'
                }
            }
        return kwargs
