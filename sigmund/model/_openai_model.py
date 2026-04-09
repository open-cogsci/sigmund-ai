import json
import logging
from types import SimpleNamespace
from .. import config
from . import BaseModel


logger = logging.getLogger('sigmund')


class OpenAIModel(BaseModel):

    def __init__(self, sigmund, model, **kwargs):
        from openai import Client, AsyncClient
        super().__init__(sigmund, model, **kwargs)
        if self._tool_choice not in (None, 'auto'):
            self._tool_choice = {"type": "function",
                                 "function": {"name": self._tool_choice}}
        self._client = Client(api_key=config.openai_api_key)
        self._async_client = AsyncClient(api_key=config.openai_api_key)

    def predict(self, messages, attachments=None, stream=False):
        # Strings need to be converted a list of length one with a single
        # message dict
        if isinstance(messages, str):
            messages = [self.convert_message(messages)]
        else:
            messages = [self.convert_message(message) for message in messages]
            messages = self._prepare_tool_messages(messages)
        # Attachments are included with the last message. The content is now
        # no longer a single str, but a list of dict            
        if attachments:
            logger.info('adding attachments to last message')
            content = [{'type': 'text', 'text': messages[-1]['content']}]
            for attachment in attachments:
                if attachment['type'] == 'image':
                    content.append({
                        'type': 'image_url',
                        'image_url': {'url': attachment['url']}
                        })
                elif attachment['type'] == 'document':
                    content.append({
                        'type': 'file',
                        'file': {
                            'filename': attachment['file_name'],
                            'file_data': attachment['url']
                        }})
            messages[-1]['content'] = content            
        return super().predict(messages, attachments, stream)

    def _tool_call_id(self, nr):
        return f'call_{nr}'

    def _prepare_tool_messages(self, messages):
        # OpenAI requires the tool message to be linked to the previous AI
        # message with a tool_call_id. The actual content doesn't appear to
        # matter, so here we dummy-link the messages
        # The system message cannot have tool_calls information, so in that 
        # case we add a dummy message. 
        if len(messages) > 1 and messages[1]['role'] == 'tool':
            logger.info('insert dummy assistant message before tool')
            messages.insert(1, {'role': 'assistant'})
        # Delete all tool messages that are preceded by user messages. This can
        # happen if the message history has been modified, for example through
        # message deletions. # Tool messages are also not allowed to be first
        clean_messages = []
        for i, message in enumerate(messages):
            if message['role'] != 'tool':
                clean_messages.append(message)
                continue
            if i == 0:
                logger.warning('first message is a tool message')
                continue
            prev_message = messages[i - 1]
            if prev_message['role'] != 'assistant':
                logger.warning('tool message not preceded by assistant message')
                continue
            clean_messages.append(message)
        messages = clean_messages
        # Make sure that tool messages are linked to preceding assistent 
        # messages
        for i, message in enumerate(messages):
            if i == 0 or message['role'] != 'tool':
                continue
            tool_info = json.loads(message['content'])
            tool_call_id = self._tool_call_id(i)
            prev_message = messages[i - 1]
            # an assistant message should not have both content and tool calls
            prev_message['content'] = ''
            prev_message['tool_calls'] = [
                {
                    'id': tool_call_id,
                    'type': 'function',
                    'function': {
                        'name': tool_info['name'],
                        'arguments': tool_info['args']
                    }
                }]
            message['tool_call_id'] = tool_call_id       
            message['name'] = tool_info['name']
            message['content'] = tool_info['content']
            if message['content'] is None:
                message['content'] = ''
        return messages

    def get_response(self, response):
        # Calculate the activity (standardized token use) for this call
        usage = response.usage
        token_rate = config.model_token_rate.get(self._model)
        if usage is None:
            logger.error(f'no usage tracked for model {self._model}')            
        elif token_rate is None:
            logger.error(f'no token rate defined for model {self._model}')
        else:
            cache_read_input_tokens = usage.prompt_tokens_details.cached_tokens
            input_tokens = usage.prompt_tokens - cache_read_input_tokens
            activity = int(input_tokens * token_rate['input'] + \
                usage.completion_tokens * token_rate['output'] + \
                cache_read_input_tokens * token_rate['cache_read_input'])
            cache_use = 100 * cache_read_input_tokens / usage.prompt_tokens
            logger.info(f'activity: {activity} (cache use: {cache_use:.2f}%)')
            if self._sigmund is not None:
                self._sigmund.database.add_activity(activity)   
        # Process response        
        tool_calls = response.choices[0].message.tool_calls
        if tool_calls:
            function = tool_calls[0].function
            if self._tools:
                for tool in self._tools:
                    if tool.name == function.name:
                        return tool.bind(function.arguments)
            logger.warning(f'invalid tool called: {function}')
            return self.invalid_tool
        return response.choices[0].message.content

    def _tool_args(self):
        if not self._tools:
            return {}
        return {'tools': self.tools(), 'tool_choice': self._tool_choice}

    def _openai_kwargs(self):
        """Builds the common kwargs for OpenAI chat completion calls."""
        kwargs = self._tool_args()
        kwargs.update(config.openai_kwargs)
        if self.json_mode:
            kwargs['response_format'] = {"type": "json_object"}
        # Only GPT-5+ currently supports reasoning effort. For GPT-5, the 
        # lowest setting is minimal, for GPT-5.1, it is low. (Or none, but we
        # want at least a little reasoning.)
        if self._model == 'gpt-5':
            kwargs['reasoning_effort'] = \
                'medium' if self._thinking else 'minimal'
        elif self._model == 'gpt-5.1':
            kwargs['reasoning_effort'] = \
                'medium' if self._thinking else 'low'
        return kwargs

    def _openai_invoke(self, fnc, messages):
        return fnc(model=self._model, messages=messages,
                    **self._openai_kwargs())

    def invoke(self, messages):
        return self._openai_invoke(
            self._client.chat.completions.create, messages=messages)
        
    def stream_invoke(self, messages):
        """A generator that returns (response, complete) tuples. During
        streaming complete is False and the responses are text fragments from
        regular text responses. For the final message, complete is True and
        the response is the reconstructed response as would be returned by 
        regular invoke().
        """
        stream = self._client.chat.completions.create(
            model=self._model, messages=messages, stream=True,
            stream_options={"include_usage": True},
            **self._openai_kwargs())
        content_parts = []
        tool_calls_acc = {}
        usage = None
        all_text = ''
        for chunk in stream:
            if chunk.usage is not None:
                usage = chunk.usage
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta
            # Yield text content fragments as they arrive
            if delta.content:
                content_parts.append(delta.content)
                all_text += delta.content
                yield all_text, False
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
        final_content = ''.join(content_parts) if content_parts else None
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

    def async_invoke(self, messages):
        return self._openai_invoke(
            self._async_client.chat.completions.create, messages=messages)
