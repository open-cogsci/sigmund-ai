# Sigmund AI

Copyright 2023-2025 Sebastiaan Mathôt

![](artwork/sigmund-avatar-small.png)

A Python library and web app for an LLM-based chatbot:

Features:

- __Privacy__: all messages and uploaded attachments are encrypted so that no-one can listen in on your conversation
- __Expert knowledge__: access to documentation 
- __Continuous conversation__: conversations are summarized when they become too long to fit into the prompt
- __Tool use__ (in research-assistant mode):
    - __Code execution__: ability to execute Python and R code
    - __Google Scholar search__: ability to search for articles on Google Scholar
    - __Image generation__: ability to generate images
- __Integrations__
    - __Python__: [connect to JupyterLab, Notebook, Spyder or Rapunzel](https://github.com/open-cogsci/jupyter-extension-sigmund)
    - __OpenSesame__: [directly integrate with OpenSesame](https://osdoc.cogsci.nl/4.0/manual/sigmund/)
    - __Sigmund Analyst__: [directly integrate with Sigmund Analyst for data analysis](https://github.com/open-cogsci/sigmund-analyst)
    
Sigmund is not a large language model itself. Rather it uses third-party models. Currently, models from [OpenAI](https://openai.com), [Anthropic](https://www.anthropic.com/), and [Mistral](https://mistral.ai/) are supported. API keys from these respective providers are required.


[output2.webm](https://github.com/user-attachments/assets/905233c3-5980-45f5-b8fb-dc769b4c3526)


## Configuration

See `sigmund/config.py` for configuration instructions.


## Dependencies

For Python dependencies, see `pyproject.toml`. In addition to these, `pandoc` is required for the ability to read attachments, and a local `redis` server needs to run for persistent data between sessions.


## Running (development)

Download the source code, and copy `.env.example` to `.env`. Edit this file to specify at least the API keys, and depending on the functionality that you want activate, possibly also other variables. The only variable that is strictly required is the OpenAI API key, because OpenAI is used to create text embeddings, even when a different model is used for the conversation.

Next, install the dependencies, build the documentation index, and launch the app!

```
pip install .               # install dependencies
python index_library.py     # build library (documentation) index
python app.py               # start the app
```

Next, access the app (by default) through:

```
http://127.0.0.1:5000/
```


## Running (production)

In production, the server is generally not run by directly calling the app. There are many ways to run a Flask app in production. One way is to use gunicorn to start the app, and then use an nginx web server as a proxy that reroutes requests to the app. When taking this route, make sure to set up nginx with a large `client_max_body_size` (to allow attachment uploading) and disable `proxy_cache` and `proxy_buffering` (to allow status messages to be streamed while Sigmund is answering).


## License

Sigmund is distributed under the terms of the GNU General Public License 3. The full license should be included in the file `COPYING`, or can be obtained from:

- <http://www.gnu.org/licenses/gpl.txt>
