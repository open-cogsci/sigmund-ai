import json
from . import BaseTool


class multiple_tools(BaseTool):
    """This tool should not be called directly. Rather, it is automatically
    created as a wrapper when multiple tool calls are included in a single
    message.
    """
    
    arguments = {}
    required_arguments = []
    
    def __init__(self, sigmund):
        self._tools = []
        self.suffix = None
        super().__init__(sigmund)
    
    def set_tools(self, tools):
        """Adds a bound tool functions as returned by BaseTool.bind(). These
        should be called with attachments as a single argument.
        """
        self._tools = tools
        
    def __call__(self):
        chain_message = []
        chain_result = []
        chain_needs_feedback = False
        chain_language = None        
        for tool in self._tools:
            message, result, language, needs_feedback = tool(self._attachments)
            chain_message.append(message)
            chain_result.append(result)
            chain_needs_feedback = chain_needs_feedback or needs_feedback
            chain_language = language
        if self.suffix is not None:
            chain_message.append(self.suffix)
        results = {
            "command": "multiple_tools",
            "tools": chain_result
        }
        message = 'Multiple tools were called. These were wrapped automatically into a single `multiple_tool()` chain by the message postprocessor. This is expected behavior.\n\n' + '\n'.join(chain_message)
        return message, json.dumps(results), chain_language, chain_needs_feedback

    def __len__(self):
        return len(self._tools)
