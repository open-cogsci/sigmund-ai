from . import BaseTool
import logging
import json
logger = logging.getLogger('sigmund')


class opensesame_update_item_script(BaseTool):
    """Updates an item's script. You should only run this tool to modify the currently selected item."""
    
    arguments = {
        'item_name': {
            'type': 'string',
            'description': 'The name of the item.'
        },
        'script': {
            'type': 'string',
            'description': 'The updated item script.'
        }
    }
    required_arguments = ['item_name', 'script']
    
    def __call__(self, item_name, script):
        data = {
            "command": "update_item_script",
            "item_name": item_name,
            "script": script
        }
        # We don't ask for feedback directly, because OpenSesame will reply
        # with a user message.
        return ('(Suggesting OpenSesame action)',
                json.dumps(data, indent=2), 'json', False)
