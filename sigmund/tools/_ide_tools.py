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
    """Opens a file in the editor so you and the user can view and edit it. Use this tool when either you or the user wants to edit or modify a file. If you only need to see the contents of a file, use `ide_inspect_files` instead."""

    arguments = {
        'path': {
            'type': 'string',
            'description': 'The path to the file to open in the editor.'
        }
    }
    required_arguments = ["path"]


class ide_inspect_files(BaseIDETool):
    """Reads and returns the contents of one or more files so you can examine them. Use this tool when you need to read file contents yourself, without opening them in the editor. If you or the user wants to edit a file, use `ide_open_file` instead."""

    arguments = {
        'paths': {
            'type': 'array',
            'items': {'type': 'string'},
            'description': 'A list of file paths whose contents should be read and returned.'
        },
        'encoding': {
            'type': 'string',
            'description': 'The text encoding to use when reading the files. (default="utf-8")'
        }
    }
    required_arguments = ["paths"]


class ide_execute_code(BaseIDETool):
    """Executes code on the user's local system and returns the output. Use this tool to run code, test a snippet, or perform a computation on behalf of the user."""

    arguments = {
        'code': {
            'type': 'string',
            'description': 'The code to execute.'
        },
        'language': {
            'type': 'string',
            'description': 'The programming language of the code, e.g. "python" or "r". (default="python")'
        }
    }
    required_arguments = ["code"]


class ide_list_files(BaseIDETool):
    """Lists the files and folders inside a directory on the user's local system and returns the result. Use this tool to explore the directory structure before inspecting or opening specific files."""

    arguments = {
        'path': {
            'type': 'string',
            'description': 'The path to the directory to list.'
        },
        'recursive': {
            'type': 'boolean',
            'description': 'If true, list files recursively in all subdirectories. (default=false)'
        },
        'max_files': {
            'type': 'integer',
            'description': 'The maximum number of files to return. (default=250)'
        }
    }
    required_arguments = ["path"]
