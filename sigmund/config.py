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

# LIBRARY INDEXING
#
# The number of documents that are indexed at once and the delay after each
# chunk. This is to avoid exceeded the rate limits of the OpenAI API
chunk_size = 100
chunk_throttle = .1

# MESSAGES
# The maximum length of a user message
max_message_length = 10000
# A fixed welcome message
welcome_message = '''Nice to meet you! I am Sigmund, your friendly AI assistant! How can I help you?'''
# The default title of a new conversation
default_conversation_title = 'New conversation'
# The number of previous messages for which tool results should be 
# retained.
keep_tool_results = 4
# Tool results larger than this are not included in the prompt used for
# generating
large_tool_result_length = 50000

# RATE LIMITS
#
# The maximum number of tokens that can be consumed per hour by the answer
# model.
max_tokens_per_hour = 500000
max_tokens_per_hour_exceeded_message = 'You have reached the hourly usage limit. Please wait and try again later!'
anthropic_max_thinking_tokens = 2048

# LOGGING
#
# When set to True, replies will be logged. This should disabled during 
# production for privacy.
log_replies = os.environ.get('SIGMUND_LOG_REPLIES', False)

# MODELS
#
# The API keys should not be shared
openai_api_key = os.environ.get('OPENAI_API_KEY', None)
anthropic_api_key = os.environ.get('ANTHROPIC_API_KEY', None)
mistral_api_key = os.environ.get('MISTRAL_API_KEY', None)
# Supported models are currently:
# - gpt-3.5
# - gpt-4o
# - gpt-4o-mini
# - claude-2.1
# - claude-3-sonnet
# - claude-3-opus
# - claude-3.5-sonnet
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
        'condense_model': 'gpt-4.1-mini',
        'public_model': 'gpt-4.1-mini',
        'answer_model': 'gpt-4.1'
    },
    'openai_o1': {
        'condense_model': 'gpt-4.1-mini',
        'public_model': 'gpt-4.1-mini',
        'answer_model': 'o3'
    },
    'anthropic': {
        'condense_model': 'claude-4-sonnet',
        'public_model': 'claude-3.5-haiku',
        'answer_model': 'claude-4-sonnet'
    },
    'anthropic_thinking': {
        'condense_model': 'claude-4-sonnet',
        'public_model': 'claude-3.5-haiku',
        'answer_model': 'claude-4-opus-thinking'
    },
    'mistral': {
        'condense_model': 'ministral-8b-2410',
        'public_model': 'gpt-4o-mini',
        'answer_model': 'mistral-medium-latest',
        'vision_model': 'pixtral-large-latest'
    },
    'dummy': {
        'condense_model': 'dummy',
        'public_model': 'dummy',
        'answer_model': 'dummy'
    }
}
# Model-specific keyword arguments that are passed to the message generation
# functions
anthropic_kwargs = {
    'max_tokens': 4096
}
openai_kwargs = {}
mistral_kwargs = {}

# TOOLS
#
tools = ['search_google_scholar', 'execute_code', 'generate_image']

# SETTINGS
#
# These are default values for settings, which are stored in the database.
settings_default = {
    # Indicates the model configuration as specified above
    'model_config': 'openai',
    # Indicates which tools are enabled
    'tool_execute_code': 'true',
    'tool_search_google_scholar': 'true',
    'tool_generate_image': 'true',
    # Indicates which library collections are enabled
    'collection_opensesame': 'true',
    'collection_datamatrix': 'true',
    'collection_forum': 'false'
}

# DOCUMENTATION
#

# Enables library search
search_enabled = True
# The library is organized into collections
search_collections = {'opensesame', 'datamatrix', 'forum'}
# The maximum distance should be determined empirically by comparing distances
# between realistic queries and relevant document, and unrelated queries and the
# documentation.
search_max_distance = 1.15
# If no results are found, we try again with a higher threshold. This may be
# necessary especially for short questions.
search_max_distance_fallback = 1.35
# The minimum length of the search query. If the query is shorter, we previous
# messages are prepended until the query reaches the minimum length or there are
# no more messages.
search_min_query_length = 1000
# The number of documents. This applies separately to regular documentation and
# howtos, and does include foundation documents.
search_docs_max = 4
# The embedding model used for search. This has the name of an OpenAI embedding
# model
search_embedding_model = 'text-embedding-3-large'
# The number of documents and maximum number of words that is kept for public 
# search
public_search_docs_max = 6
public_search_max_doc_length = 1000
search_persist_directory = "library"
search_embedding_provider = "openai"
search_embedding_model = "text-embedding-3-large"



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
