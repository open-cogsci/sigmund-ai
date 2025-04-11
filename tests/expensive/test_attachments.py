import base64
from pathlib import Path
from .expensive_test_utils import BaseExpensiveTest


class TestAttachments(BaseExpensiveTest):
    
    def _test_tool(self):
        
        image_attachment = Path(__file__).parent / 'testdata/emoji.png'
        base64_image = base64.b64encode(image_attachment.read_bytes()).decode('utf-8')
        image_url = f"data:image/png;base64,{base64_image}"
        pdf_attachment = Path(__file__).parent / 'testdata/secret-word.pdf'
        base64_pdf = base64.b64encode(pdf_attachment.read_bytes()).decode('utf-8')
        pdf_url = f"data:application/pdf;base64,{base64_pdf}"
        attachments = [{
            'type': 'document',
            'file_name': 'secret-word.pdf',
            'url': pdf_url
        },{
            'type': 'image',
            'file_name': 'emoji.png',
            'url': image_url
        }]
        query = 'What is the secret word? And is the emoji happy or sad?'
        for result in self.sigmund.send_user_message(
                query, attachments=attachments):
            print(result)
        assert 'unicorn' in result.msg.lower()
        assert 'happy' in result.msg.lower()
