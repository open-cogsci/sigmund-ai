import html
import logging
import textwrap
import time
from flask import render_template, render_template_string
import markdown
from markdown.extensions.fenced_code import FencedCodeExtension
from markdown.extensions.codehilite import CodeHiliteExtension
from markdown.extensions.toc import TocExtension
from . import config
from . import __version__
logger = logging.getLogger('heymans')


def md(text):
    if '<REPORTED>' in text or '<FINISHED>' in text:
        return text
    return markdown.markdown(text,
                             extensions=[FencedCodeExtension(),
                                         CodeHiliteExtension(),
                                         TocExtension()])


def clean(text, escape_html=True, render=True):
    if render:
        text = render_template_string(text)
    if escape_html:
        text = html.escape(text).replace('\n', '<br>\n')
    return text
    

def render(path, **kwargs):
    return render_template(
        path,
        ai_name=config.ai_name,
        page_title=config.page_title,
        server_url=config.server_url,
        max_message_length=config.max_message_length,
        version=__version__,
        **kwargs)


def deindent_code_blocks(text):
    in_block = False
    lines = []
    for line_nr, line in enumerate(text.splitlines()):
        if in_block:
            block.append(line)
            # Ending line
            if line.lstrip().startswith('```'):
                in_block = False
                block = textwrap.dedent('\n'.join(block))
                lines.append(block)
            continue
        # Starting line
        if line.lstrip().startswith('```'):
            in_block = True
            block = [line]
        else:
            lines.append(line)
    return '\n'.join(lines)
    
    
def merge_messages(messages, separator='\n'):
    """Takes a list of Message objects and merges consecutive AI and human 
    messages into a single message. This is required by some models, such as
    Claude.
    """
    if not messages:
        return []
    if len(messages) < 2:
        return messages
    merged_messages = []
    current_message = messages[0]
    for next_message in messages[1:]:
        if current_message.type == next_message.type:
            current_message.content += separator + next_message.content
        else:
            merged_messages.append(current_message)
            current_message = next_message
    merged_messages.append(current_message)
    return merged_messages


def current_datetime():
    return time.strftime('%a %d %b %Y %H:%M')
