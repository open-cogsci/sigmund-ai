import random
import markdown
from pathlib import Path
from datetime import datetime
from flask import Flask, request, jsonify, Response
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


def api_main(message, session_id, chat_history, chat_func):
    if message:
        message = message[:config.max_message_length]
        chat_history['messages'].append({"role": "user", "content": message})
    utils.save_chat_history(session_id, chat_history)
    logger.info(f'user message: {message} (session_id={session_id})')
    sources = None
    if '<REPORT>' in message:
        logger.info(f'conversation reported (session_id={session_id})')
        ai_message = 'Thank you for your feedback. Restart the conversation to try again! <REPORTED>'
    elif len(chat_history['messages']) > config.max_chat_length:
        logger.info(f'conversation too long (session_id={session_id})')
        ai_message = 'You have reached the maximum number of messages. Restart the conversation to try again! <TOO_LONG>'
    else:
        ai_message, sources = chat_func(chat_history)
    chat_history['messages'].append(
        {"role": "assistant", "content": ai_message})
    utils.save_chat_history(session_id, chat_history)
    logger.info(f'ai message: {ai_message} (session_id={session_id})')
    return jsonify(
        {'response': utils.md(f'{config.ai_name}: {ai_message}') +
         utils.format_sources(sources)})


@app.route('/api/practice', methods=['POST'])
def api_practice():
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
        logger.info(f'initializing session (session_id={session_id})')
        name = data['name']
        if not name:
            name = 'Anonymous Student'
        course = data['course']
        chapter = data['chapter']
        # If any chapter is selected, randomly select one of the folders from
        # the course folder
        if chapter == '__any__':
            chapter = random.choice(
                list(config.course_content[course]['chapters']))
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
            'messages': [{"role": "system", "content": system_prompt}]
        }
    else:
        logger.info(f'resuming session (session_id={session_id})')
    return api_main(message, session_id, chat_history, chatmodes.practice)


@app.route('/api/qa', methods=['POST'])
def api_qa():
    data = request.get_json()
    message = data['message']
    session_id = data.get('session_id', 'default')
    chat_history = utils.load_chat_history(session_id)
    if chat_history is None:
        # The first message from the Q&A chatmode to start the conversation
        if not message:
            ai_response, _ = chatmodes.qa()
            return jsonify({'response': ai_response})
        logger.info(f'initializing session (session_id={session_id})')
        chat_history = {
            'start_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'chatmode': 'qa',
            'messages': []
        }
        message = config.qa_first_question_template.format(question=message)
    else:
        logger.info(f'resuming session (session_id={session_id})')
    return api_main(message, session_id, chat_history, chatmodes.qa)


@app.route('/')
@app.route('/practice')
def practice():
    return utils.render('practice.html')


@app.route('/qa')
def qa():
    return utils.render('qa.html')


@app.route('/main.js')
def main_js():
    return utils.render('main.js')
    

@app.route('/practice.js')
def practice_js():
    return utils.render('practice.js')


@app.route('/qa.js')
def qa_js():
    return utils.render('qa.js')
    

@app.route('/stylesheet.css')
def stylesheet():
    return Response(utils.render('stylesheet.css'), mimetype='text/css')
