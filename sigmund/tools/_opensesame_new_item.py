from . import BaseTool
import logging
import json
logger = logging.getLogger('sigmund')


class opensesame_new_item(BaseTool):
    """This tool allows you to create a new item and add it to a parent item, typically a loop or a sequence. After the item has been created you will be able to define its script."""
    
    arguments = {
        'item_name': {
            'type': 'string',
            'description': 'The name of the new item.'
        },
        'item_type': {
            'type': 'string',
            'description': 'The type of the new item.'
        },
        'parent_item_name': {
            'type': 'string',
            'description': 'The name of the parent item.'
        },
        'index': {
            'type': 'number',
            'description': 'The zero-based index of the new item inside the parent item.'
        },        
    }
    required_arguments = ['item_name', 'item_type', 'parent_item_name', 'index']
    
    def __call__(self, item_name, item_type, parent_item_name, index):
        data = {
            "command": "new_item",
            "item_name": item_name,
            "item_type": item_type,
            "parent_item_name": parent_item_name,
            "index": index
        }
        # We don't ask for feedback directly, because OpenSesame will reply
        # with a user message.
        return (f'Using tool: {self.__class__.__name__}',
                json.dumps(data, indent=2), 'json', False)
