import logging
import base64
import os
import requests
from datetime import datetime
from urllib.parse import urlparse, unquote
from . import BaseTool
from .. import attachments
logger = logging.getLogger('heymans')


class DownloadTool(BaseTool):
    
    # The JSON pattern should match the regular expression shown in the prompt
    # and catch the URL as a group with the name 'url'.
    json_pattern = r"\"download_url\":\s*\"(?P<url>https?://[^']+)\""
    prompt = '''# Download files
    
You have access to the internet. To download a file, use JSON in the format below. The file will be added to your attachments.

{"download_url": "https://url_to_file"}
'''

    def _download(self, url):
        """Download URL and return a filename, content tuple."""
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()  # Raises an HTTPError for bad responses
    
            # Attempt to get the filename from the Content-Disposition header
            content_disposition = response.headers.get('Content-Disposition')
            if content_disposition:
                # If there's a filename in the header, extract it
                filename = re.findall('filename="?(.+)"?', content_disposition)[0]
            else:
                # Parse the URL to get a base filename
                parsed_url = urlparse(url)
                if parsed_url.path:
                    # Unquote URL to decode %20, etc. to actual characters
                    filename = unquote(os.path.basename(parsed_url.path))
                else:
                    # Use the domain name and a timestamp as the filename
                    filename = parsed_url.netloc.replace('.', '_') + '_' + datetime.now().strftime('%Y%m%d%H%M%S')
    
            # Check if the filename is empty or just a slash, assign a default name
            if not filename or filename == '/':
                filename = 'download_' + datetime.now().strftime('%Y%m%d%H%M%S')
    
            # Add an appropriate file extension if missing
            if not os.path.splitext(filename)[1]:
                filename += '.html'  # Default to .html for web pages without a clear file type
    
            content = response.content
            return filename, content
        except Exception as e:
            logger.error(f"Failed to download the file from {url}: {e}")
            raise
            
    def use(self, message, url):
        try:
            filename, content = self._download(url)
        except Exception as e:
            return f'I failed to download the file for the following reason: {e}', True
        description = attachments.describe_file(filename, content,
                                                self._heymans.condense_model)
        attachment_data = {
            'filename': filename,
            'content': base64.b64encode(content).decode('utf-8'),
            'description': description
        }
        self._heymans.database.add_attachment(attachment_data)
        return f'''I have downloaded {filename} and added it to my attachments.
        
<div class='json-references'>
Note to self: In my next reply I can 1) read {filename} by replying with `{{"read_attachment": "{filename}"}}`, or 2) ask the user what to do with the downloaded file.
</div> <TRANSIENT>''', True
