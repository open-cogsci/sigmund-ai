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
                 workspace_content: str=None, workspace_language: str='text'):
        self.msg = msg
        self.metadata = metadata
        self.workspace_content = workspace_content
        self.workspace_language = workspace_language
        
    def to_json(self):
        return json.dumps(
            {'response': utils.md(
                f'{config.ai_name}: {process_sigmund_message.process_ai_message(self.msg)}'),
             'metadata': self.metadata,
             'workspace_content': self.workspace_content,
             'workspace_language': self.workspace_language
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
