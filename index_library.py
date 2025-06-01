from sigmund import config
from sigmund.library import Library
from pathlib import Path
import logging
logging.basicConfig(level=logging.INFO, force=True)

# Initialize library
library = Library(
    persist_directory=config.search_persist_directory,
    embedding_provider=config.search_embedding_provider,
    embedding_model=config.search_embedding_model)

added = 0
for path in Path('sources').glob('*.json'):
    print(f"Adding documents from {path}")
    added += library.add(path)
print(f"Added {added} documents")
