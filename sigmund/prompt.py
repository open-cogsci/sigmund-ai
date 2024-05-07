import jinja2

# The system prompt during documentation search consists of the prompt below
SYSTEM_PROMPT_SEARCH = '''Do not answer the user's question. Instead, use the search_documentation function tool to search for relevant documentation.'''

# The system prompt used during question answering is composed of the fragments
# below
SYSTEM_PROMPT_IDENTITY_WITH_SEARCH = '''You are Sigmund, a brilliant AI assistant for users of OpenSesame, a program for building psychology and neuroscience experiments. Your knowledge of OpenSesame is outdated. Therefore, strictly follow the documentation that is provided in the context between <documentation> tags. You sometimes use emojis.'''
SYSTEM_PROMPT_IDENTITY_WITHOUT_SEARCH = '''You are Sigmund, a brilliant AI assistant. You sometimes use emojis.'''
# Sent by AI to indicate that message requires for replies or actions
NOT_DONE_YET_MARKER = '<NOT_DONE_YET>'
SYSTEM_PROMPT_NOT_DONE_YET = f'''When you intend to perform an action ("please wait", "I will now"), such as searching or code execution, end your reply with {NOT_DONE_YET_MARKER}.'''
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

JUDGE_RELEVANCE = '''Is the document relevant for answering the question?

# Question

{{ question }}
"""

# Document

<document>
{{ documentation }}
</document>

# Reply format

Reply with a JSON string to indicate whether the document is relevant ({"relevant": true}) or not ({"relevant": false}). Do not include any additional text.'''

TITLE_PROMPT = '''Provide a brief title that desribes the topic of the conversation below. Reply only with the title, do not add any additional text.'''
DESCRIBE_PROMPT = '''Provide a brief description of the following text:
        
Filename: {{ name }}
        
<TEXT>
{{ text_representation }}
</TEXT>'''
PUBLIC_SEARCH_PROMPT = '''For each of the documentation sections below, provide a summary in a single bullet point using this format: "- [title](url): description (max 2 sentences)". Only reply with bullet points.
    
{{ documentation }}
'''


def render(tmpl, **kwargs):
    return jinja2.Template(tmpl).render(**kwargs)
