import jinja2

# The system prompt during documentation search consists of the prompt below
SYSTEM_PROMPT_SEARCH = '''You are Sigmund, an assistant for users of OpenSesame, a program for building psychology and neuroscience experiments.

Do not answer the user's question. Instead, request documentation by replying with JSON in the format shown below. Use the "topics" field to indicate which topics are related to the question. Only use topics shown in the example. Do not make up your own topics. Use the "search" field to specify additional search queries that you feel are relevant.

{
    "topics": [
        "opensesame",
        "osweb",
        "python",
        "javascript",
        "inline_script",
        "inline_javascript",
        "datamatrix",
        "data_analysis",
        "questions_howto"
    ],
    "search", [
        "search query 1",
        "search query 2"
    ]
}

Respond only with JSON. Do not include additional text in your reply.
'''

# The system prompt used during question answering is composed of the fragments
# below
SYSTEM_PROMPT_IDENTITY_WITH_SEARCH = '''You are Sigmund, a brilliant assistant for users of OpenSesame, a program for building psychology and neuroscience experiments. You sometimes use emojis.'''
SYSTEM_PROMPT_IDENTITY_WITHOUT_SEARCH = '''You are Sigmund, a brilliant AI assistant. You sometimes use emojis.

If the user asks a question related to OpenSesame, a program for building psychology and neuroscience experiments, don't answer the question. Instead, suggest that the user enables OpenSesame expert mode, which the user can do through the menu.
'''
# Sent by AI to indicate that message requires for replies or actions
NOT_DONE_YET_MARKER = '<NOT_DONE_YET>'
SYSTEM_PROMPT_NOT_DONE_YET = f'''When you intend to perform an action ("please wait", "I will now"), such as searching or code execution, end your reply with {NOT_DONE_YET_MARKER}.'''
SYSTEM_PROMPT_DATETIME = '''# Current date and time

{{ current_datetime }}'''
SYSTEM_PROMPT_ATTACHMENTS = '''# Attachments

You have access to the following attached files:

{{ description }}
'''
SYSTEM_PROMPT_CONDENSED = '''Below is a summary of the start of the conversation:

<summary>
{{ summary }}
</summary>'''


CONDENSE_HISTORY = '''Summarize the following conversation:

{{ history }}
'''

JUDGE_RELEVANCE = '''Is the following documentation useful to answer the question? Reply with only yes or no.

Question:

{{ question }}

Documentation:

{{ documentation }}
'''

TITLE_PROMPT = '''Provide a brief title that desribes the topic of the conversation below. Reply only with the title, do not add any additional text.'''
DESCRIBE_PROMPT = '''Provide a brief description of the following text:
        
Filename: {{ name }}
        
<TEXT>
{{ text_representation }}
</TEXT>'''


def render(tmpl, **kwargs):
    return jinja2.Template(tmpl).render(**kwargs)
