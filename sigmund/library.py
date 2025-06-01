import json
from pathlib import Path
import chromadb
from chromadb.utils import embedding_functions
import hashlib
from typing import List, Dict, Any, Union
import logging
from . import config
logger = logging.getLogger('sigmund')


class Library:
    """
    A vector database library using ChromaDB for persistent document storage and search.
    """
    
    def __init__(self, persist_directory: str,
                 embedding_provider: str, embedding_model: str,
                 collection_name: str = "documents"):
        """
        Initialize the Library with ChromaDB backend.
        
        Args:
            persist_directory: Directory for persistent storage
            collection_name: Name of the ChromaDB collection
            embedding_provider: Which embedding provider to use ("mistral", "openai", "sentence-transformers")
            embedding_model: Specific model name for the provider
            api_key: API key for the embedding provider (if needed)
        """
        self._json_metadata_fields = set()
        # Initialize ChromaDB with persistent storage
        self.client = chromadb.PersistentClient(path=persist_directory)
        
        # Set up embedding function based on provider
        self.embedding_function = self._get_embedding_function(
            embedding_provider, embedding_model
        )
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=self.embedding_function
        )
        logger.info(f'library contains {self.collection.count()} documents')
        
    def _get_embedding_function(self, provider: str, model: str):
        """Get the appropriate embedding function based on provider."""
        if provider == "openai":
            return embedding_functions.OpenAIEmbeddingFunction(
                api_key=config.openai_api_key,
                model_name=model
            )
        else:
            raise ValueError(f"Unknown embedding provider: {provider}")
    
    def _clean_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Union[str, int, float, bool]]:
        """
        Clean metadata to ensure ChromaDB compatibility.
        ChromaDB only accepts: str, int, float, bool (no None, lists, dicts, etc.)
        """
        cleaned = {}
        for key, value in metadata.items():
            if value is None:
                # Skip None values
                continue
            elif isinstance(value, (str, int, float, bool)):
                # Keep valid types as-is
                cleaned[key] = value
            elif isinstance(value, (list, dict)):
                # Convert complex types to strings
                cleaned[key] = json.dumps(value)
                self._json_metadata_fields.add(key)
            else:
                # Convert other types to string
                cleaned[key] = str(value)
        return cleaned
    
    def _document_exists(self, doc_id: str) -> bool:
        """Check if a document with the given ID already exists."""
        result = self.collection.get(ids=[doc_id])
        return len(result['ids']) > 0
    
    def add(self, documents: [str, Path, dict, list[dict]],
            **metadata_kwargs) -> int:
        """
        Add documents.
        
        Args:
            documents: one of the following:
                A single document dict. Must have at least a content key. Other
                keys are treated as metadata
                A list of document dicts
                A JSON-formatted str
                A Path corresonding to a JSON file
            
            **metadata_kwargs: Additional metadata fields to include for all 
                               documents.
            
        Returns:
            Number of documents added (excluding duplicates)
        """
        if isinstance(documents, dict):
            logger.info('turning document into list')
            return self.add([documents], **metadata_kwargs)
        if isinstance(documents, str):
            logger.info('reading documents from json string')
            return self.add(json.loads(documents), **metadata_kwargs)
        if isinstance(documents, Path):
            logger.info('reading documents from json file')
            return self.add(json.loads(documents.read_text()), **metadata_kwargs)    
        
        contents = []
        metadatas = []
        ids = []
        skipped_duplicates = 0
        
        for doc_data in documents:
            # Extract content (required field)
            if 'content' not in doc_data:
                breakpoint()
                logging.warning(
                    f"Skipping document without 'content' field: {doc_data}")
                continue
                
            content = doc_data['content']
            
            # Generate unique ID based on content hash
            doc_id = hashlib.md5(content.encode()).hexdigest()
            
            # Check if document already exists
            if self._document_exists(doc_id):
                skipped_duplicates += 1
                continue
            
            # Extract and clean metadata (all other fields)
            raw_metadata = {k: v for k, v in doc_data.items() if k != 'content'}
            metadata = self._clean_metadata(raw_metadata)
            metadata.update(metadata_kwargs)
            
            if doc_id in ids:
                logger.warning(f"Duplicate document ID generated: {doc_id}")
            else:
                contents.append(content)
                metadatas.append(metadata)            
                ids.append(doc_id)
        
        if contents:
            # Add to ChromaDB collection in batches to avoid token limits
            batch_size = 100  # Adjust based on your typical document size
            total_added = 0
            
            for i in range(0, len(contents), batch_size):
                batch_contents = contents[i:i + batch_size]
                batch_metadatas = metadatas[i:i + batch_size]
                batch_ids = ids[i:i + batch_size]
                
                logger.info(f"Adding batch {i//batch_size + 1} of {(len(contents) + batch_size - 1)//batch_size} "
                           f"({len(batch_contents)} documents)")
                
                try:
                    self.collection.add(
                        documents=batch_contents,
                        metadatas=batch_metadatas,
                        ids=batch_ids
                    )
                    total_added += len(batch_contents)
                except Exception as e:
                    logger.error(f"Failed to add batch {i//batch_size + 1}: {e}")
                    # Optionally, you could try with smaller batch size or handle specific errors
                    raise
        
        if skipped_duplicates > 0:
            logger.warning(f"Skipped {skipped_duplicates} duplicate documents")
        
        return total_added if contents else 0
    
    def search(self, query: str = None, k: int = 5, max_distance: float = None,
               **metadata_filters) -> List[Dict[str, Any]]:
        """
        Search for documents similar to the query and/or matching metadata filters.

        Args:
            query: Search query text (optional - if None, searches by metadata only)
            k: Number of documents to return
            max_distance: Maximum distance threshold for semantic search (optional)
            **metadata_filters: Optional metadata filters (e.g., user_id="123")

        Returns:
            List of dictionaries with 'content', 'distance' (if query provided), and metadata fields
        """
        # Build where clause for metadata filtering
        where_clause = None
        if metadata_filters:
            filters = []
            for key, value in metadata_filters.items():
                if isinstance(value, (set, list, tuple)):
                    # Use $in operator for multiple values
                    filters.append({key: {"$in": list(value)}})
                else:
                    # Use $eq operator for single values
                    filters.append({key: {"$eq": value}})
    
            # Combine filters with $and
            if len(filters) > 1:
                where_clause = {"$and": filters}
            else:
                where_clause = filters[0]

        # Perform search
        if query is not None:
            # Semantic search with optional metadata filtering
            results = self.collection.query(
                query_texts=[query],
                n_results=k,
                where=where_clause
            )
        else:
            # Metadata-only search
            if not metadata_filters:
                raise ValueError("Either query or metadata_filters must be provided")

            results = self.collection.get(
                where=where_clause,
                limit=k
            )
            # Convert get() format to query() format for consistency
            results = {
                'documents': [results['documents']] if results['documents'] else [[]],
                'metadatas': [results['metadatas']] if results['metadatas'] else [[]],
                'distances': [[None] * len(results['documents'])] if results['documents'] else [[]]
            }
        # Print out lowest distance
        lowest_distance = None
        if results['distances'] and results['distances'][0]:
            lowest_distance = min(results['distances'][0])
            if lowest_distance is not None:
                logger.info(f'lowest distance: {lowest_distance:.2f} (max_distance = {max_distance})')        
        # Format results        
        formatted_results = []
        if results['documents'] and results['documents'][0]:
            for i, doc in enumerate(results['documents'][0]):
                # Apply distance filtering if specified
                if query is not None and max_distance is not None:
                    if results['distances'][0][i] > max_distance:
                        break  # Stop here - all subsequent results will be worse
        
                result = {
                    'content': doc,
                    **results['metadatas'][0][i]  # Add all metadata fields
                }
                # Only add distance if we performed semantic search
                if query is not None:
                    result['distance'] = results['distances'][0][i]                
        
                # Convert all JSON-encoded metadata fields back to Python objects
                for key, value in result.items():
                    if key in ('content', 'title'):
                        continue
                    if key in self._json_metadata_fields or \
                            (isinstance(value, str) and value[0] in ['{', '[']):
                        try:
                            result[key] = json.loads(value)
                        except Exception:
                            logger.warning(f'failed to decode JSON for {key}')
                            pass        
                formatted_results.append(result)

        return formatted_results
        
    def retrieve_foundation_documents(self, results):
        topics = set()
        for result in results:
            topics |= set(result.get('topics', set()))
        foundation_results = []
        for topic in topics:
            results = self.search(None, k=1, topic=topic, foundation=True)
            if results:
                logger.info(f'found foundation document for {topic}')
            else:
                logger.info(f'no foundation document for {topic}')
            foundation_results += results
        return foundation_results
    
    def count(self) -> int:
        """Return the total number of documents in the collection."""
        return self.collection.count()
    
    def delete_all(self):
        """Delete all documents from the collection."""
        # ChromaDB doesn't have a direct delete_all, so we delete and recreate
        collection_name = self.collection.name
        self.client.delete_collection(collection_name)
        self.collection = self.client.create_collection(
            name=collection_name,
            embedding_function=self.embedding_function
        )