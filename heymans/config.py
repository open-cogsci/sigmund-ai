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
flask_secret_key = os.environ['FLASK_SECRET_KEY']

max_prompt_length = 20000
condense_chunk_length = 10000

chunk_size = 100
chunk_throttle = .1
max_chat_length = 8
max_message_length = 1000
max_source_tokens = 6000
openai_api_key = os.environ.get('OPENAI_API_KEY', None)
anthropic_api_key = os.environ.get('ANTHROPIC_API_KEY', None)
search_model = 'gpt-3.5'
condense_model = 'gpt-3.5'
answer_model = 'gpt-4'
welcome_message = 'Hi, my name is Sigmund. How can I help you?'


def validate_user(username, password):
    return True


def user_info(username):
    return {
        'username': username,
        'first_name': 'John',
        'last_name': 'Doe',
        'email': 'user@domain.com'
    }


topic_sources = {
    'opensesame': 'sources/topics/opensesame.md',
    'python': 'sources/topics/inline_script.py',
    'inline_script': 'sources/topics/inline_script.py',
    'osweb': 'sources/topics/inline_javascript.js',
    'javascript': 'sources/topics/inline_javascript.js',
    'inline_javascript': 'sources/topics/inline_javascript.js',
}
