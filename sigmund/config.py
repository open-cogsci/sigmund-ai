import os
import re
from . import utils
import logging
logger = logging.getLogger('sigmund')
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
encryption_salt = os.environ.get('SIGMUND_ENCRYPTION_SALT', '0123456789ABCDEF').encode()

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
max_text_representation_length = 30000

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
welcome_message_with_search = '''Nice to meet you! I am Sigmund, your friendly OpenSesame assistant! How can I help you?

<div class="message-notification">I am currently functioning as an OpenSesame expert. <a href="/user_question_guide">Learn how to ask effective questions.</a> If you want to discuss things that are not related to OpenSesame, <a href="/api/conversation/new/without_search">click here</a> to turn me into a regular chatbot that has access to a wider range of tools.</div>'''
welcome_message_without_search = '''Nice to meet you! I am Sigmund, your friendly AI assistant! What would you like to discuss?

<div class="message-notification">I am currently functioning as a regular chatbot. In this mode I can do <a href="/about">lots of things</a>, but I cannot read the OpenSesame documentation. Therefore, if you want help with OpenSesame, <a href="/api/conversation/new/with_search">click here</a> to turn me into an OpenSesame expert.</div>'''
# The default title of a new conversation
default_conversation_title = 'New conversation'
# The number of previous messages for which tool results should be 
# retained.
keep_tool_results = 4

# RATE LIMITS
#
# The maximum number of tokens that can be consumed per hour by the answer
# model.
max_tokens_per_hour = 100000
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
# - claude-3-sonnet
# - claude-3-opus
# - mistral-tiny
# - mistral-small
# - mistral-medium
# - dummy
# Model configuations are combinations of models that can be used together
# - The search model is used to formulate search queries and evaluate whether
#   documents are relevant. This can be a cheap model.
# - The condense model is used to summarize message history when the 
#   conversation becomes too long. This can also be a cheap model.
# - The answermodel generates the actual answer. This should be a very capable
#   model
model_config = {
    'openai': {
        'search_model': 'gpt-3.5',
        'condense_model': 'gpt-3.5',
        'public_model': 'claude-3-haiku',
        'answer_model': 'gpt-4'
    },
    'anthropic': {
        'search_model': 'claude-3.5-sonnet',
        'condense_model': 'claude-3.5-sonnet',
        'public_model': 'claude-3-haiku',
        'answer_model': 'claude-3.5-sonnet'
    },
    'mistral': {
        'search_model': 'mistral-large',
        'condense_model': 'mistral-medium',
        'public_model': 'claude-3-haiku',
        'answer_model': 'mistral-large'
    },
    'dummy': {
        'search_model': 'dummy',
        'condense_model': 'dummy',
        'public_model': 'dummy',
        'answer_model': 'dummy'
    }
}
# Model-specific keyword arguments that are passed to the message generation
# functions
anthropic_kwargs = {
    'max_tokens': 1024
}
openai_kwargs = {}
mistral_kwargs = {}

# TOOLS
# 
# Tools should match the names of classes from sigmund.tools
# Search tools are executed in the first documentation-search phase
search_tools = ['search_documentation']
# Answer tools are executed during the answer phase
answer_tools_with_search = []
answer_tools_without_search = ['read_attachment', 'search_google_scholar',
                               'execute_code', 'download']

# SETTINGS
#
# These are default values for settings, which are stored in the database.
settings_default = {
    # Indicates whether documentation should be searched before answering the 
    'search_first': 'true',
    # Indicates the model configuration as specified above
    'model_config': 'openai'
}

# DOCUMENTATION
#
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
    'mouse_response_item': 'sources/topics/mouse_response_item.md',
    'feedback_item': 'sources/topics/feedback_item.md',
    'keyboard_response_item': 'sources/topics/keyboard_response_item.md',
    'logger_item': 'sources/topics/logger_item.md',
    'loop_item': 'sources/topics/loop_item.md',
    'sampler_item': 'sources/topics/sampler_item.md',
    'sketchpad_item': 'sources/topics/sketchpad_item.md',
    'synth_item': 'sources/topics/synth_item.md',
    'sequence_item': 'sources/topics/sequence_item.md',
}
# The number of documents that is considered for each search query
search_docs_per_query = 20
# The number of documents that is kept for all search queries combined
search_docs_max = 6
# The distance metric to search through documentation. Should be 'cosine' or
# 'euclidean_distance'
search_docs_distance_metric = 'cosine'
# The embedding model used for search. This has the name of an OpenAI embedding
# model
search_embedding_model = 'text-embedding-3-large'
# The number of documents and maximum number of words that is kept for public 
# search
public_search_docs_max = 6
public_search_max_doc_length = 1000
# The distance metric used for search. The cosine metric is useful because it
# is somewhat invariant to changes in document length
search_metric = 'cosine'
# The cache folder for the library that contains documentation
db_cache = 'default'
db_cache_sources = {
    'default': '.db.cache',
    'public-with-forum': '.public-with-forum.db.cache',
    'public-without-forum': '.public-without-forum.db.cache'
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
    that verifies the account. 
    
    Parameters
    ----------
    username : str
        Lowercase. Whitespace has been stripped.
    password : str
        Whitespace has been stripped.
        
    Returns
    -------
    str or None:
        If the user is validated, the username is returned. This is typically
        equal to the `username` parameter, but in some cases it may differ, for
        example if the user logs in with an email address instead of the actual
        username. If the user is not validated, None is returned.
    """
    try:
        import user_validation
    except ImportError:
        logger.info('no user validation script found')
        return username
    logger.info('using validation script')
    return user_validation.validate(username, password)


login_failed_message = '__User name or password incorrect. Please try again.__'


# SUBSCRIPTIONS
#
# Enable this to activate the Stripe-based subscription functionality.
subscription_required = bool(
    int(os.environ.get('SIGMUND_SUBSCRIPTION_REQUIRED', 0)))
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
# Additional keywords passed to stripe.checkout.Session.create to customize
# the checkout process
stripe_checkout_keywords = dict(
    allow_promotion_codes=True,
    payment_method_types=['card', 'ideal', 'bancontact', 'paypal'])


# GOOGLE LOGIN
#
google_login_enabled = True
google_client_id = os.environ.get("GOOGLE_CLIENT_ID", None)
google_client_secret = os.environ.get("GOOGLE_CLIENT_SECRET", None)
google_discovery_url = (
    "https://accounts.google.com/.well-known/openid-configuration"
)
