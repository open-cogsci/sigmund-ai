from .expensive_test_utils import BaseExpensiveTest
from sigmund import config


class TestToolNotes(BaseExpensiveTest):

    def setUp(self):
        config.settings_default['tool_add_note'] = 'true'
        config.settings_default['tool_update_note'] = 'true'
        config.settings_default['tool_remove_note'] = 'true'
        config.settings_default['tool_save_workspace_as_note'] = 'true'
        super().setUp()

    def _test_tool(self):
        # Step 1: Ask the model to create a note
        query = ('Please create a note with the label "user_pref" and the '
                 'content "The user prefers concise responses."')
        for reply in self.sigmund.send_user_message(query):
            print(reply.msg)
        notes = self.sigmund.messages.get_notes()
        assert 'user_pref' in notes, \
            f'Expected "user_pref" in notes, got: {notes}'
        assert 'concise' in notes['user_pref'].lower(), \
            f'Expected "concise" in note content, got: {notes["user_pref"]}'

        # Step 2: Update the note
        query = ('Please update the note "user_pref" to say "The user '
                 'prefers detailed, verbose responses."')
        for reply in self.sigmund.send_user_message(query):
            print(reply.msg)
        notes = self.sigmund.messages.get_notes()
        assert 'user_pref' in notes, \
            f'Expected "user_pref" still in notes after update, got: {notes}'
        assert 'verbose' in notes['user_pref'].lower(), \
            f'Expected "verbose" in updated note, got: {notes["user_pref"]}'

        # Step 3: Add a second note
        query = ('Please create another note with label "project" and '
                 'content "Working on a Python web app."')
        for reply in self.sigmund.send_user_message(query):
            print(reply.msg)
        notes = self.sigmund.messages.get_notes()
        assert len(notes) == 2, \
            f'Expected 2 notes, got {len(notes)}: {notes}'
        assert 'project' in notes, \
            f'Expected "project" in notes, got: {notes}'

        # Step 4: Remove the first note
        query = 'Please remove the note labeled "user_pref".'
        for reply in self.sigmund.send_user_message(query):
            print(reply.msg)
        notes = self.sigmund.messages.get_notes()
        assert 'user_pref' not in notes, \
            f'Expected "user_pref" to be removed, got: {notes}'
        assert 'project' in notes, \
            f'Expected "project" to still exist, got: {notes}'

        # Step 5: Verify the remaining note survives a new message
        query = 'What notes do you currently have?'
        for reply in self.sigmund.send_user_message(query):
            print(reply.msg)
        notes = self.sigmund.messages.get_notes()
        assert 'project' in notes, \
            f'Expected "project" to persist across messages, got: {notes}'