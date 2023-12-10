import jinja2
import json
import logging
from flask import render_template, render_template_string
from datetime import datetime
from pathlib import Path
import random
import markdown
from markdown.extensions.fenced_code import FencedCodeExtension
from markdown.extensions.codehilite import CodeHiliteExtension
from . import config
from . import __version__
logger = logging.getLogger('heymans')


def md(text):
    if '<REPORTED>' in text or '<FINISHED>' in text:
        return text
    return markdown.markdown(text,
                             extensions=[FencedCodeExtension(),
                                         CodeHiliteExtension()])


def clean(text):
    return render_template_string(text)
    

def render(path, **kwargs):
    return render_template(
        path,
        ai_name=config.ai_name,
        page_title=config.page_title,
        server_url=config.server_url,
        login_text=config.login_text,
        max_message_length=config.max_message_length,
        version=__version__,
        header_logo=config.header_logo,
        **kwargs)
