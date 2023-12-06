from .model import model
from . import config
from pathlib import Path
import logging
from langchain_core.documents import Document
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
