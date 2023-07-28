import jinja2
import json
from datetime import datetime
from pathlib import Path
from . import chatmodes
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


def format_sources(sources):
    if not sources:
        return ''
    formatted_sources = []
    textbooks = {}
    for path in sources:
        # Then it's not a textbook section
        if len(path.parts) < 3:
            continue
        section = path.name
        # Remove .txt extension and '-X' suffix that indicates sections that
        # have split up into smaller sections to fit into the prompt
        section = section[:-4].rsplit('-', 1)[0]
        course = path.parent.parent.name
        if course not in config.course_content:
            return ''
        textbook = config.course_content[course]['textbook']
        if textbook not in textbooks:
            textbooks[textbook] = {}
        chapter = config.course_content[course]['chapters'][path.parent.name]
        formatted_source = f'{textbook}, {chapter}, {section}'
        if formatted_source not in formatted_sources:
            formatted_sources.append(formatted_source)
    summarized_sources = chatmodes.predict(f'''You have just provided an answer based on the sources below. Each source has a textbook, chapter, and section.

```python
{formatted_sources}
```

Please response with a phrase that indicates that you've consulted these sources, starting with: For this answer I read''')
    return f'<div class="message-sources">{summarized_sources}</div>'
