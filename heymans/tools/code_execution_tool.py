from . import BaseTool
import logging
import requests
logger = logging.getLogger('heymans')


class CodeExecutionTool(BaseTool):
    
    json_pattern = r"""
\s*"execute_code"\s*:\s*\{
\s*"language"\s*:\s*"(?P<language>.+?)"
\s*,\s*"code"\s*:\s*"(?P<code>.+?)"
\s*\}
"""
    prompt = '''# Code execution

You are also a brilliant programmer. To execute Python and R code, use JSON in the format below. You will receive the output in the next message. Example code included elsewhere in your reply will not be executed. Never execute OpenSesame inline scripts.

{
    "execute_code": {
        "language": "python",
        "code": "print('your code here')"
    }
}'''
    
    def use(self, message, language, code):
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
            result = response_data.get("run", {}).get("output", "")
            logger.info(f'result: {result}')
            result_msg = f'''I executed the following code:

```{language}
{code}
```

And got the following output:

```
{result}
```'''
            return result_msg, True
        logger.error(f"Error: {response.status_code} with message: {response.content}")
        return 'Failed to execute code', True
