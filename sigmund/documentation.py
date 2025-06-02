import json
import logging
from .library import Library
from . import config
logger = logging.getLogger('sigmund')


class Documentation:
    
    def __init__(self, sigmund):
        self._sigmund = sigmund
        self._documents = []
        self.poor_match = False
        self._library = Library(
            persist_directory=config.search_persist_directory,
            embedding_provider=config.search_embedding_provider,
            embedding_model=config.search_embedding_model)
        self._collections = {
            c for c in config.search_collections
            if self._sigmund.database.get_setting(f'collection_{c}') == 'true'
        }
        logger.info(f'using collections: {self._collections}')
        
    @property
    def enabled(self):
        return self._collections
        
    def _doc_to_str(self, doc):
        s = '<document>\n'
        if doc.get('title'):
            s += f'# {doc["title"]}\n\n'
        if doc.get('url'):
            s += f'Source: {doc["url"]}\n\n'
        return s + doc['content'] + '\n</document>'
        
    def __str__(self):
        if not self._documents:
            return ''
        return '\n\n'.join(self._doc_to_str(doc) for doc in self._documents)
        
    def to_json(self):
        return json.dumps([{'page_content': doc['content'],
                            'url': doc.get('url')}
                           for doc in self])
        
    def __iter__(self):
        return (doc for doc in self._documents)
    
    def __len__(self):
        return sum(len(doc['content']) for doc in self._documents)
        
    def __contains__(self, doc):
        return doc in self._documents
    
    def prompt(self):        
        return f'''# Documentation

You have retrieved the following documentation to answer the user's question:

<documentation>
{str(self)}
</documentation>'''
    
    def append(self, doc):
        if any(doc['content'] == d['content'] for d in self):
            return
        self._documents.append(doc)        
    
    def clear(self):
        logger.info('clearing documentation')
        self._documents = []
        
    def search(self, query, fallback=False, foundation=True, howtos=True,
               max_distance=None, max_distance_fallback=None, k=None):
        """First, we separately search for regular and howto documents, because
        these tend not to be fairly comparable (howtos tend to always win).
        Finally, we insert foundation documents that match the topic of the
        search hits.
        """
        if not self._collections:
            logger.info('library search disabled')
            return
        if k is None:
            k = config.search_docs_max
        if max_distance is None:
            max_distance = config.search_max_distance
        if max_distance_fallback is None:
            max_distance_fallback = config.search_max_distance_fallback
        if fallback:
            max_distance = max_distance_fallback
        regular_results = self._library.search(
            query, foundation=False, howto=False, k=k,
            max_distance=max_distance, collection=self._collections)        
        logger.info(f'found {len(regular_results)} regular results')
        if howtos:
            howto_results = self._library.search(
                query, foundation=False, howto=True, k=k,
                max_distance=max_distance, collection=self._collections)
            logger.info(f'found {len(howto_results)} howto results')
        else:
            howto_results = []
        results = regular_results + howto_results
        if foundation:
            foundation_results = self._library.retrieve_foundation_documents(results)
            logger.info(f'found {len(foundation_results)} foundation documents')
        else:
            foundation_results = []
        self._documents = foundation_results + results
        if not fallback and not self._documents:
            self.poor_match = True
            logger.warning('no results found, retrying with higher threshold')
            self.search(query, fallback=True, foundation=foundation, 
                        howtos=howtos, max_distance=max_distance,
                        max_distance_fallback=max_distance_fallback, k=k)
