from . import BaseTool
import logging
import json
logger = logging.getLogger('sigmund')


class opensesame_select_item(BaseTool):
    """Selects an item. After the item has been selected, you will be able to modify its script."""
    
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
        return ('(Suggesting OpenSesame action)',
                json.dumps(data, indent=2), 'json', False)