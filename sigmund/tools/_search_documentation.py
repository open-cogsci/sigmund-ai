from . import BaseTool
from .. import config
import logging
from pathlib import Path
from langchain_core.documents import Document
logger = logging.getLogger('sigmund')


class search_documentation(BaseTool):
    """Search the documentation based on topics and search queries"""
    
    arguments = {
        "primary_topic": {
            "type": "string",
            "description": "The primary topic of the question"
        },
        "secondary_topic": {
            "type": "string",
            "description": "The secondary topic of the question"
        },
        "queries": {
            "type": "array",
            "items": {
                "type": "string"
            },
            "description": "A list of queries to search the documentation",
        }
    }
    required_arguments = ['primary_topic', 'queries']
    
    @property
    def tool_spec(self):
        topics = list(config.topic_sources.keys())
        arguments = self.arguments.copy()
        arguments['primary_topic']['enum'] = topics
        arguments['secondary_topic']['enum'] = topics
        return {
            "name": self.__class__.__name__,
            "description": self.__doc__,
            "parameters": {
                "type": "object",
                "properties": arguments,
                "required": self.required_arguments,
            }
        }    
    
    def __call__(self, primary_topic, queries, secondary_topic=None):
        topics = [primary_topic]
        if secondary_topic:
            topics.append(secondary_topic)
        for topic in topics:
            if topic not in config.topic_sources:
                logger.warning(f'unknown topic: {topic}')
                continue
            logger.info(f'appending doc for topic: {topic}')
            doc = Document(
                page_content=Path(config.topic_sources[topic]).read_text())
            doc.metadata['important'] = True
            self._sigmund.documentation.append(doc)
        self._sigmund.documentation.search(queries)
        return 'Searching documentation ...', '', False
