# Heymans AI tutor

Copyright 2023 Sebastiaan Mathôt

This is a working prototype of an AI-based tutor that offers two chat modes:

- In __practice__ mode, Heymans asks open-ended questions to students based on sections from a textbook. The AI gives feedback until the student answers the question correctly. This is intended as formative testing.
- In __Q&A__ mode, students can ask questions, which Heymans attempts to answer based on the sources in its library.

Heymans uses OpenAI chat models and requires an OpenAI API key.


## Configuring

Download the source code and create a `config.py` in the `heymans` package folder. See `config.example.py` for a commented example.


### Adding courses for practice mode

Next, for each chapter, organize `.txt` files with sections from that chapter in the following way:

```
sources/course_code_1/1/1.1.txt
sources/course_code_1/1/1.2.txt
sources/course_code_1/1/1.3.txt
...
sources/course_code_2/2/2.1.txt
sources/course_code_2/2/2.2.txt
sources/course_code_2/2/2.3.txt
```

Each course also needs a template for the system prompt, which contains general instructions for the model. This should be organized as follows:

```
sources/course_code_1/prompt_template.txt
```

The prompt template is a ninja2 template that contains various placeholders that will be filled in based on the configuration and user identity. See `prompt_template.example.txt` for an example.

In practice mode, for each conversation, one section is sampled at random based on the selected course and chapter.


### Adding PDF sources

You can add PDF sources to:

```
sources/pdf/
```

Each PDF source should have a human-readable name in the config file.


### Adding JSONL sources

You can also add `.jsonl` sources:

```
sources/jsonl/
```


## Running


Once Heymans is properly configured, you can start the app in development mode through:

```
python app.py
```

You can then open any of the end points:

```
https://127.0.0.1:5000/
https://127.0.0.1:5000/practice
https://127.0.0.1:5000/qa
https://127.0.0.1:5000/login
https://127.0.0.1:5000/logout
https://127.0.0.1:5000/library
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
