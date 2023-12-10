# Heymans/ Sigmund AI tutor

Copyright 2023 Sebastiaan Mathôt


This is a working prototype of an AI-based chatbot that provides sensible answers based on documentation.

Features:

- Privacy: all messages are encrypted so that no-one can listen in on your conversation
- Knowledge: access to OpenSesame documentation 
- Cpntinuous conversation: the conversation is held in a continuous thread

Heymans uses OpenAI (gpt3.5, gpt4) and/ or Anthropic (claude 2.1) chat models and requires API keys.

**Note: for the Q&A and practice bot for teaching, checkout `release/0.3.0`. The current codebase focuses on a conversational chatbot for user support.**

## Configuration

See `heymans/config.py` for configutation instructions.


## Running


Once Heymans is properly configured, you can start the app in development mode through:

```
python app.py
```

Next open:

```
https://127.0.0.1:5000/
```


## Dependencies

- anthropic
- cryptography
- faiss (or faiss-cpu)
- flask
- flask-login
- flask-wtf
- jinja2
- jq
- langchain
- markdown
- openai
- pygments
- pypdf
- python
- tiktoken


## License

Heymans is distributed under the terms of the GNU General Public License 3. The full license should be included in the file `COPYING`, or can be obtained from:

- <http://www.gnu.org/licenses/gpl.txt>
