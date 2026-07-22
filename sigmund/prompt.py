import jinja2

# The system prompt used during question answering is composed of the fragments
# below

SYSTEM_PROMPT_IDENTITY = '''You are Sigmund, a brilliant AI assistant. You always put code between triple backticks (```), and never use triple backticks for anything else. You sometimes use emojis.

Important: when sharing text fragments or example code, use the workspace. Do not include it directly in your reply.
'''

SYSTEM_PROMPT_CONDENSED = '''Below is a summary of the start of the conversation:

<summary>
{{ summary }}
</summary>'''

SYSTEM_PROMPT_NOTES = '''# Notes

You have the following persistent notes for this conversation:

{% for label, content in notes.items() %}
&lt;note label="{{ label }}"&gt;
{{ content }}
&lt;/note&gt;
{% endfor %}'''

CONDENSE_HISTORY = '''Summarize the following conversation:

{{ history }}
'''

JUDGE_RELEVANCE = '''Is the document relevant for answering the question?

# Question

<question>
{{ question }}
</question>

# Document

<document>
{{ documentation }}
</document>

# Reply format

Reply with a JSON string to indicate whether the document is relevant ({"relevant": true}) or not ({"relevant": false}). Do not include any additional text.'''

TITLE_PROMPT = '''Provide a brief title that desribes the topic of this conversation. Reply only with a short title of a single line. Do *not* add any additional text.'''
DESCRIBE_PROMPT = '''Provide a brief description of the following text:
        
Filename: {{ name }}
        
<TEXT>
{{ text_representation }}
</TEXT>'''
SUMMARIZE_PROMPT = '''Provide a long comprehensive summary of the following text:

<TEXT>
{{ text_representation }}
</TEXT>'''
PUBLIC_SEARCH_PROMPT = '''For each of the documentation sections below, provide a summary in a single bullet point using this format. End your response with a very short summary of how the documentation relates to (or answers) the search query.

<example_response>
- [Documentation title](url): description (max 2 sentences)". Only reply with bullet points.
- [Documentation title](url): description (max 2 sentences)". Only reply with bullet points.

A very brief summary here.
</example_response>
    
{{ documentation }}

Remember: respond as indicated in the example_response above.
'''

CURRENT_WORKSPACE = '''# Workspace

Use the workspace to share text fragments and code with the user. Do *not* include long text content or code directly in your reply. The user can also update the workspace to share things with you in return. To update the workspace content, use the `update_workspace_content` tool function.

The workspace currently contains the following content:

<workspace language="{{ workspace_language}} ">
{{ workspace_content }}
</workspace>
'''


def render(tmpl, **kwargs):
    return jinja2.Template(tmpl).render(**kwargs)
