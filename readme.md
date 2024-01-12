# Sigmund AI

Copyright 2023-2024 Sebastiaan Mathôt

This is a working prototype of <https://sigmundai.eu>, an AI-based chatbot that provides sensible answers based on documentation.

Features:

- Privacy: all messages are encrypted so that no-one can listen in on your conversation
- Knowledge: access to OpenSesame and DataMatrix documentation 
- Continuous conversation: conversations are summarized when they become too long to fit into the prompt
- Code execution: basic code-execution abilities in Python and R
- Google Scholar search: ability to search for articles on Google Scholar

Sigmund uses OpenAI (gpt3.5, gpt4) and/ or Anthropic (claude 2.1) chat models and requires API keys.

**Note: for the Q&A and practice bot for teaching (Heymans AI tutor), checkout `release/0.3.0`. The current codebase focuses on a conversational chatbot for user support, and has been renamed to Sigmund.**

## Configuration

See `heymans/config.py` for configuration instructions.


## Running

First, you need to create a library index:

```
python index_library.py
```


Next, you can start the app in development mode through:

```
python app.py
```

And access it (by default) through:

```
https://127.0.0.1:5000/
```


## Dependencies

See `pyproject.toml`.


## License

Sigmund is distributed under the terms of the GNU General Public License 3. The full license should be included in the file `COPYING`, or can be obtained from:

- <http://www.gnu.org/licenses/gpl.txt>
