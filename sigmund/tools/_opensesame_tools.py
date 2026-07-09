from . import BaseTool
import logging
import json
from ..documentation import Documentation
logger = logging.getLogger('sigmund')

# Corresponds to all item topics in opensesame.json
OPENSESAME_ITEM_TYPES = [
    'inline_script',
    'inline_javascript',
    'loop',
    'logger',
    'sketchpad',
    'feedback',
    'notepad',
    'sequence',
    'mouse_response',
    'keyboard_response',
    'sampler',
    'synth',
    'form_text_input',
    'form_text_display',
    'form_multiple_choice'
]


class BaseOpenSesameTool(BaseTool):
    """Base class for OpenSesame tools that handles common command logic."""

    def __call__(self, **kwargs):
        """Generic call handler that builds command data from arguments."""
        command = self.__class__.__name__.replace('opensesame_', '')
        data = {"command": command}
        data.update(kwargs)
        # We don't ask for feedback directly, because OpenSesame will reply with
        # a user message.
        return None, json.dumps(data, indent=2), 'json', False

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
    """Selects an item in the OpenSesame interface. After selecting an item, you can modify its script. Do not select an item that is already selected in the workspace."""

    arguments = {
        'item_name': {
            'type': 'string',
            'description': 'The name of the item to select.'
        }
    }


class opensesame_update_item_script(BaseOpenSesameTool):
    """Updates an item's script. You should only use this tool to modify the currently selected item. Do not use this tool to update the loop table of a loop item; use opensesame_update_loop_table instead."""

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


class opensesame_update_loop_table(BaseOpenSesameTool):
    """Updates the loop table (i.e. the set of columns and rows) of a loop item. The columns are specified as a dictionary where keys are variable names and values are lists of values, similar to a pandas DataFrame. All columns must have the same length. This replaces the entire loop table; any existing columns that are not included will be removed. The number of cycles is automatically set to the length of the columns. Use this tool instead of opensesame_update_item_script when you want to change the loop table."""

    arguments = {
        'item_name': {
            'type': 'string',
            'description': 'The name of the loop item.'
        },
        'columns': {
            'type': 'object',
            'description': 'A dictionary (DataFrame-like) where keys are column names and values are lists of values. All lists must have the same length. Example: {"cued_size": ["left", "right"], "target_side": ["left", "right"], "valid": [1, 0]}',
            'additionalProperties': {
                'type': 'array',
                'items': {
                    'type': ['string', 'number', 'boolean']
                }
            }
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
    
    
class opensesame_update_run_if_expression(BaseOpenSesameTool):
    """Sets a run-if expression for an item in a sequence. The item is specified based on its position within the sequence."""

    arguments = {
        'parent_sequence_name': {
            'type': 'string',
            'description': 'The name of the parent sequence item.'
        },
        'index': {
            'type': 'number',
            'description': 'The zero-based index of the item to set the run-if expression for.'
        },
        'run_if': {
            'type': 'string',
            'description': 'A Python expression that determines whether the item should be run. Example: "correct == 0"'
        }
    }


class opensesame_get_general_script(BaseOpenSesameTool):
    """Gets the general script for the entire experiment. Use this to get a high-level understanding of the entire experiment."""
    
    arguments = {}


class opensesame_update_general_script(BaseOpenSesameTool):
    """Updates the general script for the entire experiment. Only use this when the user explicitly asks you to build a complete experiment from scratch in one go. Before using this tool, call `opensesame_get_syntax_documentation` to get all reference syntax documents."""

    arguments = {
         'script': {
             'type': 'string',
             'description': 'The new general script for the entire experiment.'
         }
     }


class opensesame_get_syntax_documentation(BaseTool):
    """Gets reference syntax documentation for one or more item types. Call this tool before calling `opensesame_update_general_script`.
    """
    
    arguments = {
        'item_types': {
            'type': 'array',
            'items': {
                'type': 'string',
                'enum': OPENSESAME_ITEM_TYPES
            },
            'description': 'The item types to get syntax documentation for. (default=[all available item types]).'
        }
    }
    required_arguments = []
    
    def __call__(self, item_types=OPENSESAME_ITEM_TYPES):
        documentation = Documentation(self._sigmund,
                                      foundation_document_topics=item_types)
        documentation.search(query=None)
        return None, str(documentation), True
