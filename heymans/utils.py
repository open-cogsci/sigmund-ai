import html
import logging
import textwrap
import time
from flask import render_template, render_template_string
import markdown
from markdown.extensions.fenced_code import FencedCodeExtension
from markdown.extensions.codehilite import CodeHiliteExtension
from markdown.extensions.toc import TocExtension
from markdown.extensions.attr_list import AttrListExtension
from langchain.schema import HumanMessage
from . import config
from . import __version__
logger = logging.getLogger('heymans')


def md(text):
    if '<REPORTED>' in text or '<FINISHED>' in text:
        return text
    return markdown.markdown(text,
                             extensions=[FencedCodeExtension(),
                                         CodeHiliteExtension(),
                                         TocExtension(),
                                         AttrListExtension()])


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
    
    
def prepare_messages(messages, allow_ai_first=True, allow_ai_last=True,
                     merge_consecutive=False, merge_separator='\n'):
    """Takes a list of Message objects formats them to meet the requirements
    of specific models.
    
    Parameters
    ----------
    messages : list
        A list of messages, where each message object has a type property that
        is either 'system', 'ai', or ;'human'
    allow_ai_first : bool, optional
        Indicates whether the first message (after the system message) can be
        an AI message. If not, then it is removed.
    allow_ai_last : bool, optional
        Indicates whether the last message (after the system message) can be
        an AI message. If not, then a human message is appended after it.
    merge_consecutive : bool, optional
        Indicates whether multiple messages of the same class should be merged
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
    # Check whether first message after the system message is an AI message, 
    # and remove this if not allowed
    if not allow_ai_first and messages[1].type == 'ai':
        logger.info('removing first assistant mesage')
        messages.pop(1)        
    # Merge consecutive messages of the same class totether
    if len(messages) > 1 and merge_consecutive:
        merged_messages = []
        current_message = messages[0]
        for next_message in messages[1:]:
            if current_message.type == next_message.type:
                logger.info('merging consecutive messages')
                current_message.content += merge_separator + next_message.content
            else:
                merged_messages.append(current_message)
                current_message = next_message
        merged_messages.append(current_message)
        messages = merged_messages
    # Make sure the last message is human if this is required
    if not allow_ai_last and messages[-1].type == 'ai':
        logger.info('adding continue message')
        messages.append(HumanMessage(content='Please continue!'))
    return messages


def current_datetime():
    return time.strftime('%a %d %b %Y %H:%M')
