import html
import logging
import textwrap
from bs4 import BeautifulSoup
import time
import re
from flask import render_template, render_template_string
import markdown
from markdown.extensions.fenced_code import FencedCodeExtension
from markdown.extensions.codehilite import CodeHiliteExtension
from markdown.extensions.toc import TocExtension
from markdown.extensions.attr_list import AttrListExtension
from markdown.extensions.md_in_html import MarkdownInHtmlExtension
from langchain.schema import HumanMessage
from . import config
from . import __version__
logger = logging.getLogger('sigmund')


def md(text):
    return markdown.markdown(text,
                             extensions=[FencedCodeExtension(),
                                         CodeHiliteExtension(),
                                         TocExtension(),
                                         AttrListExtension(),
                                         MarkdownInHtmlExtension()])


def clean(text, escape_html=True, render=True):
    if render:
        text = render_template_string(text)
    if escape_html:
        text = html.escape(text)
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


def extract_workspace(txt: str) -> tuple:
    """Takes a string of text and extracts workspace content from it. There are
    a few ways in which this can occur:
    
    - If the text contains a workspace indicated like this:
      <workspace language="language">
      your workspace content
      </workspace>`
      Then language and the content should be extracted and returned as the 
      second value of the tuple. If no language is specified, it defaults to
      'markdown'. The workspace tags and content should be stripped from txt.
    - If the text doesn't contain an explicit workspace, but does contain 
      markdown code blocks like this:
      ```language 
      code here
      ```
      Then this code should be extracted as the workspace content and language,
      again falling back markdown if no language is provided. The markdown
      code blocks do not have to be stripped from txt.
      
    Return txt, workspace_content, language
    """
    open_pattern = r'^<workspace(?: language="(.+?)")?>'
    if re.search(open_pattern, txt, re.DOTALL | re.MULTILINE) \
            and '</workspace>' not in txt:
        logger.warning('workspace closing tag appears to be missing')
        txt += '\n</workspace>'
    # Checks for <workspace> tags
    pattern = r'^<workspace(?: language="(.+?)")?>(.*?)^</workspace>'
    match = re.search(pattern, txt, re.DOTALL | re.MULTILINE)
    if match:
        language = match.group(1) if match.group(1) else 'markdown'
        content = match.group(2).strip()
        text_without_workspace = re.sub(pattern, "", txt,
                                        flags=re.DOTALL | re.MULTILINE).strip()
        # Empty messages can cause issues, so if stripping the workspace 
        # results in an empty message, we add a placeholder.
        if not text_without_workspace:
            text_without_workspace = 'I added content to the workspace!'
        return text_without_workspace, content, language
    # Checks for ``` code blocks
    pattern_codeblock = r'^```(?:([a-z]+))?\n(.*?)^```'
    match_codeblock = re.search(pattern_codeblock, txt, re.DOTALL | re.MULTILINE)
    if match_codeblock:
        language = match_codeblock.group(1) if match_codeblock.group(1) else 'markdown'
        content = match_codeblock.group(2).strip()
        if len(content.splitlines()) > 2:
            return txt, content, language
    # Simply returns txt if no workspace is detected
    return txt, None, None


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
