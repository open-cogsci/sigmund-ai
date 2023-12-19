import random
import markdown
import json
from pathlib import Path
from datetime import datetime
from flask import Flask, request, jsonify, Response, render_template, \
    redirect, url_for, session, stream_with_context
from flask_login import login_user, LoginManager, UserMixin, login_required, \
    current_user, logout_user
from .forms import LoginForm
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.fernet import Fernet
import base64
import logging
import time
from . import config
from . import utils
from .heymans import Heymans
logger = logging.getLogger('heymans')


class User(UserMixin):
    def __init__(self, username):
        self.id = username
        logger.info(f'initializing user id: {self.id}')


logger = logging.getLogger('heymans')
logging.basicConfig(level=logging.INFO, force=True)
app = Flask(__name__, static_url_path='/static')
app.config['SECRET_KEY'] = config.flask_secret_key
login_manager = LoginManager()
@login_manager.user_loader
def load_user(user_id):
    return User(user_id)
login_manager.init_app(app)


def clear_message_history():
    user_id = current_user.get_id()
    heymans = Heymans(user_id=user_id, persistent=True,
                      encryption_key=session['encryption_key'])
    heymans.messages.clear()
    heymans.messages.save()
    
    
def chat_page():
    user_id = current_user.get_id()
    heymans = Heymans(user_id=user_id, persistent=True,
                      encryption_key=session['encryption_key'])
    html_content = ''
    previous_timestamp = None
    previous_answer_model = None
    for role, message, metadata in heymans.messages:
        if role == 'assistant':
            html_body = utils.md(
                f'{config.ai_name}: {config.process_ai_message(message)}')
            html_class = 'message-ai'
        else:
            html_body = '<p>' + utils.clean(f'You: {message}', 
                                            escape_html=True) + '</p>'
            html_class = 'message-user'
        if 'sources' in metadata:
            sources_div = '<div class="message-sources">'
            sources = json.loads(metadata['sources'])
            for source in sources:
                if source['url']:
                    sources_div += f'<a href="{source["url"]}">{source["url"]}</a><br />'
            sources_div += '</div>'
        else:
            sources_div = ''
        if previous_timestamp != metadata['timestamp']:
            previous_timestamp = metadata['timestamp']
            timestamp_div = f'<div class="message-timestamp">{metadata["timestamp"]}</div>'
        else:
            timestamp_div = ''
        if role == 'assistant' and previous_answer_model != metadata['answer_model']:
            previous_answer_model = metadata['answer_model']
            answer_model_div = f'<div class="message-answer-model">{metadata["answer_model"]}</div>'
        else:
            answer_model_div = ''
            
        html_content += f'<div class="{html_class}">{html_body}{timestamp_div}{answer_model_div}{sources_div}</div>'
    return utils.render('chat.html', message_history=html_content)


def login_handler(form, html):
    if form.validate_on_submit():
        username = form.username.data.strip().lower()
        password = form.password.data.strip()
        if not config.validate_user(username, password):
            return redirect('/login_failed')
        kdf = PBKDF2HMAC(algorithm=hashes.SHA256(),
                         length=32,
                         salt=config.encryption_salt,
                         iterations=100000,
                         backend=default_backend())
        session['encryption_key'] = base64.urlsafe_b64encode(
            kdf.derive(password.encode()))
        user = User(username)
        login_user(user)
        logger.info(f'initializing encryption key: {session["encryption_key"]}')
        return redirect('/')
    return utils.render(
        html, form=form,
        login_text=utils.md(Path('heymans/static/login.md').read_text()))
    
    
@app.route('/api/chat/start', methods=['POST'])
def api_chat_start():
    data = request.json
    session['user_message'] = data.get('message', '')
    return '{}'


@app.route('/api/chat/stream', methods=['GET'])
def api_chat_stream():
    message = session['user_message']
    user_id = current_user.get_id()
    heymans = Heymans(user_id=user_id, persistent=True,
                      encryption_key=session['encryption_key'])
    def generate():
        for reply, metadata in heymans.send_user_message(message):
            if isinstance(reply, dict):
                reply = json.dumps(reply)
            else:
                reply = json.dumps(
                    {'response': utils.md(
                        f'{config.ai_name}: {config.process_ai_message(reply)}'),
                     'metadata': metadata})
            logger.debug(f'ai message: {reply}')
            yield f'data: {reply}\n\n'
        yield 'data: {"action": "close"}\n\n'
    return Response(stream_with_context(generate()),
                    mimetype='text/event-stream')


@app.route('/about')
def about():
    return utils.render(
        'about.html',
        about_text=utils.md(Path('heymans/static/about.md').read_text()))


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


@app.route('/clear')
def clear():
    clear_message_history()
    return redirect('/chat')


@app.route('/')
def main():
    if current_user.is_authenticated:
        return chat_page()
    return redirect(url_for('login'))
    
@app.route('/chat')
@login_required
def chat():
    return chat_page()
