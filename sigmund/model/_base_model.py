import logging
import asyncio
import time
import re
logger = logging.getLogger('sigmund')


class BaseModel:
    """Base implementation for LLM chat models."""
    
    # Indicates whether the model is able to provide feedback on its own output
    supports_not_done_yet = False
    # Indicates whether the model is able to provide feedback on tool results 
    supports_tool_feedback = True
    # Approximation to keep track of token costs
    characters_per_token = 4
    
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
        logger.info(f'predicting with {self.__class__} model')
        reply = self.get_response(self.invoke(messages))
        msg_len = self.messages_length(messages)
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
    def embed_thinking_block(signature: str | None, content: str | None) -> str:
        """Embeds information about an Anthropic thinking block as an HTML element."""
        sig = f'<div class="thinking_block_signature">{signature}</div>' if signature else ""
        cont = f'<div class="thinking_block_content">{content}</div>' if content else ""
        return sig + cont
    
    @staticmethod
    def extract_thinking_block(content: str) -> [str, str | None, str | None]:
        """
        Extracts signature/content spans if present and returns a tuple:
          (cleaned_content, signature, content)
        """
        sig_pattern = r'<div\s+class="thinking_block_signature">(.*?)</div>'
        cont_pattern = r'<div\s+class="thinking_block_content">(.*?)</div>'
        signature = None
        thinking_content = None
    
        sig_match = re.search(sig_pattern, content)
        if sig_match:
            signature = sig_match.group(1)
            content = re.sub(sig_pattern, '', content, count=1)
    
        cont_match = re.search(cont_pattern, content, re.MULTILINE | re.DOTALL)
        if cont_match:
            thinking_content = cont_match.group(1)
            content = re.sub(cont_pattern, '', content, count=1,
                             flags=re.MULTILINE | re.DOTALL)
    
        cleaned = content.strip()
        if signature or thinking_content:
            return cleaned, signature, thinking_content
        return content, None, None