from . import BaseTool
from .. import config, prompt
import logging

logger = logging.getLogger('sigmund')

USER_CONTEXT_NOTES = '''# Persistent notes

How to use persistent notes:

- Use persistent notes, when you receive instructions for a complex task. Store the instructions as a note. In addition, create a todo list as a note, and update it as you work through the task. When the task is done, clear up the notes for the instructions and todo list.
- Use persistent notes, when you need to make sure that information stays available to you.
- Do *not* use persistent notes to share information with the user, because the user cannot see your notes. To share information with the user, use the workspace instead.

{% for label, content in notes.items() %}
<note label="{{ label }}">
{{ content }}
</note>
{% endfor %}'''


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
        return None, None, True

    def _auto_label(self, messages):
        existing = messages.get_notes()
        counter = 1
        while f'note_{counter}' in existing:
            counter += 1
        return f'note_{counter}'
        
    def user_context(self):
        notes = self._sigmund.messages._notes
        if config.log_replies:
            for label in notes:
                logger.info(f'[note] {label}')
        return prompt.render(USER_CONTEXT_NOTES, notes=notes)


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
        return None, None, True


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
        return None, None, True


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
        if clear_workspace:
            return None, 'Workspace converted to note.', True
        return None, None, True
