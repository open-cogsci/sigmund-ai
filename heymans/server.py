import random
import markdown
from pathlib import Path
from datetime import datetime
from flask import Flask, request, jsonify, Response, render_template, \
    redirect, url_for
from flask_login import login_user, LoginManager, UserMixin, login_required, \
    current_user, logout_user
from .forms import LoginForm
import logging
import time
from . import config
from . import utils
from .heymans import Heymans


class User(UserMixin):
    def __init__(self, username):
        self.id = username


logger = logging.getLogger('heymans')
logging.basicConfig(level=logging.INFO, force=True)
app = Flask(__name__, static_url_path='/static')
app.config['SECRET_KEY'] = config.flask_secret_key
login_manager = LoginManager()
@login_manager.user_loader
def load_user(user_id):
    return User(user_id)
login_manager.init_app(app)

@app.route('/api/chat', methods=['POST'])
def api_chat():
    data = request.get_json()
    message = data['message']
    session_id = data.get('session_id', 'default')
    user_id = current_user.get_id()
    heymans = Heymans(user_id=user_id, persistent=True)
    reply, sources = heymans.send_user_message(message)
    return jsonify({'response': utils.md(f'{config.ai_name}: {reply}'),
                    'sources': sources})
    
    
def chat_page():
    user_id = current_user.get_id()
    heymans = Heymans(user_id=user_id, persistent=True)
    html = ''
    for role, message in heymans.messages:
        if role == 'assistant':
            html_body = utils.md(f'{config.ai_name}: {message}')
            html_class = 'message-ai'
        else:
            html_body = utils.clean(f'You: {message}')
            html_class = 'message-user'
        html += f'<div class="{html_class}">{html_body}</div>'
    return utils.render('chat.html', message_history=html)


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
        return chat_page()
    return redirect(url_for('login'))
    
@app.route('/chat')
@login_required
def chat():
    return chat_page()


@app.route('/library')
def library():
    return utils.render('library.html')


@app.route('/main.js')
def main_js():
    return utils.render('main.js')

    
@app.route('/stylesheet.css')
def stylesheet():
    return Response(utils.render('stylesheet.css'), mimetype='text/css')
