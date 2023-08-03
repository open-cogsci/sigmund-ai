# Appearance
page_title = 'Heymans AI'
ai_name = 'Heymans'
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
# Text messages on various pages
login_text = f'''Hi there, my name is { ai_name }, your friendly AI assistant. 
I always look things up in [my library](/library) to make sure that what I say
is correct.

Please log in.'''
qa_start_message = f'''Hi there, my name is { ai_name }, your friendly AI assistant. 
I always look things up in [my library](/library) to make sure that what I say
is correct.

Now shoot! What would you like to know?'''
library_text = '''
## Library

Your library sources here
'''
# Three example queries are selected and shown at random when the conversation
# starts in Q&A mode
example_queries = [
    'You could try this question',
    'Or maybe this question',
    'Or maybe even this one'
]
# Server configuration.
# The external server address, that is, the URL that users visit
server_url = 'http://yourwebsite.eu'
# The port at which the flask server is running internally. This can be
# different from the server URL if the app is running behind a proxy that
# redirects
flask_port = 5000
# The flask host arhument where all 0s means listen to all incoming addresses
flask_host = '0.0.0.0'
# The secret key is used for logging in. This should be a long and arbitrary
# string that is hard to guess. This should not be shared
flask_secret_key = 'your_secret_key'
# Determines whether the app by default goes to practice mode or qa mode
main_endpoint = 'qa'
# The number of documents that are indexed at once and the delay after each
# chunk. This is to avoid exceeded the rate limits of the OpenAI API
chunk_size = 100
chunk_throttle = .1
# The maximum nummber of messages in a chat and the maximum length of user
# messages
max_chat_length = 8
max_message_length = 1000
max_source_tokens = 6000
# The default student number and name for practice mode, and course content
# for practice mode
default_name = 'Anonymous Student'
default_student_nr = 'S12345678'
course_content = {
    'course_code_1': {
        'title': 'Course Title 1',
        'textbook': 'Book 1',
        'chapters': {
            '1': 'First Chapter',
            '2': 'Second Chapter'
        }
    },
    'course_code_2': {
        'title': 'Course Title 2',
        'textbook': 'Book 2',
        'chapters': {
            '1': 'First Chapter',
            '2': 'Second Chapter'
        }
    }
}
# Human-readable names for PDF sources
sources = {
    'Psychology_2e.pdf': 'OpenStax: Psychology (2nd edition)',
    'Anatomy_and_Physiology_2e.pdf':
        'OpenStax: Anatomy and Physiology (2nd edition)'
}
# OpenAI settings. Keep your key secret!
openai_api_key = 'sk-your-openai-api-key'
model = 'gpt-4'  # gpt-4, gpt-3.5-turbo, or dummy
# Google analytics script (optional)
analytics_script = ''


def clean_source(source):
    """Optionally cleans source documents before feeding them into the prompt.
    Practice mode only.
    """
    return source


def response_rewriter(text):
    """Optionally rewrites the AI response in case it contains predictable
    mistakes that can be easily fixed with a rewriter.
    """
    return text


def validate_user(user, password):
    """Checks the login credentials. Sigmund does not contain a system to
    manage users, so that should be connected here.
    """
    return True


def user_info(username):
    """Returns more information about a username. If a first_name is provide,
    then this is used in practice to refer to the user.
    """
    return {
        'username': username,
        'first_name': 'John',
        'last_name': 'Doe',
        'email': 'user@domain.com'
    }
