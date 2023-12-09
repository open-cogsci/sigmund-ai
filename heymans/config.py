import os
import logging

logger = logging.getLogger('heymans')
page_title = 'Sigmund AI'
ai_name = 'Sigmund'
header_logo = 'static/sofa.png'
primary_font = 'Poppins'
secondary_font = 'Roboto Condensed'
background_color = '#d7d7d7'
user_message_color = '#00796b'
send_button_color = '#00796b'
start_button_color = '#00796b'
finished_color = '#388e3c'
reported_color = '#e64a19'
link_color = '#0288d1'
visited_link_color = '#0288d1'

flask_port = 5000
server_url = 'http://127.0.0.1:5000'
flask_host = '0.0.0.0'
flask_secret_key = os.environ.get('FLASK_SECRET_KEY', None)

max_prompt_length = 20000
condense_chunk_length = 10000

chunk_size = 100
chunk_throttle = .1
max_message_length = 1000
max_source_tokens = 6000
openai_api_key = os.environ.get('OPENAI_API_KEY', None)
anthropic_api_key = os.environ.get('ANTHROPIC_API_KEY', None)
search_model = 'gpt-3.5'
condense_model = 'gpt-3.5'
answer_model = 'gpt-4'
welcome_message = '''Nice to meet you! I am Sigmund, your friendly OpenSesame assistant! What is your name? 

I am best at answering questions that are specific and that I can look up in the documentation. Would you like to learn more about how to work with me?'''
login_text = '''Welcome to Sigmund, your friendly OpenSesame assistant!

<ul>
<li>Sigmund is better at answering questions about OpenSesame than other chatbots.</li>
<li>Log in using your account from <a href="forum.cogsci.nl">forum.cogsci.nl</a>.</li>
<li>All messages are encrypted so that no-one can listen in on your conversation.</li>
</ul>

Sigmund is currently in limited beta and by invitation only.
'''

topic_sources = {
    'opensesame': 'sources/topics/opensesame.md',
    'python': 'sources/topics/inline_script.py',
    'inline_script': 'sources/topics/inline_script.py',
    'osweb': 'sources/topics/inline_javascript.js',
    'javascript': 'sources/topics/inline_javascript.js',
    'inline_javascript': 'sources/topics/inline_javascript.js',
    'questions_howto': 'sources/topics/questions-how-to.md',
}


# In production, the password and encryption should be set to the user password
# and salt by validate_user() 
encryption_password = 'some password'
encryption_salt = '0123456789ABCDF'


def validate_user(username, password):
    try:
        import user_validation
    except ImportError:
        logger.info('no user validation script found')
        return True
    logger.info('using validation script')
    global encryption_password, encryption_salt
    encryption_password, encryption_salt = user_validation.validate(
        username, password)
    if encryption_password is None or encryption_salt is None:
        return False
    return True
