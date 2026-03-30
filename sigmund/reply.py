import json
from . import config, utils, process_sigmund_message


class BaseReply:

    def __contains__(self, needle):
        return needle.lower() in self.to_json().lower()

    def __str__(self):
        return self.to_json()


class Reply(BaseReply):
    """Corresponds to a regular AI reply that is sent to the client."""
    def __init__(self, msg: str, metadata: dict,
                 workspace_content: str=None, workspace_language: str='text',
                 usage: float=0):
        self.msg = msg
        self.metadata = metadata
        self.workspace_content = workspace_content
        self.workspace_language = workspace_language
        self.usage = usage

    def to_json(self):
        return json.dumps(
            {'response': utils.md(
                process_sigmund_message.process_ai_message(self.msg)),
             'metadata': self.metadata,
             'workspace_content': self.workspace_content,
             'workspace_language': self.workspace_language,
             'usage': self.usage
            }
        )


class ActionReply(BaseReply):
    """Corresponds to an action reply that is sent to the client, typically to
    set the loading indicator.
    """
    def __init__(self, msg, action='set_loading_indicator'):
        self.msg = msg
        self.action = action

    def to_json(self):
        return json.dumps({'action': self.action, 'message': self.msg})


class StreamReply(BaseReply):
    """Corresponds to a streaming text chunk sent during AI response
    generation. The front-end uses these to progressively display the
    response before the final Reply arrives.
    """
    def __init__(self, msg):
        self.msg = msg

    def to_json(self):
        msg  = utils.extract_workspace(self.msg)[0]
        return json.dumps(
            {'stream': utils.md(
                process_sigmund_message.process_ai_message(msg))})

