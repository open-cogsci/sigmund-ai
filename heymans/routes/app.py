import json
import base64
from pathlib import Path
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from flask import redirect, url_for, session, Blueprint
from flask_login import login_user, login_required, current_user, \
    logout_user, UserMixin
from .. import config
from .. import utils
from ..forms import LoginForm
from ..heymans import Heymans
import logging
logger = logging.getLogger('heymans')
app_blueprint = Blueprint('app', __name__)


class User(UserMixin):
    def __init__(self, username):
        self.id = username
        logger.info(f'initializing user id: {self.id}')


def get_heymans():
    return Heymans(user_id=current_user.get_id(), persistent=True,
                   encryption_key=session['encryption_key'])
    

def chat_page():
    heymans = get_heymans()
    if config.subscription_required and \
            not heymans.database.check_subscription():
        return redirect(url_for('subscribe.subscribe'), code=303)
    html_content = ''
    previous_timestamp = None
    previous_answer_model = None
    for role, message, metadata in heymans.messages:
        message_id = metadata.get('message_id', 0)
        delete_button = f'<button class="message-delete" onclick="deleteMessage(\'{message_id}\')"><i class="fas fa-trash"></i></button>'
        if role == 'assistant':
            html_body = utils.md(
                f'{config.ai_name}: {config.process_ai_message(message)}')
            html_class = 'message-ai'
        else:
            html_body = '<p>' + utils.clean(f'You: {message}', 
                                            escape_html=True,
                                            render=False) + '</p>'
            html_class = 'message-user'
        if 'sources' in metadata:
            sources_div = '<div class="message-sources">'
            sources = json.loads(metadata['sources'])
            urls = {source['url'] for source in sources if source['url']}
            for url in urls:
                sources_div += f'<a href="{url}">{url}</a><br />'
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
            
        html_content += f'<div class="message {html_class}" data-message-id="{message_id}">{delete_button}{html_body}{timestamp_div}{answer_model_div}{sources_div}</div>'
    # The user's settings are the defaults updated with the user-specific 
    # settings from the database
    settings = config.settings_default.copy()
    settings.update(heymans.database.list_settings())
    return utils.render('chat.html', message_history=html_content,
                        subscription_required=config.subscription_required,
                        username=heymans.user_id,
                        search_first_menu_label=config.search_first_menu_label,
                        settings=json.dumps(settings))


def login_handler(form, failed=False):
    if form.validate_on_submit():
        username = form.username.data.strip().lower()
        password = form.password.data.strip()
        username = config.validate_user(username, password)
        if username is None:
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
        logger.info(f'initializing encryption key')
        return redirect('/')
    login_text = Path('heymans/static/login.md').read_text()
    if failed:
        login_text = f'{config.login_failed_message}\n\n{login_text}'
    return utils.render(
        'login.html', form=form,
        login_text=utils.md(login_text))
    
    
@app_blueprint.route('/about')
def about():
    return utils.render(
        'info-page.html',
        content=utils.md(Path('heymans/static/about.md').read_text()))
    

@app_blueprint.route('/terms')
def terms():
    return utils.render(
        'info-page.html',
        content=utils.md(Path('heymans/static/terms.md').read_text()))


@app_blueprint.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('app.chat'))
    return login_handler(LoginForm())


@app_blueprint.route('/login_failed', methods=['GET', 'POST'])
def login_failed():
    return login_handler(LoginForm(), failed=True)


@app_blueprint.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('app.login'))


@app_blueprint.route('/')
def main():
    if current_user.is_authenticated:
        return chat_page()
    return redirect(url_for('app.login'))


@app_blueprint.route('/chat')
def chat():
    if current_user.is_authenticated:
        return chat_page()
    return redirect(url_for('app.login'))
