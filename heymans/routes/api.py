import json
import base64
import logging
from werkzeug.utils import secure_filename
from flask import request, jsonify, Response, redirect, session, \
    stream_with_context, make_response, Blueprint
from flask_login import login_required
from .. import config, utils, attachments
from .app import get_heymans
from redis import Redis
logger = logging.getLogger('heymans')
api_blueprint = Blueprint('api', __name__)
redis_client = Redis()


@api_blueprint.route('/chat/start', methods=['POST'])
@login_required
def api_chat_start():
    data = request.json
    session['user_message'] = data.get('message', '')
    session['search_first'] = data.get('search_first', True)
    session['message_id'] = data.get('message_id', None)
    heymans = get_heymans()
    redis_client.delete(f'stream_cancel_{heymans.user_id}')
    return '{}'
    

@api_blueprint.route('/chat/cancel', methods=['POST'])
@login_required
def api_chat_cancel_stream():
    heymans = get_heymans()
    logger.info(f'cancelling stream for {heymans.user_id}')
    redis_client.set(f'stream_cancel_{heymans.user_id}', '1')
    return jsonify({'status': 'cancelled'}), 200


@api_blueprint.route('/chat/stream', methods=['GET'])
@login_required
def api_chat_stream():
    message = session['user_message']
    message_id = session['message_id']
    heymans = get_heymans()
    logger.info(f'starting stream for {heymans.user_id}')
    def generate():
        for reply, metadata in heymans.send_user_message(message, message_id):
            if isinstance(reply, dict):
                reply = json.dumps(reply)
            else:
                reply = json.dumps(
                    {'response': utils.md(
                        f'{config.ai_name}: {config.process_ai_message(reply)}'),
                     'metadata': metadata})
            logger.debug(f'ai message: {reply}')
            yield f'data: {reply}\n\n'
            if redis_client.get(f'stream_cancel_{heymans.user_id}'):
                logger.info(f'stream cancelled for {heymans.user_id}')
                break
        yield 'data: {"action": "close"}\n\n'
    return Response(stream_with_context(generate()),
                    mimetype='text/event-stream')
    
    
@api_blueprint.route('/conversation/new')
@login_required
def new_conversation():
    heymans = get_heymans()
    heymans.database.new_conversation()
    return redirect('/chat')


@api_blueprint.route('/conversation/clear')
@login_required
def clear_conversation():
    heymans = get_heymans()
    heymans.messages.init_conversation()
    heymans.messages.save()
    return redirect('/chat')


@api_blueprint.route('/conversation/activate/<int:conversation_id>',
                     methods=['GET', 'POST'])
@login_required
def activate_conversation(conversation_id):
    if conversation_id:
        heymans = get_heymans()
        heymans.database.set_active_conversation(conversation_id)
    logger.info('redirecting to chat')
    return redirect('/chat')


@api_blueprint.route('/conversation/list', methods=['GET', 'POST'])
@login_required
def list_conversations():
    heymans = get_heymans()
    return jsonify(heymans.database.list_conversations())
    

@api_blueprint.route('/conversation/delete/<int:conversation_id>',
                     methods=['DELETE'])
@login_required
def delete_conversation(conversation_id):
    heymans = get_heymans()
    heymans.database.delete_conversation(conversation_id)
    return '', 204


@api_blueprint.route('/attachments/list', methods=['GET', 'POST'])
@login_required
def list_attachments():
    heymans = get_heymans()
    return jsonify(heymans.database.list_attachments())


@api_blueprint.route('/attachments/delete/<int:attachment_id>',
                     methods=['DELETE'])
@login_required
def delete_attachment(attachment_id):
    heymans = get_heymans()
    success = heymans.database.delete_attachment(attachment_id)
    return jsonify(success=success)
    

@api_blueprint.route('/attachments/add', methods=['POST'])
@login_required
def add_attachment():
    heymans = get_heymans()
    if 'file' not in request.files:
        return jsonify(success=False, message="No file part"), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify(success=False, message="No selected file"), 400
    filename = secure_filename(file.filename)
    content = file.read()
    file.seek(0)
    description = attachments.describe_file(filename, content,
                                            heymans.condense_model)
    attachment_data = {'filename': filename,
                       'content': base64.b64encode(content).decode('utf-8'),
                       'description': description}
    attachment_id = heymans.database.add_attachment(attachment_data)
    if attachment_id == -1:
        return jsonify(success=False, message="Failed to add attachment"), 500
    else:
        return jsonify(success=True, attachment_id=attachment_id)


@api_blueprint.route('/attachments/get/<int:attachment_id>', methods=['GET'])
@login_required
def get_attachment(attachment_id):
    heymans = get_heymans()
    attachment_data = heymans.database.get_attachment(attachment_id)
    if attachment_data:
        decoded_content = base64.b64decode(attachment_data['content'])
        response = make_response(decoded_content)
        response.headers['Content-Type'] = 'application/octet-stream'
        response.headers['Content-Disposition'] = \
            f'attachment; filename={attachment_data["filename"]}'
        return response
    return jsonify(success=False,
                   message="Attachment not found or access denied"), 404


@api_blueprint.route('/message/delete/<message_id>', methods=['DELETE'])
@login_required
def delete_message(message_id):
    heymans = get_heymans()
    heymans.messages.delete(message_id)
    return jsonify(success=True)
