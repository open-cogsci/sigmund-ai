# Heymans AI tutor

Copyright 2023 Sebastiaan Mathôt

This is a working prototype of an AI-based tutor that asks open-ended questions to students based on sections from a textbook. The AI gives feedback until the student answers the question correctly. This is intended as formative testing.

Heymans uses OpenAI chat models and required an OpenAI API key.


## Installation

Download the source code and create a `config.py` in the main source folder (i.e. alongside `heymans.py`)"

```python
page_title = 'Heymans AI'
server_port = 5000
server_url = 'http://localhost:5000'
ai_name = 'Heymans'  # How the AI calls itself
max_chat_length = 20
# Default student identifiers
default_name = 'Anonymous Student'
default_student_nr = 'S12345678'
# Defines which courses exist and which chapters each course has
course_content = {
    'course_code_1': {
        'title': 'Course Title 1',
        'chapters': {
            '1': 'First Chapter',
            '2': 'Second Chapter'
        }
    },
    'course_code_2': {
        'title': 'Course Title 2',
        'chapters': {
            '1': 'First Chapter',
            '2': 'Second Chapter'
        }
    }
}
openai_api_key = 'your_openai_api_key_here'
model = 'gpt-4'  # 'dummy' for testing, 'gpt-3.5-turbo' for simpler model


def is_valid_student_nr(student_nr):
    """Takes a student number and returns True if it is valid."""
    return True
```

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

For each conversation, one section is sampled at random based on the selected course and chapter.

Next, start Heymans:

```
python heymans.py
```

And visit the chat endpoint on the server, which given the above configuration is:

```
https://localhost:5000/chat
```


## Dependencies

- python
- flask
- openai
- jinja2


## License

Heymans is distributed under the terms of the GNU General Public License 3. The full license should be included in the file `COPYING`, or can be obtained from:

- <http://www.gnu.org/licenses/gpl.txt>
