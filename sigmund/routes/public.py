import logging
from flask import jsonify, Blueprint, request, Response
from flask_cors import cross_origin
from .. import config, utils, prompt
from ..sigmund import Sigmund
from .app import get_sigmund
logger = logging.getLogger('sigmund')
public_blueprint = Blueprint('public', __name__)


@public_blueprint.route('/search', methods=['POST'])
@cross_origin()
def search():
    data = request.json
    config.db_cache = data.get('source', 'default')
    query = data.get('query', None)
    offset = data.get('offset', 0) * config.public_search_docs_max
    sigmund = Sigmund(user_id='dummy', persistent=False, encryption_key=None)
    sigmund.documentation.clear()
    sigmund.documentation.search([query])
    docs = []
    urls = []
    logging.info(f'public search: {query} (offset={offset})')
    for doc in sigmund.documentation._documents[offset:]:
        if doc.metadata['url'] in urls:
            print('skipping duplicate')
            continue
        urls.append(doc.metadata['url'])
        doc.page_content = doc.page_content[
            :config.public_search_max_doc_length]
        docs.append(doc)
        if len(docs) >= config.public_search_docs_max:
            break
    sigmund.documentation._documents = docs
    logging.info(f'public search results: {len(docs)}')
    query = prompt.render(prompt.PUBLIC_SEARCH_PROMPT,
                          documentation=sigmund.documentation)
    results = utils.md(
        sigmund.public_model.predict(query).replace('\n\n-', '\n-'))
    return jsonify(results=results)


@public_blueprint.route('/search_widget')
def search_widget():
    return utils.render('search-widget.html')


@public_blueprint.route('/search-widget.js')
@cross_origin()
def search_widget_js():
    return Response(utils.render('search-widget.js'),
                    mimetype='text/javascript')
