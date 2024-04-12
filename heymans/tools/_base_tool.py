import logging
# import re
import json
import functools
from typing import Optional, Tuple
logger = logging.getLogger('heymans')


class BaseTool:
    """A base class for tools that process an AI reply."""
    
    tool_spec = None
    
    def __init__(self, heymans):
        self._heymans = heymans
        
    @property
    def tool_spec(self):
        return {
            "name": self.__class__.__name__,
            "description": self.__doc__,
            "parameters": {
                "type": "object",
                "properties": self.arguments,
                "required": self.required_arguments,
            }
        }
        
    @property
    def name(self):
        return self.__class__.__name__
    
    def bind(self, args):
        if isinstance(args, str):
            args = json.loads(args)
        return functools.partial(self, **args)
        
    def __call__(self) -> Tuple[str, Optional[str], bool]:
        """Should be implemented in a tool with additional arguments that
        match tool specification.
        """
        raise NotImplementedError()
