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
        max_message_length=config.max_message_length,
        version=__version__,
        primary_font=config.primary_font,
        secondary_font=config.secondary_font,
        background_color=config.background_color,
        user_message_color=config.user_message_color,
        send_button_color=config.send_button_color,
        start_button_color=config.start_button_color,
        finished_color=config.finished_color,
        reported_color=config.reported_color,
        header_logo=config.header_logo,
        link_color=config.link_color,
        visited_link_color=config.visited_link_color,
        **kwargs)
