from . import BaseTool
import logging
import json
import base64
from .. import utils
from ..attachments import file_to_text
logger = logging.getLogger('sigmund')


class read_attachment(BaseTool):
    """Read an attached file. The full contents of the attachment is returned as plain text."""
    arguments = {
        "filename": {
            "type": "string",
            "description": "The attachment file to read",
        }
    }
    required_arguments = ["filename"]
    
    @property
    def tool_spec(self):
        arguments = self.arguments.copy()
        arguments['filename']['enum'] = [
            attachment['filename'] for attachment in
            self._sigmund.database.list_attachments().values()
        ]
        return {
            "name": self.__class__.__name__,
            "description": self.__doc__,
            "parameters": {
                "type": "object",
                "properties": arguments,
                "required": self.required_arguments,
            }
        }
    
    def __call__(self, filename):
        texts = []
        for attachment_id, attachment in \
                self._sigmund.database.list_attachments().items():
            if filename != attachment['filename']:
                continue
            attachment = self._sigmund.database.get_attachment(attachment_id)
            content = file_to_text(
                attachment['filename'],
                base64.b64decode(attachment['content']))
            text = f'File name: {attachment["filename"]}\n\nFile content:\n{content}'
            result = f'''One moment please ...
        
<div class="attachment-content">
{text}
</div>'''            
            return 'I am going to read the attached file now.', result, True
        return 'Something went wrong while trying to read the attachment', \
            '', False