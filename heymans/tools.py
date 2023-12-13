from .model import model
from . import config
from pathlib import Path
import logging
import re
import json
from langchain_core.documents import Document
import requests
logger = logging.getLogger('heymans')


class BaseTool:
    
    json_pattern = None
    prompt = None
    
    def __init__(self, heymans):
        self.json_pattern = re.compile(self.json_pattern,
                                       re.VERBOSE | re.DOTALL)
        self._heymans = heymans
        
    def use(self, message: str) -> tuple[str | None, bool]:
        """Should be implemented in a tool with additional arguments that
        match the names of the fields from the json_pattern. 
        """
        raise NotImplementedError()
    
    def run(self, message: str) -> tuple[str, list, bool]:
        """Takes a message and uses the tool if the messages contains relevant
        JSON instructions. Returns the updated message, which can be changed by
        the tool notably by string the tool JSON instructions, a list of result
        strings, and a boolean indicating whether the model should reply to the
        result.
        
        Since there can be multiple instructions for one tool in a single
        message, the result is a list, rather than a single string.
        """
        spans = []
        results = []
        needs_reply = []
        for match in self.json_pattern.finditer(message):
            logger.info(f'executing tool {self}')
            args = {self.as_json_value(key) : self.as_json_value(val)
                    for key, val in match.groupdict().items()}
            match_result, match_needs_reply = self.use(message, **args)
            if match_result is not None:
                results.append(match_result)
            needs_reply.append(match_needs_reply)
            spans.append((match.start(), match.end()))
        # We now loop through all spans that correspond to JSON code blocks.
        # We find the first preceding { and succeeding } because the matching
        # only occurs within a block, and then we remove this. The goal of this
        # is to strip the JSON blocks from the reply.
        if spans:
            for span in spans[::-1]:
                for start in range(span[0], -1, -1):
                    ch = message[start]
                    if ch == '{':
                        break
                    if not ch.isspace():
                        start = None
                        break
                for end in range(span[1], len(message) + 1):
                    ch = message[end]
                    if ch == '}':
                        break
                    if not ch.isspace():
                        start = None
                        break
                if start and end:
                    message = message[:start] + message[end + 1:]
            # Remove empty JSON code blocks in case the JSON was embedded in
            # blocks
            message = re.sub(r'```json\s*```', '', message)
        return message, results, any(needs_reply)
        
    def as_json_value(self, s):
        try:
            return json.loads(s)
        except json.JSONDecodeError:
            return json.loads(f'"{s}"')


class SearchTool(BaseTool):
    
    json_pattern = r'"search"\s*:\s*(?P<queries>\[\s*"(?:[^"\\]|\\.)*"(?:\s*,\s*"(?:[^"\\]|\\.)*")*\s*\])'
    
    def use(self, message, queries):
        if len(self._heymans.documentation) == 0:
            logger.info('no topics were added, so skipping search')
        else:
            self._heymans.documentation.search(queries)
        return None, False


class TopicsTool(BaseTool):
    
    json_pattern = r'"topics"\s*:\s*(?P<topics>\[\s*"(?:[^"\\]|\\.)*"(?:\s*,\s*"(?:[^"\\]|\\.)*")*\s*\])'
    
    def use(self, message, topics):
        for topic in topics:
            if topic not in config.topic_sources:
                logger.warning(f'unknown topic: {topic}')
                continue
            logger.info(f'appending doc for topic: {topic}')
            doc = Document(
                page_content=Path(config.topic_sources[topic]).read_text())
            doc.metadata['important'] = True
            self._heymans.documentation.append(doc)
        return None, False


class CodeInterpreterTool(BaseTool):
    
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
