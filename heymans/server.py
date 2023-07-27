import random
from pathlib import Path
from datetime import datetime
from flask import Flask, request, jsonify
import openai
import logging
import time
from . import config
from . import utils
from . import chatmodes

logger = logging.getLogger('heymans')
logging.basicConfig(level=logging.INFO, force=True)
static_folder = Path(__file__).parent / 'static'
app = Flask(__name__, static_url_path='/static')
openai.api_key = config.openai_api_key


@app.route('/api', methods=['POST'])
def api():
    data = request.get_json()
    message = data['message']
    chatmode = data['chatmode']
    session_id = data.get('session_id', 'default')
    chat_history = utils.load_chat_history(session_id)
    student_nr = data['student_nr'].strip()
    if not config.is_valid_student_nr(student_nr):
        return jsonify({'response': f'I\'m sorry, but {student_nr} is not a '
                                    f'valid student number for this course.'})
    if chat_history is None:
        # The first message from the Q&A chatmode
        if not message and chatmode == 'qa':
            return jsonify({'response': chatmodes.qa()})
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
        system_prompt = utils.get_system_prompt(course, name, source)
        chat_history = {
            'name': name,
            'student_nr': student_nr,
            'start_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'course': course,
            'chapter': chapter,
            'source': str(source),
            'chatmode': chatmode,
            'messages': []
        }
        if chatmode == 'practice':
            chat_history['messages'].append(
                {"role": "system", "content": system_prompt})
    else:
        logger.info(f'resuming session (session_id={session_id})')
    if message:
        message = message[:config.max_message_length]
        chat_history['messages'].append({"role": "user", "content": message})
    utils.save_chat_history(session_id, chat_history)
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
                if chatmode == 'practice':
                    ai_message = chatmodes.practice(chat_history)
                elif chatmode == 'qa':
                    ai_message = chatmodes.qa(chat_history)
                else:
                    ai_message = f'Invalid chat mode: {chatmode}'
            except Exception as e:
                return jsonify({'error': str(e)}), 400
    chat_history['messages'].append(
        {"role": "assistant", "content": ai_message})
    utils.save_chat_history(session_id, chat_history)
    return jsonify({'response': ai_message})


@app.route('/chat')
def chat():
    return utils.render(static_folder / 'client.html')


@app.route('/client.js')
def javascript():
    return utils.render(static_folder / 'client.js')
