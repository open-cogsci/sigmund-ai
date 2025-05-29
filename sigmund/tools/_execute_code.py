from . import BaseTool
import logging
import requests
logger = logging.getLogger('sigmund')


class execute_code(BaseTool):
    """Add Python or R code to the workspace and execute it. Do not use this tool unless code should actually be executed. When executing Python, you can only use modules from the Python standard library."""
    
    arguments = {
        'language': {
            'type': 'string',
            'description': 'The programming language to use',
            'enum': ['r', 'python']
        },
        'code': {
            'type': 'string',
            'description': 'The code to execute. Use print() to print to the standard output.'
        }
    }
    required_arguments = ['language', 'code']
    
    def __call__(self, language, code):
        logger.info(f'executing {language} code: {code}')
        url = "https://emkc.org/api/v2/piston/execute"
        language_aliases = {'python': 'python',
                            'r': 'r'}
        language = language_aliases[language.lower()]
        language_versions = {'python': '3.10', 'r': '4.1.1'}
        language_files = {'python': 'main.py', 'r': 'main.R'}
        data = {
            "language": language,
            "version": language_versions[language],
            "files": [{"name": language_files[language], "content": code}],
            "stdin": "",
            "args": [],
            "compile_timeout": 10000,
            "run_timeout": 3000,
            "compile_memory_limit": -1,
            "run_memory_limit": -1
        }
        response = requests.post(url, json=data)
        if response.status_code == 200:
            response_data = response.json()
            result = response_data.get("run", {}).get("output", "").strip()
            logger.info(f'result: {result}')
            message = f'''I added code to the workspace, executed it, and received the following output:

```
{result}
```

<workspace language="{language}">
{code}
</workspace>
'''
            return message, result, language, True
        logger.error(f"Error: {response.status_code} with message: {response.content}")
        return 'Failed to execute code', code, language, True
