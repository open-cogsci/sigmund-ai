from . import BaseTool


class update_workspace_content(BaseTool):
    """Updates the content of the workspace. Use this to share text or code with the user."""

    arguments = {
        "content": {
            "type": "string",
            "description": "The workspace content.",
        },
        "language": {
            "type": "string",
            "description": "The language of the workspace content. (default='markdown')",
        }
    }
    required_arguments = ["content"]

    def __call__(self, content, language='markdown'):
        return None, content, language, False
