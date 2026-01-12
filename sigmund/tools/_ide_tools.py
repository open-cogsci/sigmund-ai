from . import BaseTool
import logging
import json
logger = logging.getLogger('sigmund')


class BaseIDETool(BaseTool):
    """Base class for IDE tools that handles common command logic."""

    def __call__(self, **kwargs):
        """Generic call handler that builds command data from arguments."""
        command = self.__class__.__name__.replace('ide_', '')
        data = {"command": command}
        data.update(kwargs)
        # We don't ask for feedback directly, because OpenSesame will reply with
        # a user message.
        return ('(Suggesting IDE action)', json.dumps(data, indent=2),
                'json', False)

    @property
    def required_arguments(self):
        """Automatically derive required arguments from arguments dict."""
        return list(self.arguments.keys())


class ide_open_file(BaseIDETool):
    """Opens a file in the editor."""

    arguments = {
        'path': {
            'type': 'string',
            'description': 'The file path.'
        }
    }


class ide_execute_code(BaseIDETool):
    """Executes code in the editor. This code is executed locally on the user's system.'"""

    arguments = {
        'code': {
            'type': 'string',
            'description': 'The code to execute.'
        },
        'language': {
            'typ': 'string',
            'description': 'The programming language of the code.'
        }
    }
