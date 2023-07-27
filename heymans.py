import random
from pathlib import Path
from datetime import datetime
from flask import Flask, request, jsonify
import jinja2
import json
import openai
import logging
import time
import config

__version__ = '0.1.5'
logger = logging.getLogger('heymans')
logging.basicConfig(level=logging.INFO, force=True)


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


app = Flask(__name__, static_url_path='/static')
openai.api_key = config.openai_api_key


@app.route('/api', methods=['POST'])
def api():
    data = request.get_json()
    message = data['message']
    session_id = data.get('session_id', 'default')
    chat_history = load_chat_history(session_id)
    student_nr = data['student_nr'].strip()
    if not config.is_valid_student_nr(student_nr):
        return jsonify({'response': f'I\'m sorry, but {student_nr} is not a '
                                     'valid student number for this course.'})
    if chat_history is None:
        logger.info(f'initializing session (session_id={session_id})')
        name = data['name'].strip()
        if not name:
            name = 'Anonymous Student'
        course = data['course']
        chapter = data['chapter']
        # If any chapter is selected, randomly select one of the folders from
        # the course folder
        if chapter == '__any__':
            course_folder = Path('sources') / course
            chapter = random.choice(
                [f.name for f in course_folder.iterdir() if f.is_dir()])
        source_folder = Path('sources') / course / chapter
        source = random.choice(list(source_folder.glob('*.txt')))
        logger.info(f'using source {source} (session_id={session_id})')
        system_prompt = get_system_prompt(course, name, source)
        chat_history = {
            'name': name,
            'student_nr': student_nr,
            'start_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'course': course,
            'chapter': chapter,
            'source': str(source),
            'messages': [{"role": "system", "content": system_prompt}]
        }
    else:
        logger.info(f'resuming session (session_id={session_id})')
    if message:
        message = message[:config.max_message_length]
        chat_history['messages'].append({"role": "user", "content": message})
    save_chat_history(session_id, chat_history)
    logger.info(f'Received message: {message} (session_id={session_id})')
    if '<REPORT>' in message:
        logger.info(f'conversation reported (session_id={session_id})')
        ai_message = 'Thank you for your feedback. Restart the conversation to try again! <REPORTED>'
    elif len(chat_history['messages']) > config.max_chat_length:
        logger.info(f'conversation too long (session_id={session_id})')
        ai_message = 'You have reached the maximum number of messages. Restart the conversation to try again!'
    else:
        if config.model == 'dummy':
            time.sleep(.2)
            if len(chat_history['messages']) > 3:
                ai_message = '<FINISHED>'
            else:
                ai_message = f'Dummy response based on {chat_history["source"]}'
        else:
            try:
                response = openai.ChatCompletion.create(
                  model=config.model,
                  messages=chat_history['messages'])
            except Exception as e:
                return jsonify({'error': str(e)}), 400
            ai_message = response.choices[0].message['content']
    chat_history['messages'].append(
        {"role": "assistant", "content": ai_message})
    save_chat_history(session_id, chat_history)
    return jsonify({'response': ai_message})
    

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


@app.route('/chat')
def chat():
    return render('static/client.html')


@app.route('/client.js')
def javascript():
    return render('static/client.js')


if __name__ == '__main__':
    app.run(host=config.flask_host, port=config.flask_port)
