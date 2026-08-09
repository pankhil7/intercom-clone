import logging
from datetime import datetime
from app.socket.server import sio
from app.services.auth_service import decode_widget_token

logger = logging.getLogger(__name__)

connected_widgets = {}  # {sid: {contact_id, org_id, conversation_id}}


@sio.on('connect', namespace='/widget')
async def widget_connect(sid, environ, auth):
    session_token = None
    if auth and isinstance(auth, dict):
        session_token = auth.get('session_token')

    if not session_token:
        await sio.disconnect(sid, namespace='/widget')
        return False

    payload = decode_widget_token(session_token)
    if not payload:
        await sio.disconnect(sid, namespace='/widget')
        return False

    contact_id = payload['contact_id']
    org_id = payload['org_id']
    conversation_id = auth.get('conversation_id') if auth else None

    connected_widgets[sid] = {
        'contact_id': contact_id,
        'org_id': org_id,
        'conversation_id': conversation_id,
    }

    await sio.enter_room(sid, f'contact:{contact_id}', namespace='/widget')
    if conversation_id:
        await sio.enter_room(sid, f'conversation:{conversation_id}', namespace='/widget')

    # Notify agents
    await sio.emit(
        'contact:online',
        {'contact_id': contact_id, 'conversation_id': conversation_id},
        room=f'org:{org_id}',
        namespace='/agent',
    )
    logger.info(f"Widget contact {contact_id} connected")


@sio.on('disconnect', namespace='/widget')
async def widget_disconnect(sid):
    widget = connected_widgets.pop(sid, None)
    if widget:
        await sio.emit(
            'contact:offline',
            {
                'contact_id': widget['contact_id'],
                'last_seen_at': datetime.utcnow().isoformat(),
            },
            room=f'org:{widget["org_id"]}',
            namespace='/agent',
        )


@sio.on('typing:start', namespace='/widget')
async def widget_typing_start(sid, data):
    widget = connected_widgets.get(sid)
    if not widget:
        return
    conversation_id = data.get('conversation_id')
    if conversation_id:
        await sio.emit(
            'typing:start',
            {'conversation_id': conversation_id, 'sender_type': 'contact'},
            room=f'conversation:{conversation_id}',
            namespace='/agent',
        )


@sio.on('typing:stop', namespace='/widget')
async def widget_typing_stop(sid, data):
    widget = connected_widgets.get(sid)
    if not widget:
        return
    conversation_id = data.get('conversation_id')
    if conversation_id:
        await sio.emit(
            'typing:stop',
            {'conversation_id': conversation_id, 'sender_type': 'contact'},
            room=f'conversation:{conversation_id}',
            namespace='/agent',
        )


@sio.on('heartbeat', namespace='/widget')
async def widget_heartbeat(sid, data):
    pass


@sio.on('join:conversation', namespace='/widget')
async def widget_join_conversation(sid, data):
    conversation_id = data.get('conversation_id')
    if conversation_id:
        await sio.enter_room(sid, f'conversation:{conversation_id}', namespace='/widget')
        widget = connected_widgets.get(sid)
        if widget:
            widget['conversation_id'] = conversation_id
