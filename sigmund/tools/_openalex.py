from . import BaseTool
from .. import config
import logging
import json
import base64
import pyalex
from pyalex import Works
from mistralai import Mistral

logger = logging.getLogger('sigmund')
pyalex.config.api_key = config.openalex_api_key


class search_openalex(BaseTool):
    """Search OpenAlex for scientific articles. An overview of metadata (abstracts, authors, titles, etc.) of matching articles will be returned, including OpenAlex IDs that can be used with download_from_openalex."""

    arguments = {
        "queries": {
            "type": "array",
            "items": {
                "type": "string"
            },
            "description": "A list of search queries",
        },
        "max_results_per_query": {
            "type": "integer",
            "description": "The maximum number of results to return per query. (default=10)",
        }
    }
    required_arguments = ["queries"]

    def __call__(self, queries, max_results_per_query=10):
        results = []
        if isinstance(queries, str):
            queries = [queries]
        logger.info(f'searching OpenAlex for {len(queries)} queries')
        for query in queries:
            pager = (Works()
                     .search(query)
                     .paginate(
                         per_page=min(max_results_per_query, 25),
                         n_max=max_results_per_query))
            for page in pager:
                for work in page:
                    logger.info(
                        f'appending doc for OpenAlex search: {query}')
                    oa = work.get("open_access") or {}
                    location = work.get("primary_location") or {}
                    source = location.get("source") or {}
                    result = {
                        "openalex_id": work.get("id"),
                        "title": work.get("title"),
                        "doi": work.get("doi"),
                        "year": work.get("publication_year"),
                        "authors": [
                            a["author"]["display_name"]
                            for a in work.get("authorships", [])
                        ],
                        "abstract": work.get("abstract"),
                        "venue": source.get("display_name"),
                        "cited_by_count": work.get("cited_by_count"),
                        "is_open_access": oa.get("is_oa"),
                        "oa_url": oa.get("oa_url"),
                    }
                    results.append(result)
        message = (f'I found {len(results)} articles and added them to '
                   f'the workspace.')
        results = json.dumps(results, indent='  ')
        return message, results, True


class download_from_openalex(BaseTool):
    """Download the full text (in TEI-XML format) of a single scientific article from OpenAlex using its OpenAlex ID."""

    arguments = {
        "openalex_id": {
            "type": "string",
            "description": "The OpenAlex ID of the article (e.g. 'https://openalex.org/W1234567890' or 'W1234567890').",
        }
    }
    required_arguments = ["openalex_id"]

    def __call__(self, openalex_id):
        if not openalex_id.startswith("https://"):
            openalex_id = f"https://openalex.org/{openalex_id}"
        work = Works()[openalex_id]
        if not work['has_content']['pdf']:
            return "No full text available for this article.", "", True
        try:
            pdf_content = work.pdf.get()
        except Exception as e:
            logger.error(f"Failed to download PDF for {openalex_id}: {e}")
            return "Failed to download full text for this article.", "", True
        try:
            full_text = _ocr_extract(pdf_content, "application/pdf")
        except Exception as e:
            logger.error(f"Failed to convert PDF to text for {openalex_id}: {e}")
            return "Failed to convert PDF to text for this article.", "", True            
        title = work.get("title", openalex_id)
        message = (f'I downloaded the full text of "{title}" and added '
                   f'it to the workspace.')
        return message, full_text, True
        
        
def _ocr_extract(content, mimetype):
    """Extract text from a document using Mistral's OCR API.
    
    Parameters
    ----------
    content : bytes
        The document content.
    mimetype : str
        The MIME type of the document.
    
    Returns
    -------
    str
        The extracted text.
    """
    b64_content = base64.b64encode(content).decode('utf-8')    
    client = Mistral(api_key=config.mistral_api_key)
    ocr_response = client.ocr.process(
        model="mistral-ocr-latest",
        document={
            "type": "document_url",
            "document_url": f"data:{mimetype};base64,{b64_content}" 
        },
        include_image_base64=False
    )
    return '\n\n'.join(page.markdown for page in ocr_response.pages)
