import json
from . import BaseTool
import logging
logger = logging.getLogger('sigmund')

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
        is_command = False
        for tool in self._tools:
            message, result, language, needs_feedback = tool(self._attachments)
            chain_message.append(message)
            chain_result.append(result)
            # When a tool result is a command, this means that we should not
            # request feedback. In this case, the command first goes to the app
            # and through this route, we request feedback. A command is embedded
            # as a JSON encoded str in the command field of the content.
            content = result.get('content')
            if isinstance(content, str):
                try:
                    content = json.loads(content)
                    if isinstance(content, dict) and content.get('command'):
                        logger.info('Command detected in multiple_tools chain')
                        is_command = True
                except json.JSONDecodeError:
                    pass
            chain_needs_feedback = chain_needs_feedback or needs_feedback
            chain_language = language
        if self.suffix is not None:
            chain_message.append(self.suffix)
        results = {
            "command": "multiple_tools",
            "tools": chain_result
        }
        message = 'Multiple tools were called. These were wrapped automatically into a single `multiple_tool()` chain by the message postprocessor. This is expected behavior.\n\n' + '\n'.join(chain_message)
        return (message, json.dumps(results), chain_language,
                chain_needs_feedback and not is_command)

    def __len__(self):
        return len(self._tools)
