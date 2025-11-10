from . import BaseTool
import logging
import json
logger = logging.getLogger('sigmund')


class opensesame_remove_item_from_parent(BaseTool):
    """Removes an item from a parent item, typically a loop or a sequence."""
    
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
            "command": "remove_item_from_parent",
            "parent_item_name": parent_item_name,
            "index": index
        }
        # We don't ask for feedback directly, because OpenSesame will reply
        # with a user message.
        return ('(Suggesting OpenSesame action)',
                json.dumps(data, indent=2), 'json', False)