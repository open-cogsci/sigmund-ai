import os
import re
from . import utils
import logging
logger = logging.getLogger('heymans')
page_title = 'Sigmund AI'
ai_name = 'Sigmund'

# SERVER
#
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
flask_secret_key = os.environ.get('FLASK_SECRET_KEY', '0123456789ABCDEF')
# A secret salt that is used to encrypt the messages on disk in combination
# with the user password
encryption_salt = os.environ.get('HEYMANS_ENCRYPTION_SALT', '0123456789ABCDEF').encode()

# FILES AND FOLDERS
#
# Contains the encrypted message history
sessions_folder = 'sessions'
# Contains the encrypted uploads
uploads_folder = 'uploads'

# PROMPT HISTORY
#
# The maximum length of a prompt in characters. If the prompt exceeds this 
# length, the start will be summarized.
max_prompt_length = 20000
# The length of the prompt to be summarized.
condense_chunk_length = 10000

# ATTACHMENTS
#
# The maximum length of the text representation of an attachment that is used
# to generate a description
max_text_representation_length = 16000

# LIBRARY INDEXING
#
# The number of documents that are indexed at once and the delay after each
# chunk. This is to avoid exceeded the rate limits of the OpenAI API
chunk_size = 100
chunk_throttle = .1

# MESSAGES
# The maximum length of a user message
max_message_length = 5000
# A fixed welcome message
welcome_message_with_search = '''Nice to meet you! I am Sigmund, your friendly OpenSesame assistant!

I am best at answering questions that are specific and that I can look up in the documentation. I also have basic code execution abilities, can read attachments, and can look up scientific articles on Google Scholar.

What is your name? And would you like to learn more about how to work with me?

<small style="color:gray;">PS. If you want to discuss things that are unrelated to OpenSesame, disable "OpenSesame expert" mode in the menu. That will make me a better general-purpose chatbot.</small>'''
welcome_message_without_search = '''Nice to meet you! I am Sigmund, your friendly AI assistant!

I have basic code execution abilities, I can read attachments, and I can look up scientific articles on Google Scholar.

Let\'s get started! What would like you to disuss?

<small style="color:gray;">PS. If you want help with OpenSesame, enable "OpenSesame expert" mode in the menu. That will give me access to the OpenSesame documentation.</small>
'''
# The default title of a new conversation
default_conversation_title = 'New conversation'
# The number of previous messages for which transient content should be 
# retained. Transient content are large chunks of information that are included
# in AI messages, usually as the result of tool use.
keep_transient = 4

# RATE LIMITS
#
# The maximum number of tokens that can be consumed per hour by the answer
# model.
max_tokens_per_hour = 50000
max_tokens_per_hour_exceeded_message = 'You have reached the hourly usage limit. Please wait and try again later!'


# LOGGING
#
# When set to True, replies will be logged. This should disabled during 
# production for privacy.
log_replies = False

# MODELS
#
# The API keys should not be shared
openai_api_key = os.environ.get('OPENAI_API_KEY', None)
anthropic_api_key = os.environ.get('ANTHROPIC_API_KEY', None)
mistral_api_key = os.environ.get('MISTRAL_API_KEY', None)
# Supported models are currently:
# - gpt-3.5
# - gpt-4
# - claude-2.1
# - mistral-tiny
# - mistral-small
# - mistral-medium
# - dummy
# The search model is used to formulate search queries and evaluate whether
# documents are relevant
search_model = 'gpt-3.5'
# The condense model is used to summarize message history when the conversation
# becomes too long
condense_model = 'gpt-3.5'
# The answermodel generates the actual answer
answer_model = 'gpt-4'

# TOOLS
# 
# Tools should match the names of classes from heymans.tools
# Search tools are executed in the first documentation-search phase
search_tools = ['TopicsTool', 'SearchTool']
# Answer tools are executed during the answer phase
answer_tools = ['CodeExecutionTool', 'GoogleScholarTool', 'AttachmentsTool',
                'DownloadTool']

# DOCUMENTATION
#
# Indicates whether documentation should be searched before answering the 
# question.
search_first = True
# Jow the search-first option appears in the menu
search_first_menu_label = 'OpenSesame expert'
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
    # This pattern looks for a colon possibly followed by any number of 
    # whitespaces # and/or HTML tags, followed by a newline and a dash, and 
    # replaces it with a colon, newline, newline, and dash
    pattern = r':\s*(<[^>]+>\s*)?\n-'
    replacement = ':\n\n-'
    return re.sub(pattern, replacement, msg)
    

def validate_user(username, password):
    """user_validation.validate() should connect to an authentication system
    that verifies the account. Whitespace has been stripped from both the
    username and the password. The username is converted to lowercase.
    """
    try:
        import user_validation
    except ImportError:
        logger.info('no user validation script found')
        return True
    logger.info('using validation script')
    return user_validation.validate(username, password)


login_failed_message = '__User name or password incorrect. Please try again.__'


# SUBSCRIPTIONS
#
# Enable this to activate the Stripe-based subscription functionality.
subscription_required = True
# This is the duration of the subscription in days. This should be set to a bit
# longer than a month to provide a grace period in case of payment issues.
subscription_length = 40
#
# Stripe is a payment portal. The information below should not be shared
#
# The Price ID identifies the product. You can find it in the product catalog
# of the Stripe dashboard.
stripe_price_id = os.environ.get('STRIPE_PRICE_ID', None)
# The publishable key is the API keys section of the Developers dashboard
stripe_publishable_key = os.environ.get('STRIPE_PUBLISHABLE_KEY', None)
# The secret (API) key is the API keys section of the Developers dashboard
stripe_secret_key = os.environ.get('STRIPE_SECRET_KEY', None)
# The webhook secret is used to ensure that webhook calls actually come from
# stripe
stripe_webhook_secret = os.environ.get('STRIPE_WEBHOOK_SECRET', None)
