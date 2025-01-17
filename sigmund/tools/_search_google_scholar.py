from . import BaseTool
import logging
import json
from scholarly import scholarly
logger = logging.getLogger('sigmund')


class search_google_scholar(BaseTool):
    """Search Google Scholar for scientific articles. An overview of metadata (abstracts, authors, titles, etc.) of matching articles will be returned."""
    
    arguments = {
        "queries": {
            "type": "array",
            "items": {
                "type": "string"
            },
            "description": "A list of search queries",
        }
    }
    required_arguments = ["queries"]
    
    def __call__(self, queries):
        results = []
        for query in queries:
            for i, result in enumerate(scholarly.search_pubs(query)):
                logger.info(f'appending doc for google scholar search: {query}')
                info = result['bib']
                if 'eprint_url' in result:
                    info['fulltext_url'] = result['eprint_url']
                results.append(info)
                if i >= 3:
                    break
        message = f'I found {len(results)} articles and added them to the workspace.'
        results = json.dumps(results, indent='  ')
        return message, results, True
