from . import BaseTool
import logging
import json
logger = logging.getLogger('sigmund')


class opensesame_rename_item(BaseTool):
    """This tool allows you to select an item in the OpenSesame user interface. """
    
    arguments = {
        'from_item_name': {
            'type': 'string',
            'description': 'The current name of the item to rename.'
        },
        'to_item_name': {
            'type': 'string',
            'description': 'The target name of the item to rename.'
        }
    }
    required_arguments = ['from_item_name', 'to_item_name']
    
    def __call__(self, from_item_name, to_item_name):
        data = {
            "command": "rename_item",
            "from_item_name": from_item_name,
            "to_item_name": to_item_name
        }
        # We don't ask for feedback directly, because OpenSesame will reply
        # with a user message.
        return (f'Using tool: {self.__class__.__name__}',
                json.dumps(data, indent=2), 'json', False)
