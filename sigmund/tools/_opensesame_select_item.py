from . import BaseTool
import logging
import json
logger = logging.getLogger('sigmund')


class opensesame_select_item(BaseTool):
    """This tool allows you to select an item in the OpenSesame user interface. """
    
    arguments = {
        'item_name': {
            'type': 'string',
            'description': 'The name of the item to select.'
        }
    }
    required_arguments = ['item_name']
    
    def __call__(self, item_name):
        data = {
            "command": "select_item",
            "item_name": item_name
        }
        # We don't ask for feedback directly, because OpenSesame will reply
        # with a user message.
        return (f'Using tool: {self.__class__.__name__}',
                json.dumps(data, indent=2), 'json', False)