import logging
import base64
import os
import requests
from datetime import datetime
from urllib.parse import urlparse, unquote
from . import BaseTool
from .. import attachments
logger = logging.getLogger('sigmund')


class download(BaseTool):
    """Download a file or webpage from the internet. The downloaded file or webpage will be saved as attachment, and can be read later.·"""
    
    arguments = {
        "url": {
            "type": "string",
            "description": "The url of a file of webpage",
        }
    }
    required_arguments = ["url"]    

    def _download(self, url):
        """Download URL and return a filename, content tuple."""
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            # Attempt to get the filename from the Content-Disposition header
            content_disposition = response.headers.get('Content-Disposition')
            if content_disposition:
                # If there's a filename in the header, extract it
                filename = re.findall('filename="?(.+)"?', 
                                      content_disposition)[0]
            else:
                # Parse the URL to get a base filename
                parsed_url = urlparse(url)
                if parsed_url.path:
                    # Unquote URL to decode %20, etc. to actual characters
                    filename = unquote(os.path.basename(parsed_url.path))
                else:
                    # Use the domain name and a timestamp as the filename
                    filename = parsed_url.netloc.replace('.', '_') + '_' \
                        + datetime.now().strftime('%Y%m%d%H%M%S')
            # Check if the filename is empty or just a slash, use default name
            if not filename or filename == '/':
                filename = 'download_' \
                    + datetime.now().strftime('%Y%m%d%H%M%S')
            # Add an appropriate file extension if missing
            if not os.path.splitext(filename)[1]:
                # Default to .html for web pages without a clear file type
                filename += '.html'  
            content = response.content
            return filename, content
        except Exception as e:
            logger.error(f"Failed to download the file from {url}: {e}")
            raise
            
    def __call__(self, url):
        filename, content = self._download(url)
        description = attachments.describe_file(filename, content,
                                                self._sigmund.condense_model)
        attachment_data = {
            'filename': filename,
            'content': base64.b64encode(content).decode('utf-8'),
            'description': description
        }
        self._sigmund.database.add_attachment(attachment_data)
        return f'''I have downloaded {filename} and added it to my attachments.''', \
            '', False