import logging
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
                 tool_choice='auto', strip_thinking_blocks=False):
        self._sigmund = sigmund
        self._model = model
        self._thinking = thinking
        self._tools = tools
        self._tool_choice = tool_choice
        self.json_mode = False
        self._stream_result = None
        self._strip_thinking_blocks = strip_thinking_blocks

    def __repr__(self):
        return f'{self.__class__.__name__}(model={self._model}, thinking={self._thinking})'

    def invalid_tool(self, *args, **kwargs) -> str:
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

    def stream_invoke(self, messages):
        yield self.invoke(messages), True   

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

    def _check_message_length(self, messages):
        """Returns (msg_len, error) where error is None if length is OK."""
        msg_len = self.messages_length(messages)
        if msg_len > config.max_message_length:
            logger.warning(f'message too long: {msg_len}')
            return msg_len, 'Sorry, the message or workspace contains too much text. Can you please shorten it?'
        return msg_len, None

    def predict(self, messages, attachments=None, stream=False):
        if stream:
            return self._stream_predict(messages)
        msg_len, error = self._check_message_length(messages)
        if error:
            return error
        logger.info(f'predicting with {self}')
        reply = self.get_response(self.invoke(messages))
        if self._strip_thinking_blocks:
            reply = self.strip_thinking_blocks(reply)
        return reply

    def _stream_predict(self, messages):
        """Generator that yields (text, complete) chunks during streaming."""
        msg_len, error = self._check_message_length(messages)
        if error:
            yield error, True
            return
        logger.info(f'predicting with {self} (streaming)')
        for reply, complete in self.stream_invoke(messages):
            if complete:
                break
            yield reply, False
        reply = self.get_response(reply)
        if self._strip_thinking_blocks:
            reply = self.strip_thinking_blocks(reply)        
        yield reply, True

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
        
    @classmethod
    def strip_thinking_blocks(cls, content: str) -> str:
        """Removes all thinking blocks from the content string and returns
        the remaining text."""
        return cls._thinking_block_pattern.sub('', content).strip()