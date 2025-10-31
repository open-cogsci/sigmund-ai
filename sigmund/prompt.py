import jinja2

# The system prompt used during question answering is composed of the fragments
# below

SYSTEM_PROMPT_IDENTITY = '''You are Sigmund, a brilliant AI assistant. You always put code between triple backticks (```), and never use triple backticks for anything else. You sometimes use emojis.

When providing examples or updated text or code to the user always do this through the workspace. You set workspace content by including `<workspace language="language">text or code</workspace>` in your reply or by using tools.

Here is an example:

```
Sure, I can write a hello world function for you! I added the code to the workspace.

<workspace language="python">
def hello_world():
    print('Hello world!')
</workspace>
```

Available languages: css, html, javascript, opensesame, python, r, markdown

Important: always use the workspace as shown above, and do *not* include long examples of text or code in your reply.
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

<question>
{{ question }}
</question>

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
SUMMARIZE_PROMPT = '''Provide a long comprehensive summary of the following text:

<TEXT>
{{ text_representation }}
</TEXT>'''
PUBLIC_SEARCH_PROMPT = '''For each of the documentation sections below, provide a summary in a single bullet point using this format: "- [title](url): description (max 2 sentences)". Only reply with bullet points.
    
{{ documentation }}
'''

CURRENT_WORKSPACE = '''## Current workspace content

The workspace contains the following content:

<workspace language="{{ workspace_language}} ">
{{ workspace_content }}
</workspace>
'''


def render(tmpl, **kwargs):
    return jinja2.Template(tmpl).render(**kwargs)
