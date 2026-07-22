import html
import logging
import time
import re
import base64
from io import BytesIO
from flask import render_template, render_template_string
import markdown
from markdown.extensions.fenced_code import FencedCodeExtension
from markdown.extensions.codehilite import CodeHiliteExtension
from markdown.extensions.toc import TocExtension
from markdown.extensions.attr_list import AttrListExtension
from markdown.extensions.md_in_html import MarkdownInHtmlExtension
from markdown.extensions.tables import TableExtension
from . import config
from . import __version__
logger = logging.getLogger('sigmund')


def md(text):
    return markdown.markdown(text,
                             extensions=[FencedCodeExtension(),
                                         CodeHiliteExtension(),
                                         TocExtension(),
                                         AttrListExtension(),
                                         MarkdownInHtmlExtension(),
                                         TableExtension()])


def clean(text, escape_html=True, render=True):
    if render:
        text = render_template_string(text)
    if escape_html:
        text = html.escape(text)
    return text
    

def render(path, theme=None, **kwargs):
    if theme is None or theme not in config.themes:
        theme = config.settings_default['theme']
    kwargs['theme_stylesheet'] = config.themes[theme]['stylesheet']
    kwargs['theme_pygments'] = config.themes[theme]['pygments']
    kwargs['theme_codemirror'] = config.themes[theme]['codemirror']
    return render_template(
        path,
        ai_name=config.ai_name,
        page_title=config.page_title,
        server_url=config.server_url,
        max_message_length=config.max_message_length,
        version=__version__,
        **kwargs)


def prepare_messages(messages, allow_ai_first=True, allow_ai_last=True,
                     merge_consecutive=False, merge_separator='\n'):
    """Takes a list of Message objects formats them to meet the requirements
    of specific models.

    Parameters
    ----------
    messages : list
        A list of messages, where each message is a dict with 'role' and 'content' keys.
        Valid roles are 'system', 'assistant', and 'user'.
    allow_ai_first : bool, optional
        Indicates whether the first message (after the system message) can be
        an assistant message. If not, then it is removed.
    allow_ai_last : bool, optional
        Indicates whether the last message (after the system message) can be
        an assistant message. If not, then a user message is appended after it.
    merge_consecutive : bool, optional
        Indicates whether multiple messages of the same role should be merged
        into a single message.
    merge_separator : str, optional
        If messages are merged, the separator that is used to join their 
        content.

    Returns
    -------
    list
    """
    if not isinstance(messages, list):
        return messages
    if not messages:
        return []
    # Check whether first message after the system message is an assistant message, 
    # and remove this if not allowed
    if not allow_ai_first and messages[1]['role'] == 'assistant':
        logger.info('removing first assistant message')
        messages.pop(1)        
    # Merge consecutive messages of the same role together
    if len(messages) > 1 and merge_consecutive:
        merged_messages = []
        current_message = messages[0]
        for next_message in messages[1:]:
            if current_message['role'] == next_message['role']:
                logger.info('merging consecutive messages')
                current_message['content'] += merge_separator + next_message['content']
            else:
                merged_messages.append(current_message)
                current_message = next_message
        merged_messages.append(current_message)
        messages = merged_messages
    # Make sure the last message is user if this is required
    if not allow_ai_last and messages[-1]['role'] == 'assistant':
        logger.info('adding continue message')
        messages.append(dict(role='user', content='Please continue!'))
    return messages


def remove_masked_elements(content):
    # This pattern matches:
    #   1) an opening tag <tag ...>
    #   2) that includes class="...mask..."
    #   3) everything inside (including nested tags)
    #   4) up to the matching </tag>
    #
    # It does this by capturing the tag name in group 1, so we can search for
    # the matching </tag> later, and also checking for "mask" in the class attribute.
    pattern = re.compile(
        r'<([a-zA-Z0-9]+)([^>]*)\bclass\s*=\s*[\'"]([^"\']*\bmask\b[^"\']*)[\'"]([^>]*)>(.*?)</\1>',
        re.DOTALL
    )
    return re.sub(pattern, '', content)


def current_datetime():
    return time.strftime('%a %d %b %Y %H:%M')


def limit_image_size(img_data, max_size=3_000_000):
    """
    Scale down a base64-encoded image if its size exceeds max_size.

    Args:
        img_data (str): Base64-encoded image data
        max_size (int): Maximum allowed size in bytes (default: 5,000,000)

    Returns:
        str: Base64-encoded image data (original or scaled down)
    """
    
    if len(img_data) <= max_size:
        return img_data
    from PIL import Image
    img_bytes = base64.b64decode(img_data)
    img = Image.open(BytesIO(img_bytes))
    # Start with 90% quality and reduce if needed
    quality = 90
    scale_factor = 0.9  # Start with 90% of original size
    while True:
        # Calculate new dimensions while maintaining aspect ratio
        new_width = int(img.width * scale_factor)
        new_height = int(img.height * scale_factor)
        # Ensure minimum size of 1x1
        new_width = max(1, new_width)
        new_height = max(1, new_height)
        # Resize the image
        resized_img = img.resize((new_width, new_height), Image.LANCZOS)
        # Save to bytes buffer with current quality
        buffer = BytesIO()
        resized_img.save(buffer, format=img.format, quality=quality,
                         optimize=True)
        buffer_size = buffer.tell()
        # Check if we're under the size limit
        if buffer_size <= max_size:
            # Encode back to base64
            return base64.b64encode(buffer.getvalue()).decode('utf-8')
        # If not, reduce quality first, then scale factor
        if quality > 10:
            quality -= 10
        else:
            scale_factor -= 0.1
        # Safety check to prevent infinite loop
        if scale_factor <= 0.1:
            break
    # If we get here, we couldn't reduce enough - return the smallest possible
    buffer = BytesIO()
    resized_img.save(buffer, format=img.format, quality=10, optimize=True)
    return base64.b64encode(buffer.getvalue()).decode('utf-8')
