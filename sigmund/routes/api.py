import json
import base64
import mimetypes
import logging
from flask import request, jsonify, Response, redirect, session, \
    stream_with_context, make_response, Blueprint
from flask_login import login_required
from .. import config
from ..redis_client import redis_client
from .app import get_sigmund
logger = logging.getLogger('sigmund')
api_blueprint = Blueprint('api', __name__)


@api_blueprint.route('/health', methods=['GET'])
@login_required
def health():
    return jsonify(success=True)


@api_blueprint.route('/chat/start', methods=['POST'])
@login_required
def api_chat_start():

    # Store request data in the session
    message = request.form.get('message', '')
    workspace_content = request.form.get('workspace_content', '')
    workspace_language = request.form.get('workspace_language', '')
    message_id = request.form.get('message_id', '')
    transient_settings = request.form.get('transient_settings', '{}')
    transient_settings = json.loads(transient_settings)
    transient_system_prompt = request.form.get('transient_system_prompt', '')
    foundation_document_topics = request.form.get('foundation_document_topics',
                                                  None)
    if foundation_document_topics is not None:
        foundation_document_topics = json.loads(foundation_document_topics)
    session['user_message']       = message
    session['workspace_content']  = workspace_content
    session['workspace_language'] = workspace_language
    session['message_id']         = message_id
    session['transient_settings'] = transient_settings
    session['transient_system_prompt'] = transient_system_prompt
    session['foundation_document_topics'] = foundation_document_topics

    sigmund = get_sigmund(transient_settings=transient_settings)
    redis_client.delete(f'stream_cancel_{sigmund.user_id}')

    # Grab attached files from the request
    attachments = request.files.getlist('attachments')
    attachment_list = []
    for file in attachments:
        if not file:
            continue
        # Read file contents
        file_bytes = file.read()
        file_b64 = base64.b64encode(file_bytes).decode('utf-8')
        # Guess a MIME type for building the data URL
        mime_type, _ = mimetypes.guess_type(file.filename)
        if not mime_type:
            # Fallback if unable to guess the MIME type
            mime_type = 'application/octet-stream'
        # Build data URL
        data_url = f"data:{mime_type};base64,{file_b64}"
        # Define the type field
        # (Optional) Distinguish between documents and images more precisely:
        if mime_type.startswith('image/'):
            attachment_type = 'image'
        else:
            attachment_type = 'document'
        attachment_list.append({
            'type': attachment_type,
            'file_name': file.filename,
            'url': data_url
        })
    # Save to Redis
    # Convert list of attachments to JSON first
    redis_client.set(f'attachments_{sigmund.user_id}', json.dumps(attachment_list))
    return '{}'


@api_blueprint.route('/chat/stream', methods=['GET'])
@login_required
def api_chat_stream():

    # Retrieve message details from session
    message = session.get('user_message', '')
    workspace_content = session.get('workspace_content', '')
    workspace_language = session.get('workspace_language', '')
    message_id = session.get('message_id', '')
    transient_settings = session.get('transient_settings')
    transient_system_prompt = session.get('transient_system_prompt')
    foundation_document_topics = session.get('foundation_document_topics')

    # Retrieve attachments from Redis
    sigmund = get_sigmund(transient_settings=transient_settings,
                          transient_system_prompt=transient_system_prompt,
                          foundation_document_topics=foundation_document_topics)
    attachments_json = redis_client.get(f'attachments_{sigmund.user_id}')
    attachments = []
    if attachments_json:
        attachments = json.loads(attachments_json)

    logger.info(f'starting stream for {sigmund.user_id}')
    def generate():
        for reply in sigmund.send_user_message(
                message, workspace_content, workspace_language,
                attachments=attachments, message_id=message_id):
            json_reply = reply.to_json()
            logger.debug(f'ai message: {json_reply}')
            yield f'data: {json_reply}\n\n'
            if redis_client.get(f'stream_cancel_{sigmund.user_id}'):
                logger.info(f'stream cancelled for {sigmund.user_id}')
                break
        yield 'data: {"action": "close"}\n\n'

    # Return a server-sent event response
    return Response(stream_with_context(generate()),
                    mimetype='text/event-stream')


@api_blueprint.route('/chat/cancel', methods=['POST'])
@login_required
def api_chat_cancel_stream():
    sigmund = get_sigmund()
    logger.info(f'cancelling stream for {sigmund.user_id}')
    redis_client.set(f'stream_cancel_{sigmund.user_id}', '1')
    return jsonify({'status': 'cancelled'}), 200    
    
    
@api_blueprint.route('/conversation/new')
@login_required
def new_conversation():
    sigmund = get_sigmund()
    sigmund.database.new_conversation()
    return redirect('/chat')


@api_blueprint.route('/conversation/clear')
@login_required
def clear_conversation():
    sigmund = get_sigmund()
    sigmund.messages.init_conversation()
    sigmund.messages.save()
    return redirect('/chat')


@api_blueprint.route('/conversation/activate/<int:conversation_id>',
                     methods=['GET', 'POST'])
@login_required
def activate_conversation(conversation_id):
    if conversation_id:
        sigmund = get_sigmund()
        sigmund.database.set_active_conversation(conversation_id)
    logger.info('redirecting to chat')
    return redirect('/chat')


@api_blueprint.route('/conversation/list', methods=['GET'])
@login_required
def list_conversations():
    sigmund = get_sigmund()
    query = request.args.get('query', None)
    return jsonify(sigmund.database.list_conversations(query))
    

@api_blueprint.route('/conversation/delete/<int:conversation_id>',
                     methods=['DELETE'])
@login_required
def delete_conversation(conversation_id):
    sigmund = get_sigmund()
    sigmund.database.delete_conversation(conversation_id)
    return '', 204


@api_blueprint.route('/conversation/export', methods=['GET'])
@login_required
def export_conversations():
    sigmund = get_sigmund()
    conversations = sigmund.database.export_conversations()
    if conversations:
        response = make_response(json.dumps(conversations))
        response.headers['Content-Type'] = 'application/json'
        response.headers['Content-Disposition'] = \
            'attachment; filename=sigmund-export.json'
        return response
    return jsonify(success=False,
                   message="No conversations found or access denied"), 404


@api_blueprint.route('/message/delete/<message_id>', methods=['DELETE'])
@login_required
def delete_message(message_id):
    sigmund = get_sigmund()
    sigmund.messages.delete(message_id)
    return jsonify(success=True)


@api_blueprint.route('/setting/set', methods=['POST'])
@login_required
def set_setting():
    data = request.json
    if not isinstance(data, dict):
        logger.warning(f'invalid setting data: {data}')
        return jsonify(success=False, message='invalid setting data')
    sigmund = get_sigmund()
    logger.info(f'setting: {data}')
    for key, value in data.items():
        sigmund.database.set_setting(key, value)
    return jsonify(success=True)
    

@api_blueprint.route('/setting/get/<key>')
@login_required
def get_setting(key):
    sigmund = get_sigmund()
    value = sigmund.database.get_setting(key)
    if value is None:
        if key in config.settings_default:
            value = config.settings_default[key]
            logger.info(f'using default setting for {key}: {value}')
        else:
            return jsonify(success=False, value=value)
    logger.info(f'get setting: {key} = {value}')
    return jsonify(success=True, value=value)
    
