from . import BaseTool
import logging
import json
import base64
from .. import utils
logger = logging.getLogger('heymans')


class AttachmentsTool(BaseTool):
    
    json_pattern = r'"read_attachments"\s*:\s*(?P<attachments>\[\s*"(?:[^"\\]|\\.)*"(?:\s*,\s*"(?:[^"\\]|\\.)*")*\s*\])'

    @property
    def prompt(self):
        info = {"read_attachments": []}
        description = []
        for attachment in self._heymans.database.list_attachments().values():
            info['read_attachments'].append(attachment['filename'])
            description.append(
                f'- {attachment["filename"]}: {attachment["description"]}')
        if not description:
            logger.info('no attachments for tool')
            return ''
        description = '\n'.join(description)
        info = json.dumps(info)
        prompt = f'''# Attachments

You have access to the following attached documents:

{description}

To read them, use JSON in the format below. You will receive the attachment in the next message.

{info}
'''
        return prompt
    
    def use(self, message, attachments):
        
        texts = []
        for attachment_id, attachment in \
                self._heymans.database.list_attachments().items():
            if attachment['filename'] not in attachments:
                continue
            attachment = self._heymans.database.get_attachment(attachment_id)
            content = utils.file_to_text(
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
