import logging
import os
import io
import subprocess
import tempfile
from pdfminer.high_level import extract_text
from . import config, prompt
logger = logging.getLogger('heymans')


def file_to_text(name: str, content: bytes) -> str:
    """Generates a text representation of a file, based on its name and 
    content. If the file cannot be converted to a text representation, 
    'No description' is returned. The representation is limited to the maximum
    length as specified in the config.
    """
    suffix = os.path.splitext(name)[1]
    if suffix == '.pdf':
        try:
            text_representation = extract_text(io.BytesIO(content))
        except Exception as e:
            logger.error(f'failed to extract text: {e}')
            return 'No description'
    else:
        with tempfile.NamedTemporaryFile(suffix=suffix) as temp_file:
            temp_file.write(content)
            try:
                output = subprocess.run(
                    ['pandoc', '-s', temp_file.name, '-t', 'plain'],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    check=True,
                    text=True
                )
            except subprocess.CalledProcessError as e:
                logger.error(f'failed to extract text: {e}')
                return 'No description'
            except FileNotFoundError as e:
                logger.error(f'pandoc is not available: {e}')
                return 'No description'
        text_representation = output.stdout
    if not text_representation:
        text_representation = content.decode('utf-8', errors='ignore')
    text_representation = text_representation.strip()[
        :config.max_text_representation_length]
    if not text_representation:
        return 'No description'
    return text_representation


def describe_file(name: str, content: bytes, model: str) -> str:
    """Generates an LLM description of a file based on its name and content."""
    return model.predict(
        prompt.render(prompt.DESCRIBE_PROMPT,
                      name=name,
                      text_representation=file_to_text(name, content)))


def attachments_prompt(db) -> str:
    """Returns a prompt fragment to include in the system prompt, containing
    a list of all attachments including descriptions. An empty string
    is returned if there are no attachments.
    """
    description = []
    for attachment in db.list_attachments().values():
        description.append(
            f'- {attachment["filename"]}: {attachment["description"]}')
    if not description:
        return ''
    return prompt.render(prompt.SYSTEM_PROMPT_ATTACHMENTS,
                         description='\n'.join(description))
