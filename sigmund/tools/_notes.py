from . import BaseTool
from .. import config, prompt
import logging

logger = logging.getLogger('sigmund')


class add_note(BaseTool):
    """Stores a note that persists throughout the conversation. Use this for
    information that you need to remember."""

    arguments = {
        "content": {
            "type": "string",
            "description": "The note content.",
        },
        "label": {
            "type": "string",
            "description": "A short label that uniquely identifies the note.",
        }
    }
    required_arguments = ["content"]

    def __call__(self, content, label=None):
        messages = self._sigmund.messages
        if label is None:
            label = self._auto_label(messages)
        if len(messages.get_notes()) >= config.max_notes:
            return (f'Failed to create note: maximum number of notes '
                    f'({config.max_notes}) reached.', None, True)
        if len(content) > config.max_note_length:
            return (f'Failed to create note: content exceeds maximum length '
                    f'({config.max_note_length} characters).', None, True)
        messages.set_note(label, content)
        message = f'I created a persistent note for myself ({label}).'
        return message, None, True

    def _auto_label(self, messages):
        existing = messages.get_notes()
        counter = 1
        while f'note_{counter}' in existing:
            counter += 1
        return f'note_{counter}'


class update_note(BaseTool):
    """Updates the content of an existing persistent note."""

    arguments = {
        "label": {
            "type": "string",
            "description": "The label of the note to update.",
        },
        "content": {
            "type": "string",
            "description": "The new content for the note.",
        }
    }
    required_arguments = ["label", "content"]

    def __call__(self, label, content):
        messages = self._sigmund.messages
        if label not in messages.get_notes():
            return (f'Failed to update note: no note with label "{label}" '
                    f'exists.', None, True)
        if len(content) > config.max_note_length:
            return (f'Failed to update note: content exceeds maximum length '
                    f'({config.max_note_length} characters).', None, True)
        messages.set_note(label, content)
        message = f'I updated my persistent note ({label}).'
        return message, None, True


class remove_note(BaseTool):
    """Removes a persistent note from the conversation."""

    arguments = {
        "label": {
            "type": "string",
            "description": "The label of the note to remove.",
        }
    }
    required_arguments = ["label"]

    def __call__(self, label):
        messages = self._sigmund.messages
        if label not in messages.get_notes():
            return (f'Failed to remove note: no note with label "{label}" '
                    f'exists.', None, True)
        messages.remove_note(label)
        message = f'I removed my persistent note ({label}).'
        return message, None, True


class save_workspace_as_note(BaseTool):
    """Saves the current workspace content as a persistent note."""

    arguments = {
        "label": {
            "type": "string",
            "description": "A short label that uniquely identifies the note.",
        },
        "clear_workspace": {
            "type": "boolean",
            "description": "If true, clear the workspace after saving it as "
                           "a note. Defaults to true. (default=False)",
        },
        "summarize": {
            "type": "boolean",
            "description": "If true, store a summary of the workspace content "
                           "instead of the full content. (default=False)",
        }
    }
    required_arguments = ["label"]

    def __call__(self, label, clear_workspace=True, summarize=False):
        messages = self._sigmund.messages
        if messages.workspace_content is None:
            return ('Failed to save workspace as note: the workspace is '
                    'empty.', None, True)
        if len(messages.get_notes()) >= config.max_notes:
            return (f'Failed to create note: maximum number of notes '
                    f'({config.max_notes}) reached.', None, True)
        content = messages.workspace_content
        if summarize:
            summary_prompt = prompt.render(
                prompt.SUMMARIZE_PROMPT, text_representation=content)
            content = self._sigmund.condense_model.predict(summary_prompt)
            if not isinstance(content, str):
                return ('Failed to save workspace as note: summarization '
                        'failed.', None, True)
            content = content.strip()
        if len(content) > config.max_note_length:
            return (f'Failed to create note: content exceeds maximum length '
                    f'({config.max_note_length} characters).', None, True)
        messages.set_note(label, content)
        message = (f'I saved the workspace content as a persistent note '
                   f'({label}).')
        if clear_workspace:
            return message, 'Workspace converted to note.', True
        return message, None, True
