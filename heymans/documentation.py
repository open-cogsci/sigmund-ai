import json
from pathlib import Path
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
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
        if not self._documents:
            return ''
        return '\n\n'.join(
            f"<document>{doc.page_content}</document>" for doc in self._documents)
        
    def to_json(self):
        return json.dumps([{'page_content': doc.page_content,
                            'url': doc.metadata.get('url', None)}
                           for doc in self])
        
    def __iter__(self):
        return (doc for doc in self._documents)
    
    def __len__(self):
        return sum(len(doc.page_content) for doc in self._documents)
        
    def __contains__(self, doc):
        return doc in self._documents
    
    def prompt(self):
        if not self._documents:
            return None
        return f'''# Documentation

You have retrieved the following documentation to answer the user's question:

<documentation>
{str(self)}
</documentation>'''
    
    def append(self, doc):
        if any(doc.page_content == d.page_content for d in self):
            return
        self._documents.append(doc)
            
    def strip_irrelevant(self, question):
        important = [doc for doc in self
                     if doc.metadata.get('important', False)]
        optional = [doc for doc in self
                    if not doc.metadata.get('important', False)]
        prompts = [prompt.render(prompt.JUDGE_RELEVANCE,
                                 documentation=doc.page_content,
                                 question=question)
                   for doc in optional]
        replies = self._heymans.condense_model.predict_multiple(prompts)
        for reply, doc in zip(replies, optional):
            doc_desc = f'{doc.metadata["url"]} ({doc.metadata["seq_num"]})'
            if not reply.lower().startswith('no'):
                important.append(doc)
                logger.info(f'keeping {doc_desc}')
            else:
                logger.info(f'stripping {doc_desc}')
        self._documents = important
    
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
        if config.openai_api_key is None:
            logger.warning(
                'No OpenAI API key provided, no documentation available')
            return
        self._embeddings_model = OpenAIEmbeddings(
            openai_api_key=config.openai_api_key)
        logger.info('reading FAISS documentation cache')
        self._db = FAISS.load_local(Path('.db.cache'), self._embeddings_model)
        self._retriever = self._db.as_retriever(
            search_kwargs={'k': config.search_docs_per_query})
    
    def search(self, queries):
        if config.openai_api_key is None:
            return []
        docs = []
        for query in queries:
            logger.info(f'searching FAISS')
            for doc in self._retriever.invoke(query):
                doc_desc = f'{doc.metadata["url"]} ({doc.metadata["seq_num"]})'
                if any(doc.page_content == ref.page_content for ref in docs):
                    logger.info(f'duplicate {doc_desc}')
                    continue
                if doc.page_content not in self._heymans.documentation and \
                        doc.page_content not in docs:
                    logger.info(f'adding {doc_desc}')
                    docs.append(doc)
                else:
                    logger.info(f'skipping {doc_desc}')
        return docs
