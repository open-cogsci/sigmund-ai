import logging
import asyncio
import time
import re
from .. import config
logger = logging.getLogger('sigmund')


class BaseModel:
    """Base implementation for LLM chat models."""

    # Indicates whether the model is able to provide feedback on its own output
    supports_not_done_yet = False
    # Indicates whether the model is able to provide feedback on tool results 
    supports_tool_feedback = True
    # Approximation to keep track of token costs
    characters_per_token = 4    
    # Regex that matches a single thinking block (signature div followed by
    # content div). Used by extract_thinking_blocks.
    _thinking_block_pattern = re.compile(
        r'<div\s+class="thinking_block_signature">(.*?)</div>\s*'
        r'<div\s+class="thinking_block_content">(.*?)</div>',
        re.DOTALL
    )    

    def __init__(self, sigmund, model, thinking=False, tools=None,
                 tool_choice='auto'):
        self._sigmund = sigmund
        self._model = model
        self._thinking = thinking
        self._tools = tools
        self._tool_choice = tool_choice
        self.total_tokens_consumed = 0
        self.prompt_tokens_consumed = 0
        self.completion_tokens_consumed = 0
        self.json_mode = False

    def __repr__(self):
        return f'{self.__class__.__name__}(model={self._model}, thinking={self._thinking})'

    def invalid_tool(self) -> str:
        return 'Invalid tool', None, 'markdown', False

    def get_response(self, response) -> [str, callable]:
        return response.content

    def tools(self):
        if self._tools is None:
            return []
        return [{"type": "function", "function": t.tool_spec}
                for t in self._tools if t.tool_spec]

    def invoke(self, messages, attachments=None):
        raise NotImplementedError()

    def async_invoke(self, messages, attachments=None):
        raise NotImplementedError()

    def messages_length(self, messages) -> int:
        if isinstance(messages, str):
            return len(messages)
        return sum([len(m.content if hasattr(m, 'content') else m['content'])
                   for m in messages])

    def convert_message(self, message):
        if isinstance(message, str):
            return dict(role='user', content=message)
        if isinstance(message, dict):
            return message
        raise ValueError(f'Unknown message type: {message}')

    def predict(self, messages, attachments=None, track_tokens=True):
        t0 = time.time()
        msg_len = self.messages_length(messages)
        if msg_len > config.max_message_length:
            logger.warning(f'message too long: {msg_len}')
            return 'Sorry, the message or workspace contains too much text. Can you please shorten it?'
        logger.info(f'predicting with {self}')
        reply = self.get_response(self.invoke(messages))
        dt = time.time() - t0
        prompt_tokens = msg_len // self.characters_per_token
        reply_len = len(reply) if isinstance(reply, str) else 0
        logger.info(f'predicting {reply_len + msg_len} took {dt} s')
        if track_tokens:
            completion_tokens = reply_len // self.characters_per_token
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
        prompts = [[self.convert_message(prompt)] for prompt in prompts]
        try:
            loop = asyncio.get_event_loop()
            if not loop.is_running():
                logger.info('re-using async event loop')
                use_async = True
            else:
                logger.info('async event loop is already running')
                use_async = False
        except RuntimeError:
            logger.info('creating async event loop')
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            use_async = True

        if not use_async:
            logger.info('predicting multiple without async')
            return [self.get_response(self.invoke(prompt))
                                              for prompt in prompts]

        async def wrap_gather():
            tasks = [self.async_invoke(prompt) for prompt in prompts]
            try:
                predictions = await asyncio.gather(*tasks)
            except Exception as e:
                logger.warning(f'failed to gather predictions: {e}')
                return []
            return [self.get_response(p) for p in predictions]

        logger.info('predicting multiple using async')
        return loop.run_until_complete(wrap_gather())

    @staticmethod
    def embed_thinking_block(signature: str | None,
                             content: str | None) -> str:
        """Embeds a single thinking block as HTML divs."""
        sig = (f'<div class="thinking_block_signature">{signature}</div>'
               if signature else "")
        cont = (f'<div class="thinking_block_content">{content}</div>'
                if content else "")
        return sig + cont

    @classmethod
    def extract_thinking_blocks(cls, content: str) -> list | None:
        """Extracts all thinking blocks and surrounding text from flat HTML
        content and returns them as a list of Anthropic-style content block
        dicts, preserving the original interleaved order.

        Returns a list of dicts, each either:
          {'type': 'thinking', 'thinking': str, 'signature': str}
          {'type': 'text', 'text': str}

        If no thinking blocks are found, returns ``None`` to signal that no
        transformation is needed.
        """
        matches = list(cls._thinking_block_pattern.finditer(content))
        if not matches:
            return None
        blocks = []
        last_end = 0
        for match in matches:
            # Text segment preceding this thinking block
            text_before = content[last_end:match.start()].strip()
            if text_before:
                blocks.append({'type': 'text', 'text': text_before})
            blocks.append({
                'type': 'thinking',
                'thinking': match.group(2),
                'signature': match.group(1),
            })
            last_end = match.end()
        # Text segment after the last thinking block
        text_after = content[last_end:].strip()
        if text_after:
            blocks.append({'type': 'text', 'text': text_after})
        # The Anthropic API does not allow empty text blocks, so filter them
        # out.  If no text block remains at all, add a filler.
        blocks = [b for b in blocks
                  if b['type'] != 'text' or b['text'].strip()]
        if not any(b['type'] == 'text' for b in blocks):
            blocks.append({
                'type': 'text',
                'text': 'I added content to the workspace.'
            })
        return blocks