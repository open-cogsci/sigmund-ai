from .model import model
from . import config
from pathlib import Path
import logging
logger = logging.getLogger('heymans')


class BaseTool:
    
    def __init__(self, heymans):
        self._heymans = heymans
        
    def use(self, message, args):
        pass
    
    
class SearchTool(BaseTool):
    
    def use(self, message, args):
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
            self._heymans.documentation.append(
                Path(config.topic_sources[topic]).read_text())
