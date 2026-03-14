from .expensive_test_utils import BaseExpensiveTest
from sigmund import prompt

# This is a conversation that Haiku struggles with to give a title to
title_prompt = [{'content': prompt.TITLE_PROMPT,
  'role': 'system'},
 {'content': "Here's a list of prompts. Can you explain to me how these "
             'prompts relate to each other?',
  'role': 'user'},
 {'content': '<div '
             'class="thinking_block_signature">ErUJCkYICxgCKkA7JQmp9eYL1HbqnPW3eYRyyznYpqC+4SdcQnPLwKJng0tuiBwHBHVQ8jOD8EKkcTxvFp0EJlMfd84AYBSSVkAAEgyTjNeqnpTpKFVfx2gaDAz9N6winnLrVKoHlCIwX/XtGfU+e3ASOOJzu5iXk8sxatsKFHZTOgVDPYfRFLHtsmGB9wcKTGB9PHLCtKKtKpwIbqS798lNGaao2w+y0t/e6OTp9RVaXhmPaW6vM56nhynl+WazOEVCiyqA2FMFHT9ITFgMxRuE46C72uAGBjduv+VF60re+FA5pW56ISYVpzayOREiRVAL4PD1rRJGdPv7bwUux2gQ+aHzz71kT115vFVhYLHfZXD/386O4Wl0ZPguwrnKVYWpzoNrT43fvkX47knCakq81ytIo6guBPVt8PpZMCaHJKY1JEm+SZaLVP1Qkw+2miYF0AnTVgjFUml0/4/HYUXNLjjfQnTnPpAvK5Nh59QV9Qig0e993WBAFancTnkl9zhsG60+s0nXMKcsr79xo5LmsmwTt/pcuzirH8yIZO5ggcJc+NAlQay5lJc2caSTegpc+UrDSar6VFTp2ViLIZI5/8poT0iDoN2zTJZDLWuJxqEnKkOa/Vw8EbTJGag7RJTTT6DH/ddzUNUhbjOYOqPMo/U9ClK8yIW/kLN/AEnWFFZgphXsGpErkU5cPXOe+F+fomQBaBcd0XzMVKGz/pxd8UdE5iwJb7465Ltw3QU1KqIe58zTvfzTgur/sotnMCpFtG4IZU7ylgs2g792nItdBkI39WfVtREQq9cmf9Gkjd94XfL64gHhPcvICSmuhRTZQHS2jRhapkFKXqjFbB3RieDec/eDYWrfJWXq7sZriB5M0i+YajtJkFJzBrz8G5OEaLOFaMcjOYpm8Niv4VBM2iKsXmucxbJat7RSEBaWn4xESPQ40Z1StKhRIrpFJq5QVu3yP8u33Ay3kvaXJHZ0btLV6o4EH9yTdVNDbyoLyzV8NPoHqKh/7e0EbRtALKOQcXl3JYLhDU259K4O1bUHBn5n/gHO0nGZYtLEIyFn9z5Upq13K9lhxmRn9o9GRWg5Tx9S1nq1f79csogBlX0OpMwAh45S1J4cxdCQOV4jbfai3jrnwFZLnR1zC1aodSEleXQtMELII2IavKY+juiL8fydFOViyyMbIznrUpoaNOcmLfxAteXy9p2JpsRnswbeneCCBHzAAqMJd6TjZGVWIOjN9wKFByMEfuQf37wDXm1m/hOwYImyJkFJRw+M6+a2iibPBL614Kw1GU5sND1L/QCHU9S/PN5icLPN2KuIV47Gy38YJjiIKJq+OH7VD7VLwBVko2ryGoDjEhJNWqwt0xF0StSm1LhfsvbWo4rDG+NgTk/UcOXp6DiqcrXvQTUeN5+qIUKYhad/HdD3TLFz1Y3vZljOw2MbFpQ17YqJp4kRY3vQpmi3fnWtrJFKZDUbTOC8m5Tb1FXTh1kbLzjzVNVgoG3apSdZGEofr31wN8XKx+DHxq9w0r1M3DIeLYhiW77TdasTj2tX4poyh4arXnonykTZKuMudM98PH/ZJCfxNI7dp9uot7iH6DBc7Ski+m8DKswYAQ==</div><div '
             'class="thinking_block_content">The user wants me to explain how '
             'the prompts in the file relate to each other. Let me analyze the '
             'prompts and their relationships.\n'
             '\n'
             '1. **SYSTEM_PROMPT_IDENTITY** - The core identity/persona prompt '
             'for Sigmund\n'
             '2. **SYSTEM_PROMPT_CONDENSED** - Used to inject a summary of '
             'earlier conversation history\n'
             '3. **SYSTEM_PROMPT_NOTES** - Used to inject persistent notes '
             'into the system prompt\n'
             '4. **CONDENSE_HISTORY** - Used to ask the model to summarize '
             'conversation history (for condensing)\n'
             '5. **JUDGE_RELEVANCE** - Used to ask the model whether a '
             'document is relevant to a question (RAG filtering)\n'
             '\n'
             '\n'
             '6. **TITLE_PROMPT** - Used to generate a title for a '
             'conversation\n'
             '7. **DESCRIBE_PROMPT** - Used to generate a brief description of '
             'a document/file\n'
             '8. **SUMMARIZE_PROMPT** - Used to generate a long summary of a '
             'document/file\n'
             '9. **PUBLIC_SEARCH_PROMPT** - Used to format documentation '
             'search results into bullet points\n'
             '10. **CURRENT_WORKSPACE** - Used to inject current workspace '
             'content into the system prompt\n'
             '\n'
             'The first five prompts handle the core system behavior and '
             'conversation management, while the remaining five are utility '
             'prompts for generating metadata and formatting content. The '
             "system prompts work together to maintain Sigmund's identity "
             'while adapting to conversation context, while the utility '
             'prompts support document processing and search '
             'functionality.</div>\n'
             "Sure! Here's an overview of how the prompts relate to each other "
             '🧠\n'
             '\n'
             'The prompts fall into roughly **four categories**:\n'
             '\n'
             '---\n'
             '\n'
             '### 🤖 System prompt (assembled together)\n'
             'These three prompts are combined to form the system prompt that '
             "guides Sigmund's behavior during a conversation:\n"
             '\n'
             '- **`SYSTEM_PROMPT_IDENTITY`** — The core persona: who Sigmund '
             'is and how it should behave (e.g. use workspaces, use backticks '
             'for code).\n'
             '- **`SYSTEM_PROMPT_CONDENSED`** — Injected when the conversation '
             'history gets long. It uses `CONDENSE_HISTORY` (see below) to '
             'first *produce* the summary, and then includes that summary in '
             'the system prompt.\n'
             '- **`SYSTEM_PROMPT_NOTES`** — Injected when persistent notes '
             'exist for the conversation. Together with '
             '`SYSTEM_PROMPT_CONDENSED`, it keeps the context window '
             'manageable.\n'
             '- **`CURRENT_WORKSPACE`** — Also injected into the system prompt '
             'to tell Sigmund what is currently in the workspace.\n'
             '\n'
             '---\n'
             '\n'
             '### 🔁 Conversation management\n'
             '- **`CONDENSE_HISTORY`** — A utility prompt sent to the model to '
             '*compress* old conversation history into a summary. The result '
             'feeds into `SYSTEM_PROMPT_CONDENSED`.\n'
             '\n'
             '---\n'
             '\n'
             '### 📚 Retrieval-Augmented Generation (RAG)\n'
             'These prompts support document search and retrieval:\n'
             '\n'
             '- **`JUDGE_RELEVANCE`** — Sent to the model to filter out '
             'irrelevant documents before including them in the context. '
             'Returns a simple `{"relevant": true/false}` JSON.\n'
             '- **`PUBLIC_SEARCH_PROMPT`** — Takes relevant documentation '
             'sections and formats them as bullet-point summaries for the '
             'user.\n'
             '- **`DESCRIBE_PROMPT`** / **`SUMMARIZE_PROMPT`** — Used to '
             'pre-process documents: generating short descriptions or long '
             'summaries that can be used for indexing or retrieval.\n'
             '\n'
             '---\n'
             '\n'
             '### 🏷️ Housekeeping\n'
             '- **`TITLE_PROMPT`** — A standalone prompt used to auto-generate '
             'a short title for a conversation, likely for display in a chat '
             'history UI.\n'
             '\n'
             '---\n'
             '\n'
             'In short, `SYSTEM_PROMPT_IDENTITY` is the *foundation*, while '
             'the other system prompt fragments are *dynamically injected* '
             'based on context. The remaining prompts are *utility prompts* '
             'used behind the scenes to manage knowledge and conversation '
             'state.',
  'role': 'assistant'},
 {'content': prompt.TITLE_PROMPT,
  'role': 'user'}]


class TestCondenseMessageHistory(BaseExpensiveTest):
    
    def _test_tool(self):
        
        suggested_title = self.sigmund.condense_model.predict(title_prompt)
        print(suggested_title)
        assert len(suggested_title.splitlines()) == 1
