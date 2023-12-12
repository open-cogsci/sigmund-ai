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
    
    def __init__(self, heymans):
        self.json_pattern = re.compile(self.json_pattern,
                                       re.VERBOSE | re.DOTALL)
        self._heymans = heymans
        
    def use(self, message):
        pass
    
    
    def run(self, message):
        if self.json_pattern is None:
            logger.warning(f'no JSON pattern or key defined for {self}')
            return
        spans = []
        for match in self.json_pattern.finditer(message):
            logger.info(f'executing tool {self}')
            args = {self.as_json_value(key) : self.as_json_value(val)
                    for key, val in match.groupdict().items()}
            self.use(message, **args)
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
        return message
        
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
            return
        self._heymans.documentation.search(queries)


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


class CodeInterpreterTool(BaseTool):
    
    json_pattern = r"""
\s*"execute_code"\s*:\s*\{
\s*"language"\s*:\s*"(?P<language>.+?)"
\s*,\s*"code"\s*:\s*"(?P<code>.+?)"
\s*\}
"""
    
    def use(self, message, language, code):
        logger.info(f'executing {language} code: {code}')
        url = "https://emkc.org/api/v2/piston/execute"
        language_versions = {'python': '3.10', 'r': '4.1.1'}
        language_files = {'python': 'main.py', 'r': 'main.R'}
        data = {
            "language": "python",
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
            result_msg = f'Result:\n```\n{result}\n```'
            self._heymans.reply_extras.append(result_msg)
            self._heymans.send_feedback_message(result_msg)
            return result
        logger.error(f"Error: {response.status_code} with message: {response.content}")
        return 'Failed to execute code'
