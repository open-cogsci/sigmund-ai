from . import BaseTool
import logging
import json
import base64
from .. import utils, attachments
logger = logging.getLogger('heymans')


class AttachmentsTool(BaseTool):
    
    json_pattern = r'"read_attachments"\s*:\s*(?P<attachments>\[\s*"(?:[^"\\]|\\.)*"(?:\s*,\s*"(?:[^"\\]|\\.)*")*\s*\])'

    @property
    def prompt(self):
        info = {'read_attachments': []}
        for attachment in self._heymans.database.list_attachments().values():
            info['read_attachments'].append(attachment['filename'])
        if not info['read_attachments']:
            logger.info('no attachments for tool')
            return ''
        info = json.dumps(info)
        return f'''# Attachments

To read attachments, use JSON in the format below. You will receive the attachments in the next message.

{info}
'''
    
    def use(self, message, attachments):
        
        texts = []
        for attachment_id, attachment in \
                self._heymans.database.list_attachments().items():
            if attachment['filename'] not in attachments:
                continue
            attachment = self._heymans.database.get_attachment(attachment_id)
            content = attachments.file_to_text(
                attachment['filename'],
                base64.b64decode(attachment['content']))
            text = f'File name: {attachment["filename"]}\n\nFile content:\n{content}'
            texts.append(text)
        if not texts:
            return '', False
        texts = '\n\n'.join(texts)
        return f'''I am going to read the attached file(s) now.
        
<div class='json-references'>
texts
</div> <TRANSIENT>''', True
