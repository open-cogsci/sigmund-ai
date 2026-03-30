import logging
import tempfile
import base64
import os
from types import SimpleNamespace
from .. import config, utils
from . import BaseModel
from ._openai_model import OpenAIModel
logger = logging.getLogger('sigmund')


class MistralModel(OpenAIModel):

    supports_not_done_yet = False

    def __init__(self, sigmund, model, **kwargs):
        from mistralai.client import Mistral
        BaseModel.__init__(self, sigmund, model, **kwargs)
        self._actual_model = self._model
        # Mistral doesn't allow a tool to be specified by name. So if this
        # happens, we instead use the 'any' option, which forces use of the
        # best fitting tool, which in the case of a single tool boils down to
        # the same thing as forcing the tool by name.
        if self._tool_choice not in [None, 'none', 'auto', 'any']:
            self._tool_choice = 'any'
        self._client = Mistral(api_key=config.mistral_api_key)

    def predict(self, messages, attachments=None, stream=False):
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
        return BaseModel.predict(self, messages, attachments, stream)

    def get_response(self, response) -> [str, callable]:
        # Calculate the activity (standardized token use) for this call
        usage = response.usage
        token_rate = config.model_token_rate.get(self._model)
        if token_rate is None:
            logger.error(f'no token rate defined for model {self._model}')
        else:
            activity = int(usage.prompt_tokens * token_rate['input'] + \
                usage.completion_tokens * token_rate['output'])
            logger.info(f'activity: {activity}')
            self._sigmund.database.add_activity(activity)           
        content = response.choices[0].message.content
        tool_message_prefix = ''
        # During thinking, content consists of a mix of text and thinking 
        # blocks, where thinking blocks themselves consist of chunks of text.
        # For now, we simply concatenate everything into a single large 
        # response. This is because there may be multiple thinking and text 
        # blocks mixed in a single response, see also:
        # - <https://github.com/mistralai/client-python/issues/252>
        if isinstance(content, list):
            text = []
            tool_message_prefix = ''
            for block in content:
                if block.type == 'text':
                    text.append(block.text)
                    tool_message_prefix += block.text
                if block.type == 'thinking':
                    for thinking_chunk in block.thinking:
                        text.append(thinking_chunk.text)
                        tool_message_prefix += thinking_chunk.text
            content = '\n'.join(text)
        # If tool calls are present, we execute the tool using the current text
        # as a prefix.
        tool_calls = response.choices[0].message.tool_calls
        if tool_calls:
            function = tool_calls[0].function
            if self._tools:
                for tool in self._tools:
                    if tool.name == function.name:
                        return tool.bind(function.arguments,
                                         message_prefix=tool_message_prefix + '\n\n')
            logger.warning(f'invalid tool called: {function}')
            return self.invalid_tool            
        return content

    def _tool_call_id(self, nr):
        # Must be a-z, A-Z, 0-9, with a length of 9
        return f'{nr:09d}'

    def _invoke_kwargs(self, messages):
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
        return kwargs

    def _mistral_invoke(self, fnc, messages):
        return fnc(model=self._actual_model, messages=messages,
                   **self._invoke_kwargs(messages))

    def invoke(self, messages):
        return self._mistral_invoke(self._client.chat.complete, messages)     

    def stream_invoke(self, messages):
        """A generator that returns (response, complete) tuples. During
        streaming complete is False and the responses are text fragments from
        regular text responses. For the final message, complete is True and
        the response is the reconstructed response as would be returned by 
        regular invoke().
        """
        stream = self._client.chat.stream(
            model=self._actual_model, messages=messages,
            **self._invoke_kwargs(messages))
        # Content items are (type, data) tuples where type is 'text' or
        # 'thinking'. For text, data is a string fragment. For thinking,
        # data is a list of thinking-chunk objects (with .text attributes).
        content_items = []
        has_list_content = False
        tool_calls_acc = {}
        usage = None
        all_text = ''
        for event in stream:
            chunk = event.data
            if chunk.usage is not None:
                usage = chunk.usage
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta
            # Content can be a plain string or a list of typed blocks
            # (text / thinking) when the model uses extended thinking.
            if delta.content:
                if isinstance(delta.content, str):
                    content_items.append(('text', delta.content))
                    all_text += delta.content
                    yield all_text, False
                elif isinstance(delta.content, list):
                    has_list_content = True
                    for item in delta.content:
                        if item.type == 'text' and item.text:
                            content_items.append(('text', item.text))
                            all_text += item.text
                            yield all_text, False
                        elif item.type == 'thinking':
                            content_items.append(
                                ('thinking', item.thinking or []))
            # Accumulate streamed tool call fragments
            if delta.tool_calls:
                for tc in delta.tool_calls:
                    idx = tc.index
                    if idx not in tool_calls_acc:
                        tool_calls_acc[idx] = SimpleNamespace(
                            id=tc.id or '',
                            type=tc.type or 'function',
                            function=SimpleNamespace(
                                name='', arguments=''))
                    acc = tool_calls_acc[idx]
                    if tc.id:
                        acc.id = tc.id
                    if tc.type:
                        acc.type = tc.type
                    if tc.function:
                        if tc.function.name:
                            acc.function.name = tc.function.name
                        if tc.function.arguments:
                            acc.function.arguments += tc.function.arguments
        # Reconstruct the final response to match the structure returned by
        # invoke(), so that get_response() works on it.
        if not content_items:
            final_content = None
        elif not has_list_content:
            # Simple string content (no thinking blocks)
            final_content = ''.join(data for _, data in content_items)
        else:
            # Merge adjacent blocks of the same type into a compact list of
            # SimpleNamespace objects compatible with get_response().
            merged = []
            for item_type, item_data in content_items:
                if merged and merged[-1][0] == item_type:
                    if item_type == 'text':
                        merged[-1] = ('text', merged[-1][1] + item_data)
                    else:
                        merged[-1] = ('thinking',
                                      merged[-1][1] + item_data)
                else:
                    merged.append((item_type, item_data))
            final_content = []
            for block_type, block_data in merged:
                if block_type == 'text':
                    final_content.append(
                        SimpleNamespace(type='text', text=block_data))
                else:
                    final_content.append(
                        SimpleNamespace(type='thinking',
                                        thinking=block_data))
        final_tool_calls = (
            [tool_calls_acc[i] for i in sorted(tool_calls_acc)]
            if tool_calls_acc else None
        )
        message = SimpleNamespace(
            content=final_content,
            tool_calls=final_tool_calls,
            role='assistant')
        choice = SimpleNamespace(message=message)
        response = SimpleNamespace(choices=[choice], usage=usage)
        yield response, True

    def async_invoke(self, messages, attachments=None):
        return self._mistral_invoke(self._client.chat.complete_async, messages)