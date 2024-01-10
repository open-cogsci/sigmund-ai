import logging
import re
import json
from typing import Optional, Tuple
logger = logging.getLogger('heymans')


class BaseTool:
    """A base class for tools that process an AI reply."""
    
    # A JSON patter to match tool instructions. Should contain named groups, 
    # which are passed to use() as named arguments
    json_pattern = None
    # A prompt section that is automatically included in the system prompt 
    # when specified.
    prompt = None
    
    def __init__(self, heymans):
        self.json_pattern = re.compile(self.json_pattern,
                                       re.VERBOSE | re.DOTALL)
        self._heymans = heymans
        
    def use(self, message: str) -> Tuple[Optional[str], bool]:
        """Should be implemented in a tool with additional arguments that
        match the names of the fields from the json_pattern. 
        """
        raise NotImplementedError()
    
    def run(self, message: str) -> Tuple[str, list, bool]:
        """Takes a message and uses the tool if the messages contains relevant
        JSON instructions. Returns the updated message, which can be changed by
        the tool notably by string the tool JSON instructions, a list of result
        strings, and a boolean indicating whether the model should reply to the
        result.
        
        Since there can be multiple instructions for one tool in a single
        message, the result is a list, rather than a single string.
        """
        spans = []
        results = []
        needs_reply = []
        for match in self.json_pattern.finditer(message):
            logger.info(f'executing tool {self}')
            args = {self.as_json_value(key) : self.as_json_value(val)
                    for key, val in match.groupdict().items()}
            match_result, match_needs_reply = self.use(message, **args)
            if match_result is not None:
                results.append(match_result)
            needs_reply.append(match_needs_reply)
            spans.append((match.start(), match.end()))
        # We now loop through all spans that correspond to JSON code blocks.
        # We find the first preceding { and succeeding } because the matching
        # only occurs within a block, and then we remove this. The goal of this
        # is to strip the JSON blocks from the reply.
        if spans:
            for span in spans[::-1]:
                for start in range(span[0], -1, -1):
                    ch = message[start]
                    if ch == '{':
                        break
                    if start is not span[0] and not ch.isspace() and ch != '"':
                        start = None
                        break
                for end in range(span[1], len(message) + 1):
                    ch = message[end]
                    if ch == '}':
                        break
                    if not ch.isspace() and ch != '"':
                        start = None
                        break
                if start is not None and end is not None:
                    message = message[:start] + message[end + 1:]
            # Remove empty JSON code blocks in case the JSON was embedded in
            # blocks
            message = re.sub(r'```json\s*```', '', message).strip()
            if not message:
                message = f'Running `{self.__class__.__name__}` … <TRANSIENT>'''
        return message, results, any(needs_reply)
        
    def as_json_value(self, s):
        try:
            return json.loads(s)
        except json.JSONDecodeError:
            return json.loads(f'"{s}"')
