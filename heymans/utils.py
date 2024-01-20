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


def current_datetime():
    return time.strftime('%a %d %b %Y %H:%M')
