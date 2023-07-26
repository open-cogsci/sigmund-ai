import re
import random
from pathlib import Path
from flask import Flask, request, jsonify
import jinja2
import json
import openai
import logging
import time
import config
logger = logging.getLogger('heymans')


def get_system_prompt(course, name, source):
    source = Path(source).read_text()
    source = re.sub('(?<!\n)\n(?!\n)', ' ', source).replace('\n ', ' ')
    while '\n\n\n' in source:
        source = source.replace('\n\n\n', '\n\n')
    tmpl = jinja2.Template(
        (Path('sources') / course / 'prompt_template.txt').read_text())
    return tmpl.render(ai_name=config.ai_name, source=source, name=name)
    

def log_chat(session_id, chat_history):
    if not Path('sessions').exists():
        Path('sessions').mkdir()
    Path(f'sessions/{session_id}.json').write_text(
        json.dumps(chat_history))


app = Flask(__name__, static_url_path='/static')
openai.api_key = config.openai_api_key
sessions = {}


@app.route('/api', methods=['POST'])
def api():
    data = request.get_json()
    message = data['message']
    session_id = data.get('session_id', 'default')
    chat_history = sessions.get(session_id, None)
    student_nr = data['student_nr'].strip()
    if not config.is_valid_student_nr(student_nr):
        return jsonify({'response': f'I\'m sorry, but {student_nr} is not a '
                                     'valid student number for this course.'})
    if chat_history is None:
        logger.info(f'initializing session {session_id}')
        name = data['name'].strip()
        if not name:
            name = 'Anonymous Student'
        course = data['course']
        chapter = data['chapter']
        source_folder = Path('sources') / course / chapter
        source = random.choice(list(source_folder.glob('*.txt')))
        logger.info(f'using source {source}')
        system_prompt = get_system_prompt(course, name, source)
        chat_history = {
            'name': name,
            'student_nr': student_nr,
            'course': course,
            'chapter': chapter,
            'source': str(source),
            'messages': [{"role": "system", "content": system_prompt}]
        }
    else:
        logger.info(f'resuming session {session_id}')
    if message:
        chat_history['messages'].append({"role": "user", "content": message})
    log_chat(session_id, chat_history)
    print(message)
    if '<REPORT>' in message:
        ai_message = 'Thank you for your feedback. Restart the conversation to try again! <REPORTED>'
    elif len(chat_history['messages']) > config.max_chat_length:
        ai_message = 'You have reached the maximum number of messages. Restart the conversation to try again!'
    else:
        if config.model == 'dummy':
            time.sleep(1)
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
    log_chat(session_id, chat_history)
    sessions[session_id] = chat_history
    return jsonify({'response': ai_message})
    

def render(path):
    tmpl = jinja2.Template(Path(path).read_text())
    return tmpl.render(ai_name=config.ai_name,
                       page_title=config.page_title,
                       server_url=config.server_url,
                       default_name=config.default_name,
                       default_student_nr=config.default_student_nr,
                       course_content=json.dumps(config.course_content))


@app.route('/chat')
def chat():
    return render('static/client.html')


@app.route('/client.js')
def javascript():
    return render('static/client.js')


if __name__ == '__main__':
    app.run(port=config.server_port)
