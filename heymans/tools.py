from .model import model
from . import config
from pathlib import Path
import logging
from langchain_core.documents import Document
import requests
logger = logging.getLogger('heymans')


class BaseTool:
    
    def __init__(self, heymans):
        self._heymans = heymans
        
    def use(self, message, args):
        pass
    
    
class SearchTool(BaseTool):
    
    def use(self, message, args):
        if len(self._heymans.documentation) == 0:
            logger.info('no topics were added, so skipping search')
            return
        if not isinstance(args, list):
            logger.warning(f'search tool expects a list, not {args}')
            args = [message]
        else:
            args = [message] + args
        self._heymans.documentation.search(args)


class TopicsTool(BaseTool):
    
    def use(self, message, args):
        if not isinstance(args, list):
            logger.warning('topics tool expects a list, not {args}')
            return
        for topic in args:
            if topic not in config.topic_sources:
                logger.warning(f'unknown topic: {topic}')
                continue
            logger.info(f'appending doc for topic: {topic}')
            doc = Document(
                page_content=Path(config.topic_sources[topic]).read_text())
            doc.metadata['important'] = True
            self._heymans.documentation.append(doc)


class CodeInterpreterTool(BaseTool):
    
    def use(self, message, args):
        if not isinstance(args, dict):
            logger.warning('code-interpreter tool expects a dict, not {args}')
            return
        language = args.get('language', 'python').lower()
        code = args.get('code', '')
        if not language or not code:
            return
        result = self._execute(language, code)
        result_msg = f'Result:\n```\n{result}\n```'
        self._heymans.reply_extras.append(result_msg)
        self._heymans.send_feedback_message(result_msg)

    def _execute(self, language, script):
        url = "https://emkc.org/api/v2/piston/execute"
        language_versions = {'python': '3.10', 'r': '4.1.1'}
        language_files = {'python': 'main.py', 'r': 'main.R'}
        data = {
            "language": "python",
            "version": language_versions[language],
            "files": [{"name": language_files[language], "content": script}],
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
            return result
        logger.error(f"Error: {response.status_code} with message: {response.content}")
        return 'Failed to execute code'
