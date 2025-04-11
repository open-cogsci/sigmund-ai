import logging
import tempfile
import base64
import os
from .. import config, utils
from . import BaseModel
from ._openai_model import OpenAIModel
logger = logging.getLogger('sigmund')


class MistralModel(OpenAIModel):
    
    supports_not_done_yet = False

    def __init__(self, sigmund, model, **kwargs):
        from mistralai import Mistral
        BaseModel.__init__(self, sigmund, **kwargs)
        self._model = model
        self._actual_model = self._model
        # Mistral doesn't allow a tool to be specified by name. So if this
        # happens, we instead use the 'any' option, which forces use of the
        # best fitting tool, which in the case of a single tool boils down to
        # the same thing as forcing the tool by name.
        if self._tool_choice not in [None, 'none', 'auto', 'any']:
            self._tool_choice = 'any'
        self._client = Mistral(api_key=config.mistral_api_key)
        
    def predict(self, messages, attachments=None, track_tokens=True):
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
        # Attachments are included with the last message. The content is now
        # no longer a single str, but a list of dict
        self._actual_model = self._model
        if attachments:
            logger.info('adding attachments to last message')
            content = [{'type': 'text', 'text': messages[-1]['content']}]
            for attachment in attachments:
                # Decompose the HTML-style data into a mimetype and the 
                # actual data
                url = attachment['url']
                data = url[url.find(',') + 1:]                
                if attachment['type'] == 'image':
                    # Vision requires a special model (pixtral). This model also
                    # understands text and documents, so whenever there is a 
                    # single attachment, we switch to using this model.
                    self._actual_model = \
                        config.model_config['mistral']['vision_model']
                    content.append({'type': 'image_url',
                                    'image_url': attachment['url']})
                elif attachment['type'] == 'document':
                    # Documents have to be uploaded first, and then provided as
                    # a url
                    tmp_file = tempfile.NamedTemporaryFile(delete=False)
                    tmp_file.write(base64.b64decode(data))
                    tmp_file.close()
                    uploaded_pdf = self._client.files.upload(
                        file={
                            "file_name": attachment['file_name'],
                            "content": open(tmp_file.name, 'rb'),
                        },
                        purpose="ocr"
                    )
                    os.remove(tmp_file.name)
                    signed_url = self._client.files.get_signed_url(file_id=uploaded_pdf.id)
                    content.append({'type': 'document_url',
                                    'document_url': signed_url.url})
            messages[-1]['content'] = content
        return BaseModel.predict(self, messages, attachments, track_tokens)
        
    def _tool_call_id(self, nr):
        # Must be a-z, A-Z, 0-9, with a length of 9
        return f'{nr:09d}'
        
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
        return fnc(model=self._actual_model, messages=messages, **kwargs)
    
    def invoke(self, messages):
        return self._mistral_invoke(self._client.chat.complete, messages)
        
    def async_invoke(self, messages, attachments=None):
        return self._mistral_invoke(self._client.chat.complete_async, messages)
