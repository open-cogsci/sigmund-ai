from . import BaseTool
import logging
import json
logger = logging.getLogger('sigmund')


class opensesame_add_existing_item_to_parent(BaseTool):
    """This tool allows you to add an existing item to a parent item, typically a loop or a sequence. This creates a linked copy of the item. After the item has been added you will be able to define its script."""
    
    arguments = {
        'item_name': {
            'type': 'string',
            'description': 'The name of the existing item.'
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
    required_arguments = ['item_name', 'parent_item_name', 'index']
    
    def __call__(self, item_name, parent_item_name, index):
        data = {
            "command": "add_existing_item_to_parent",
            "item_name": item_name,
            "parent_item_name": parent_item_name,
            "index": index
        }
        # We don't ask for feedback directly, because OpenSesame will reply
        # with a user message.
        return (f'Using tool: {self.__class__.__name__}',
                json.dumps(data, indent=2), 'json', False)
