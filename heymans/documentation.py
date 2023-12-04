import asyncio
from pathlib import Path
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS
import logging
from . import config
from . import prompt
logger = logging.getLogger('heymans')


class Documentation:
    
    def __init__(self, heymans, sources=[]):
        self._heymans = heymans
        self._documents = []
        self._sources = sources
        
    def __str__(self):
        return '\n\n'.join(
            f"<document>{doc}</document>\n" for doc in self._documents)
        
    def __iter__(self):
        return (doc for doc in self._documents)
    
    def __len__(self):
        return sum(len(doc) for doc in self._documents)
        
    def __contains__(self, doc):
        return doc in self._documents
    
    def append(self, doc):
        if doc not in self._documents:
            self._documents.append(doc)
            
    def strip_irrelevant(self, question):
        prompts = [prompt.render(prompt.JUDGE_RELEVANCE, documentation=doc,
                                 question=question)
                   for doc in self]
        replies = [self._heymans.condense_model.predict(prompt)
                   for prompt in prompts]
        relevant = []
        for reply, doc in zip(replies, self):
            if not reply.lower().startswith('no'):
                relevant.append(doc)
            else:
                logger.info(f'stripping irrelevant documentation')
        self._documents = relevant
    
    def clear(self):
        logger.info('clearing documentation')
        self._documents = []
        
    def search(self, queries):
        for source in self._sources:
            for doc in source.search(queries):
                if doc not in self._documents:
                    self._documents.append(doc)
        

class BaseDocumentationSource:
    
    def __init__(self, heymans):
        self._heymans = heymans
    
    def search(self, queries):
        pass
    
    
class FAISSDocumentationSource(BaseDocumentationSource):
    
    def __init__(self, heymans):
        super().__init__(heymans)
        self._embeddings_model = OpenAIEmbeddings(
            openai_api_key=config.openai_api_key)
        logger.info('reading FAISS documentation cache')
        self._db = FAISS.load_local(Path('.db.cache'), self._embeddings_model)
        self._retriever = self._db.as_retriever()
    
    def search(self, queries):
        docs = []
        for query in queries:
            logger.info(f'retrieving from FAISS: {query}')
            for doc in self._retriever.invoke(query):
                if doc.page_content not in self._heymans.documentation and \
                        doc.page_content not in docs:
                    logger.info(
                        f'Retrieving {doc.metadata["url"]} (length={len(doc.page_content)})')
                    docs.append(doc.page_content)
                    break
        return docs
    
    
class OpenSesameDocumentationSource(BaseDocumentationSource):
    
    def __init__(self, heymans):
        super().__init__(heymans)
        self._py_doc = Path('sources/py/opensesame.py').read_text()
        self._js_doc = Path('sources/js/opensesame.js').read_text()
        self._py_keywords = ['opensesame', 'inline_script', 'python', 'canvas',
            'keyboard', 'mouse', 'sampler', 'synth', 'sequence', 'loop',
            'variable', 'experiment', 'stimulus', 'display', 'task',
            'paradigm', 'run if', 'run-if', 'show if', 'show-if']
        self._js_keywords = ['osweb', 'javascript', 'online', 'browser',
            'inline_javascript', 'firefox', 'safari']

    def search(self, queries):
        queries = ''.join(queries).lower()
        if any(keyword in queries 
               for keyword in self._py_keywords + self._js_keywords):
            if any(keyword in queries for keyword in self._js_keywords):
                logger.info('retrieving general osweb documentation')
                return [self._js_doc]
            logger.info('retrieving general opensesame documentation')
            return [self._py_doc]
        return []
