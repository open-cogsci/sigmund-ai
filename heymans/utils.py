import jinja2
import json
from datetime import datetime
from pathlib import Path
from . import config
from . import __version__


def render(path):
    tmpl = jinja2.Template(Path(path).read_text())
    return tmpl.render(ai_name=config.ai_name,
                       page_title=config.page_title,
                       server_url=config.server_url,
                       default_name=config.default_name,
                       default_student_nr=config.default_student_nr,
                       max_message_length=config.max_message_length,
                       version=__version__,
                       course_content=json.dumps(config.course_content))


def get_system_prompt(course, name, source):
    source = config.clean_source(Path(source).read_text())
    tmpl = jinja2.Template(
        (Path('sources') / course / 'prompt_template.txt').read_text())
    return tmpl.render(ai_name=config.ai_name, source=source, name=name)


def save_chat_history(session_id, chat_history):
    if not Path('sessions').exists():
        Path('sessions').mkdir()
    chat_history['end_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    Path(f'sessions/{session_id}.json').write_text(
        json.dumps(chat_history))


def load_chat_history(session_id):
    path = Path(f'sessions/{session_id}.json')
    if path.exists():
        return json.loads(Path(f'sessions/{session_id}.json').read_text())
    return None
