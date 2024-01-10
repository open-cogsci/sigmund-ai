from . import BaseTool
import logging
import json
from scholarly import scholarly
logger = logging.getLogger('heymans')


class GoogleScholarTool(BaseTool):
    
    json_pattern = r'"search_google_scholar"\s*:\s*(?P<queries>\[\s*"(?:[^"\\]|\\.)*"(?:\s*,\s*"(?:[^"\\]|\\.)*")*\s*\])'
    prompt = '''# Search Google Scholar

You are also a brilliant researcher. To search for articles on Google Scholar, use JSON in the format below. You will receive the output in the next message.

{
    "search_google_scholar": [
        "search query 1",
        "search query 2"
    ]
}'''
    
    def use(self, message, queries):
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
        return f'''I found {len(results)} articles. I am going to read them now.

<div class='json-references'>
{json.dumps(results)}
</div> <TRANSIENT>''', True
