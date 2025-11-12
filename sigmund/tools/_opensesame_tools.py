from . import BaseTool
import logging
import json
logger = logging.getLogger('sigmund')


class BaseOpenSesameTool(BaseTool):
    """Base class for OpenSesame tools that handles common command logic."""

    def __call__(self, **kwargs):
        """Generic call handler that builds command data from arguments."""
        command = self.__class__.__name__.replace('opensesame_', '')
        data = {"command": command}
        data.update(kwargs)
        # We don't ask for feedback directly, because OpenSesame will reply with
        # a user message.
        return ('(Suggesting OpenSesame action)', json.dumps(data, indent=2),
                'json', False)

    @property
    def required_arguments(self):
        """Automatically derive required arguments from arguments dict."""
        return list(self.arguments.keys())


class opensesame_add_existing_item_to_parent(BaseOpenSesameTool):
    """Adds an existing item to a parent item, which is typically a loop or a sequence. This creates a linked copy of the item."""

    arguments = {
        'item_name': {
            'type': 'string',
            'description': 'The name of the existing item to add.'
        },
        'parent_item_name': {
            'type': 'string',
            'description': 'The name of the parent item.'
        },
        'index': {
            'type': 'number',
            'description': 'The zero-based index where the item should be inserted in the parent.'
        }
    }


class opensesame_new_item(BaseOpenSesameTool):
    """Creates a new item and adds it to a parent item, which is typically a loop or a sequence. After the item has been created you will be able to define its script."""

    arguments = {
        'item_name': {
            'type': 'string',
            'description': 'The name of the new item to create.'
        },
        'item_type': {
            'type': 'string',
            'description': 'The type of the new item (e.g., "sketchpad", "keyboard_response", "inline_script").'
        },
        'parent_item_name': {
            'type': 'string',
            'description': 'The name of the parent item.'
        },
        'index': {
            'type': 'number',
            'description': 'The zero-based index where the item should be inserted in the parent.'
        }
    }


class opensesame_remove_item_from_parent(BaseOpenSesameTool):
    """Removes an item from a parent item, which is typically a loop or a sequence."""

    arguments = {
        'parent_item_name': {
            'type': 'string',
            'description': 'The name of the parent item.'
        },
        'index': {
            'type': 'number',
            'description': 'The zero-based index of the item to remove from the parent.'
        },       
    }


class opensesame_rename_item(BaseOpenSesameTool):
    """Renames an item in the experiment."""

    arguments = {
        'from_item_name': {
            'type': 'string',
            'description': 'The current name of the item.'
        },
        'to_item_name': {
            'type': 'string',
            'description': 'The new name for the item.'
        }
    }


class opensesame_select_item(BaseOpenSesameTool):
    """Selects an item in the OpenSesame interface. After selecting an item, you can modify its script."""

    arguments = {
        'item_name': {
            'type': 'string',
            'description': 'The name of the item to select.'
        }
    }


class opensesame_update_item_script(BaseOpenSesameTool):
    """Updates an item's script. You should only use this tool to modify the currently selected item."""

    arguments = {
        'item_name': {
            'type': 'string',
            'description': 'The name of the item (should be the currently selected item).'
        },
        'script': {
            'type': 'string',
            'description': 'The complete updated script for the item.'
        }
    }


class opensesame_set_global_var(BaseOpenSesameTool):
    """Sets a global experiment variable that can be accessed throughout the experiment."""

    arguments = {
        'var_name': {
            'type': 'string',
            'description': 'The name of the global variable.'
        },
        'value': {
            'type': ['string', 'number'],
            'description': 'The value to assign to the variable.'
        }
    }