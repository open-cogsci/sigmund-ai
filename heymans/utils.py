import jinja2
import json
import html
import logging
import textwrap
import time
import os
import io
from flask import render_template, render_template_string
from datetime import datetime
from pathlib import Path
from cryptography.fernet import Fernet
import base64
import hashlib
import markdown
import subprocess
import tempfile
from pdfminer.high_level import extract_text
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


def clean(text, escape_html=True):
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


def file_to_text(name, content):
    suffix = os.path.splitext(name)[1]
    if suffix == '.pdf':
        try:
            text_representation = extract_text(io.BytesIO(content))
        except Exception as e:
            logger.error(f'failed to extract text: {e}')
            return 'No description'
    else:
        with tempfile.NamedTemporaryFile(suffix=suffix) as temp_file:
            temp_file.write(content)
            try:
                output = subprocess.run(
                    ['pandoc', '-s', temp_file.name, '-t', 'plain'],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    check=True,
                    text=True
                )
            except subprocess.CalledProcessError as e:
                logger.error(f'failed to extract text: {e}')
                return 'No description'
        text_representation = output.stdout
    if not text_representation:
        text_representation = content.decode('utf-8', errors='ignore')
    text_representation = text_representation.strip()[
        :config.max_text_representation_length]
    if not text_representation:
        return 'No description'
    return text_representation

def describe_file(name, content, model):
    text_representation = file_to_text(name, content)
    description = model.predict(
        f'''Provide a brief description of the following text:
        
Filename: {name}
        
<TEXT>\n{text_representation}\n</TEXT>''')
    return description
