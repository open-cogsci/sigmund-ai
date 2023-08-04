import random
import markdown
from pathlib import Path
from datetime import datetime
from flask import Flask, request, jsonify, Response, render_template, \
    redirect, url_for
from flask_login import login_user, LoginManager, UserMixin, login_required, \
    current_user, logout_user
from .forms import LoginForm
import openai
import logging
import time
from . import config
from . import utils
from . import chatmodes


class User(UserMixin):
    def __init__(self, username):
        self.id = username


logger = logging.getLogger('heymans')
logging.basicConfig(level=logging.INFO, force=True)
openai.api_key = config.openai_api_key
app = Flask(__name__, static_url_path='/static')
app.config['SECRET_KEY'] = config.flask_secret_key
login_manager = LoginManager()
@login_manager.user_loader
def load_user(user_id):
    return User(user_id)
login_manager.init_app(app)


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
    session_id = data.get('session_id', 'default')
    chat_history = utils.load_chat_history(session_id)
    if chat_history is None:
        logger.info(f'initializing session (session_id={session_id})')
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
        user_info = config.user_info(current_user.get_id())
        name = user_info.get('first_name', 'Unknown Student')
        system_prompt = utils.get_system_prompt(course, name, source)
        chat_history = {
            'user_info': user_info,
            'name': name,
            'start_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'course': course,
            'chapter': chapter,
            'source': str(source),
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
    user_info = config.user_info(current_user.get_id())
    if chat_history is None:
        # The first message from the Q&A chatmode to start the conversation
        if not message:
            if hasattr(config, 'init_user_qa'):
                config.init_user_qa(user_info)
            ai_message, sources = chatmodes.qa()
            return jsonify(
                {'response': utils.md(f'{config.ai_name}: {ai_message}') +
                utils.format_sources(sources)})
        logger.info(f'initializing session (session_id={session_id})')
        chat_history = {
            'user_info': user_info,
            'start_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'messages': []
        }
    else:
        logger.info(f'resuming session (session_id={session_id})')
    if hasattr(config, 'resume_user_qa'):
        config.resume_user_qa(user_info)
    return api_main(message, session_id, chat_history, chatmodes.qa)


def login_handler(form, html):
    if form.validate_on_submit():
        if not config.validate_user(form.username.data,
                                    form.password.data):
            return redirect('/login_failed')
        user = User(form.username.data)
        login_user(user)
        return redirect('/')
    return utils.render(html, form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    return login_handler(LoginForm(), 'login.html')


@app.route('/login_failed', methods=['GET', 'POST'])
def login_failed():
    return login_handler(LoginForm(), 'login_failed.html')


@app.route('/logout')
def logout():
    logout_user()
    return redirect('/login')


@app.route('/')
def main():
    if current_user.is_authenticated:
        if config.main_endpoint == 'practice':
            return utils.render('practice.html')
        return utils.render('qa.html')
    else:
        return redirect(url_for('login'))


@app.route('/practice')
@login_required
def practice():
    return utils.render('practice.html')


@app.route('/library')
def library():
    return utils.render('library.html')


@app.route('/qa')
@login_required
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
