from . import BaseTool
import logging
logger = logging.getLogger('heymans')


class SearchTool(BaseTool):
    """Searches through the indexed documentation and inserts matching 
    fragments into the documentation object.
    """
    
    json_pattern = r'"search"\s*:\s*(?P<queries>\[\s*"(?:[^"\\]|\\.)*"(?:\s*,\s*"(?:[^"\\]|\\.)*")*\s*\])'
    
    def use(self, message, queries):
        if len(self._heymans.documentation) == 0:
            logger.info('no topics were added, so skipping search')
        else:
            self._heymans.documentation.search(queries)
        return None, False
