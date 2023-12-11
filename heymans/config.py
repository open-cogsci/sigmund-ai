import os
from . import utils
import logging
logger = logging.getLogger('heymans')
page_title = 'Sigmund AI'
ai_name = 'Sigmund'

# SERVER
# The external server address, that is, the URL that users visit
server_url = os.environ.get('FLASK_SERVER_URL', 'http://127.0.0.1:5000')
# The port at which the flask server is running internally. This can be
# different from the server URL if the app is running behind a proxy that
# redirects
flask_port = int(os.environ.get('FLASK_PORT', 5000))
# The flask host arhument where all 0s means listen to all incoming addresses
flask_host = os.environ.get('FLASK_HOST', '0.0.0.0')
# The secret key is used for logging in. This should be a long and arbitrary
# string that is hard to guess. This should not be shared
flask_secret_key = os.environ.get('FLASK_SECRET_KEY', None)
# A secret salt that is used to encrypt the messages on disk in combination
# with the user password
encryption_salt = os.environ.get('HEYMANS_ENCRYPTION_SALT', '0123456789ABCDEF').encode()

max_prompt_length = 20000
condense_chunk_length = 10000

# LIBRARY INDEXING
# The number of documents that are indexed at once and the delay after each
# chunk. This is to avoid exceeded the rate limits of the OpenAI API
chunk_size = 100
chunk_throttle = .1

# MESSAGES
# The maximum length of a user message
max_message_length = 5000
# A fixed welcome message
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

# MODELS
# The API keys should not be shared
openai_api_key = os.environ.get('OPENAI_API_KEY', None)
anthropic_api_key = os.environ.get('ANTHROPIC_API_KEY', None)
# The search model is used to formulate search queries and evaluate whether
# documents are relevant
search_model = 'gpt-3.5'
# The condense model is used to summarize message history when the conversation
# becomes too long
condense_model = 'gpt-3.5'
# The answermodel generates the actual answer
answer_model = 'gpt-4'

# DOCUMENTATION
# Topic sources are used to feed in specific chunks of documentation that are
# relevant to a topic.
topic_sources = {
    'opensesame': 'sources/topics/opensesame.md',
    'python': 'sources/topics/inline_script.py',
    'inline_script': 'sources/topics/inline_script.py',
    'osweb': 'sources/topics/inline_javascript.js',
    'javascript': 'sources/topics/inline_javascript.js',
    'inline_javascript': 'sources/topics/inline_javascript.js',
    'datamatrix': 'sources/topics/datamatrix.py',
    'data_analysis': 'sources/topics/datamatrix.py',
    'questions_howto': 'sources/topics/questions-how-to.md',
}


def process_ai_message(msg):
    """Allows for processing of the AI message before it is passed to Python
    markdown. This allows for some common formatting issues to be resolved, 
    such as the fact that the AI often forgets to put a blank line between
    the colon and the start of the enumeration, and that fenced code blocks
    are sometimes indented.
    """
    return utils.deindent_code_blocks(msg.replace(':\n-', ':\n\n-'))
    

def validate_user(username, password):
    """user_validation.validate() should connect to an authentication system
    that verifies the account.
    """
    try:
        import user_validation
    except ImportError:
        logger.info('no user validation script found')
        return True
    logger.info('using validation script')
    return user_validation.validate(username, password)
