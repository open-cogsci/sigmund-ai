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


def process_ai_message(msg):
    msg = msg.replace('<div class="thinking_block_content">',
                      '<div class="thinking_block_content" markdown="1">')
    msg = fix_bullet_points(msg)
    # This pattern looks for a colon possibly followed by any number of
    # whitespaces
    # and/or HTML tags, followed by a newline and a dash, and
    # replaces it with a colon, newline, newline, and dash
    pattern = r':\s*(&lt;[^&gt;]+&gt;\s*)?\n(?=-|\d+\.)'
    replacement = ':\n\n'
    msg = re.sub(pattern, replacement, msg)
    # If the message doesn't start with a letter, then it may start with some 
    # markdown character that we should properly interpret, and thus needs to 
    # be on a newline preceded by an empty line.
    if msg and not msg[0].isalpha():
        msg = '\n\n' + msg
    msg = dedent_code_blocks(msg)
    msg = fix_markdown_headings(msg)
    return msg


def dedent_code_blocks(message: str) -> str:
    """
    Dedent code blocks (triple backticks or triple tildes) if *all* lines
    in the block share the same leading indentation, including the fence lines.
    Handles optional language specifiers like ```python or ~~~javascript.
    """

    lines = message.splitlines(keepends=True)  # preserve line endings
    n = len(lines)
    i = 0
    result = []

    while i < n:
        line = lines[i]
        # Attempt to match an opening fence: indentation + "```" or "~~~",
        # plus optional language specifier, and then end-of-line.
        mo_open = re.match(r'^([ \t]*)(```|~~~)([^\n]*)\r?\n?$', line)
        if not mo_open:
            # Not an opening fence line => just append and move on
            result.append(line)
            i += 1
            continue
        # Extract fence info
        indent = mo_open.group(1)
        fence = mo_open.group(2)
        # The optional language spec is mo_open.group(3), but we don’t need to store it

        block_lines = [line]  # include opening fence line
        found_closing = False
        i_block = i + 1

        # Look for matching closing fence
        while i_block < n:
            candidate = lines[i_block]
            mo_close = re.match(
                rf'^([ \t]*)({re.escape(fence)})([^\n]*)\r?\n?$', 
                candidate
            )
            if mo_close and mo_close.group(1) == indent:
                # Same indentation, same fence => it's the closing fence
                block_lines.append(candidate)
                found_closing = True
                i_block += 1
                break
            else:
                # Not a closing fence => collect as part of the block
                block_lines.append(candidate)
                i_block += 1

        # If we found a closing fence, we can attempt to dedent
        if found_closing:
            # Check uniform indentation for ALL lines in block (opening + content + closing)
            all_share_indent = True
            for bline in block_lines:
                # Ignore empty lines
                if not bline.strip():
                    continue                
                mo_line = re.match(r'^([ \t]*)(.*)$', bline)
                if mo_line:
                    line_indent = mo_line.group(1)
                    if line_indent < indent:
                        all_share_indent = False
                        break

            if all_share_indent:
                # Dedent each line by removing the common indent
                dedented = [bline[len(indent):] if bline.strip() else bline
                            for bline in block_lines]
                result.extend(dedented)
            else:
                # Keep block as-is
                result.extend(block_lines)

            i = i_block
        else:
            # No closing fence found => keep everything as-is
            result.extend(block_lines)
            i = i_block

    return "".join(result)


def fix_markdown_headings(text: str) -> str:
    """
    Converts text with heading lines of repeated '─' or '-' surrounding a heading
    into valid Markdown headings, ensuring each heading is non-empty and followed by
    a blank line.
    
    Example:
      ────────────────────────────────────────────────────────────────────────
      Why you’re getting “Bad file descriptor”
      ────────────────────────────────────────────────────────────────────────
      
    becomes:
      ## Why you’re getting “Bad file descriptor”
      
      (with a blank line after)
    """
    lines = text.splitlines()
    output = []
    i = 0
    while i < len(lines):
        line = lines[i].rstrip()
        
        # Check if the current line is a "rule" line
        if re.fullmatch(r'[─-]{10,}', line):
            # Make sure we have at least two more lines to consider
            if i + 2 < len(lines):
                heading_candidate = lines[i + 1].rstrip()
                next_line = lines[i + 2].rstrip()
                
                # Check if the line after next is also a "rule" line
                if re.fullmatch(r'[─-]{10,}', next_line):
                    # Check if the heading candidate is non-empty
                    if heading_candidate.strip():
                        # It's a heading: turn the middle line into a heading
                        output.append(f"## {heading_candidate.strip()}")
                        output.append("")  # blank line after heading
                        i += 3
                        continue
        
        # If it's not a heading section, just add the line as is
        output.append(line)
        i += 1
    
    return "\n".join(output)


def fix_bullet_points(text: str) -> str:
    """
    Convert lines that start with '• ' into '- '.
    """
    # Use a regex that finds lines that begin either at start of text or
    # after a newline, followed by '•', then a space, e.g. "• ".
    return re.sub(r"^(?:•)\s+", "- ", text, flags=re.MULTILINE)
