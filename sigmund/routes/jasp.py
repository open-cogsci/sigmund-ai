import json
import logging
from flask import Blueprint, request, jsonify, Response
from flask_cors import cross_origin
from openai import OpenAI
from .. import config

logger = logging.getLogger('sigmund')

jasp_blueprint = Blueprint('jasp', __name__)

_client = OpenAI(api_key=config.openai_api_key)


@jasp_blueprint.route('/completions', methods=['POST'])
@cross_origin()
def completions():
    """Proxy that forwards OpenAI-compatible chat completion requests to OpenAI."""
    body = request.get_json(force=True)
    body['reasoning_effort'] = 'none'
    stream = body.get('stream', False)
    if stream:
        return _stream_response(body)

    response = _client.chat.completions.create(**body)
    return jsonify(response.model_dump())


def _stream_response(body):
    """Return a streaming SSE response by proxying to OpenAI."""
    def generate():
        stream = _client.chat.completions.create(**body)
        for chunk in stream:
            yield f"data: {chunk.model_dump_json()}\n\n"
        yield "data: [DONE]\n\n"

    return Response(generate(), mimetype='text/event-stream')