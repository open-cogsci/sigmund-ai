import json
from pathlib import Path
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.vectorstores.utils import DistanceStrategy
from langchain_core.documents import Document
import logging
from . import config
from . import prompt
logger = logging.getLogger('sigmund')


class Documentation:
    
    def __init__(self, sigmund, sources=[]):
        self._sigmund = sigmund
        self._documents = []
        self._sources = sources
        
    def _doc_to_str(self, doc):
        s = '<document>\n'
        if doc.metadata.get('title', None):
            s += f'# {doc.metadata["title"]}\n\n'
        if doc.metadata.get('url', None):
            s += f'Source: {doc.metadata["url"]}\n\n'
        return s + doc.page_content + '\n</document>'
        
    def __str__(self):
        if not self._documents:
            return ''
        return '\n\n'.join(self._doc_to_str(doc) for doc in self._documents)
        
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
        while optional and len(important) < config.search_docs_max:
            batch = optional[:config.search_docs_max]
            logger.info(f'evaluating document batch (n={len(batch)}): {[doc.metadata["seq_num"] for doc in batch]}')
            optional = optional[config.search_docs_max:]
            prompts = [prompt.render(prompt.JUDGE_RELEVANCE,
                                     documentation=doc.page_content,
                                     question=question)
                       for doc in batch]
            self._sigmund.condense_model.json_mode = True
            replies = self._sigmund.condense_model.predict_multiple(prompts)
            self._sigmund.condense_model.json_mode = False
            config.mistral_kwargs = dict()
            for reply, doc in zip(replies, batch):
                doc_desc = f'{doc.metadata["url"]} ({doc.metadata["seq_num"]})'
                try:
                    reply = json.loads(reply)
                except json.JSONDecodeError:
                    logger.warning(f'invalid JSON for {doc_desc} (reply: {reply})')
                    continue
                if not isinstance(reply, dict):
                    logger.warning(f'invalid JSON for {doc_desc} (reply: {reply})')
                    continue
                if not reply.get('relevant', False):
                    logger.info(f'stripping {doc_desc} (reply: {reply})')
                    continue
                logger.info(f'keeping {doc_desc} (reply: {reply})')
                important.append(doc)
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
    
    def __init__(self, sigmund):
        self._sigmund = sigmund
    
    def search(self, queries):
        pass

    
class FAISSDocumentationSource(BaseDocumentationSource):
    
    def __init__(self, sigmund):
        super().__init__(sigmund)
        if config.openai_api_key is None:
            logger.warning(
                'No OpenAI API key provided, no documentation available')
            return
        self._embeddings_model = OpenAIEmbeddings(
            openai_api_key=config.openai_api_key,
            model=config.search_embedding_model)
        logger.info('reading FAISS documentation cache')
        db_cache = config.db_cache_sources[config.db_cache]
        self._db = FAISS.load_local(Path(db_cache), self._embeddings_model,
                                    allow_dangerous_deserialization=True)
        if config.search_docs_distance_metric == 'cosine':
            self._db.distance_strategy = DistanceStrategy.COSINE
        elif config.search_docs_distance_metric == 'euclidean_distance':
            self._db.distance_strategy = DistanceStrategy.EUCLIDEAN_DISTANCE
        else:
            raise ValueError(
                f'invalid search_docs_distance_metric: {config.search_docs_distance_metric}')

    def search(self, queries):
        if config.openai_api_key is None:
            return []
        docs = []
        for query in queries:
            if config.log_replies:
                logger.info(f'documentation search query: {query}')
            for doc, score in self._db.similarity_search_with_score(
                    query, k=config.search_docs_per_query):
                doc_desc = f'{doc.metadata["url"]} ({doc.metadata["seq_num"]})'
                if any(doc.page_content == ref.page_content for ref, _ in docs):
                    continue
                if doc.page_content not in self._sigmund.documentation and \
                        doc.page_content not in docs:
                    docs.append((doc, score))
        # The documents that are retrieved need a little re-ordering to be
        # optimal. First we rank them by score across all search queries. Then
        # we reorder them so that documents without URL, which tend to be short
        # how-to's alternate with documents with URL, which tend to be longer
        # pieces of documentation. This is to make sure that documentation
        # stands a chance against the how-to's, which tend to be preferred by
        # the algorithm. Finally we keep only the top few documents.
        docs = sorted(docs, key=lambda doc: doc[1])
        with_url = [d for d in docs if d[0].metadata['url'] is not None]
        without_url = [d for d in docs if d[0].metadata['url'] is None]
        reordered_docs = []
        while with_url or without_url:
            if with_url:
                reordered_docs.append(with_url.pop(0))
            if without_url:
                reordered_docs.append(without_url.pop(0))
        for doc, score in reordered_docs:
            doc_desc = f'{doc.metadata["url"]} ({doc.metadata["seq_num"]})'
            logger.info(f'considering {doc_desc}, score: {score}')
        return [doc for doc, _ in reordered_docs]
