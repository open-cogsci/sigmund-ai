from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from datamatrix import functional as fnc
from pathlib import Path
import logging
import openai
import time
from . import config
logger = logging.getLogger('sigmund')


class CachedEmbeddings(OpenAIEmbeddings):
    """Uses memoization to avoid calculating embeddings over and over again"""
    def embed_documents(self, texts):
        @fnc.memoize(persistent=True)
        def inner(texts):
            return super(CachedEmbeddings, self).embed_documents(texts)
        return inner(texts)


def load_library(force_reindex=False, cache_folder=config.db_cache,
                 exclude_filter=[]):
    db_cache = Path(config.db_cache_sources[cache_folder])
    src_path = Path('sources')
    embeddings_model = CachedEmbeddings(openai_api_key=config.openai_api_key,
                                        model=config.search_embedding_model)
    if not force_reindex and db_cache.exists():
        logger.info('loading library from cache')
        db = FAISS.load_local(db_cache, embeddings_model,
                              allow_dangerous_deserialization=True)
        return db.as_retriever()
    from langchain_community.document_loaders import TextLoader, \
        PyPDFLoader, JSONLoader
    logger.info('initializing library')
    data = []
    # PDF files are unstructured. They can be named through config.sources
    for src in src_path.glob('pdf/**/*.pdf'):
        if any(f in str(src) for f in exclude_filter):
            logger.info(f'skipping pdf: {src}')
            continue
        logger.info(f'indexing pdf: {src}')
        data += PyPDFLoader(str(src)).load_and_split()
    # jsonl is mainly for documentation
    for src in src_path.glob('jsonl/*.jsonl'):
        logger.info(f'indexing json: {src}')
        if any(f in str(src) for f in exclude_filter):
            logger.info(f'skipping json: {src}')
            continue            
        loader = JSONLoader(src, jq_schema='.', content_key='content',
                            json_lines=True,
                            metadata_func=_extract_metadata)
        data += loader.load()
    # To avoid running into rate limits, we throttle the ingestion of the
    # documents
    for i in range(0, len(data), config.chunk_size):
        logger.info(
            f'ingesting chunk {i}-{i + config.chunk_size}/{len(data)}')
        chunk = data[i:i + config.chunk_size]
        if not i:
            db = FAISS.from_documents(chunk, embeddings_model)
        else:
            time.sleep(config.chunk_throttle)
            db.add_documents(chunk)
    db.save_local(db_cache)
    logger.info(f'libary initialized')
    return db.as_retriever()


def _extract_metadata(record, metadata):
    metadata['url'] = record.get('url', record.get('source', None))
    metadata['title'] = record['title']
    return metadata
