from . import BaseTool
import logging
import json
logger = logging.getLogger('sigmund')


class opensesame_remove_item_from_parent(BaseTool):
    """This tool allows you to remove an item from a parent item, typically a loop or a sequence."""
    
    arguments = {
        'parent_item_name': {
            'type': 'string',
            'description': 'The name of the parent item.'
        },
        'index': {
            'type': 'number',
            'description': 'The zero-based index of the to-be-removed item inside the parent item.'
        },       
    }
    required_arguments = ['parent_item_name', 'index']
    
    def __call__(self, parent_item_name, index):
        data = {
            "command": "new_item",
            "parent_item_name": parent_item_name,
            "index": index
        }
        # We don't ask for feedback directly, because OpenSesame will reply
        # with a user message.
        return (f'Using tool: {self.__class__.__name__}',
                json.dumps(data, indent=2), 'json', False)