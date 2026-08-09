import logging
from datetime import datetime
from app.socket.server import sio
from app.services.auth_service import decode_access_token

logger = logging.getLogger(__name__)

# Track online agents: {sid: {user_id, org_id}}
connected_agents = {}


@sio.on('connect', namespace='/agent')
async def agent_connect(sid, environ, auth):
    token = None
    if auth and isinstance(auth, dict):
        token = auth.get('token')

    if not token:
        await sio.disconnect(sid, namespace='/agent')
        return False

    payload = decode_access_token(token)
    if not payload:
        await sio.disconnect(sid, namespace='/agent')
        return False

    user_id = payload['sub']
    org_id = payload['org']

    connected_agents[sid] = {'user_id': user_id, 'org_id': org_id}

    await sio.enter_room(sid, f'org:{org_id}', namespace='/agent')
    await sio.enter_room(sid, f'agent:{user_id}', namespace='/agent')

    await sio.emit(
        'agent:online',
        {'user_id': user_id},
        room=f'org:{org_id}',
        namespace='/agent',
        skip_sid=sid,
    )
    logger.info(f"Agent {user_id} connected (sid={sid})")


@sio.on('disconnect', namespace='/agent')
async def agent_disconnect(sid):
    agent = connected_agents.pop(sid, None)
    if agent:
        await sio.emit(
            'agent:offline',
            {
                'user_id': agent['user_id'],
                'last_seen_at': datetime.utcnow().isoformat(),
            },
            room=f'org:{agent["org_id"]}',
            namespace='/agent',
        )
        logger.info(f"Agent {agent['user_id']} disconnected")


@sio.on('join:conversation', namespace='/agent')
async def join_conversation(sid, data):
    conversation_id = data.get('conversation_id')
    if conversation_id:
        await sio.enter_room(sid, f'conversation:{conversation_id}', namespace='/agent')
        return {'status': 'ok'}


@sio.on('leave:conversation', namespace='/agent')
async def leave_conversation(sid, data):
    conversation_id = data.get('conversation_id')
    if conversation_id:
        await sio.leave_room(sid, f'conversation:{conversation_id}', namespace='/agent')


@sio.on('typing:start', namespace='/agent')
async def agent_typing_start(sid, data):
    agent = connected_agents.get(sid)
    if not agent:
        return
    conversation_id = data.get('conversation_id')
    if conversation_id:
        await sio.emit(
            'typing:start',
            {
                'conversation_id': conversation_id,
                'sender_type': 'agent',
                'sender_id': agent['user_id'],
            },
            room=f'conversation:{conversation_id}',
            namespace='/widget',
            skip_sid=sid,
        )


@sio.on('typing:stop', namespace='/agent')
async def agent_typing_stop(sid, data):
    agent = connected_agents.get(sid)
    if not agent:
        return
    conversation_id = data.get('conversation_id')
    if conversation_id:
        await sio.emit(
            'typing:stop',
            {'conversation_id': conversation_id, 'sender_type': 'agent'},
            room=f'conversation:{conversation_id}',
            namespace='/widget',
            skip_sid=sid,
        )


@sio.on('message:mark_read', namespace='/agent')
async def mark_read(sid, data):
    from app.database import SessionLocal
    from app.models.message import Message
    from datetime import datetime

    db = SessionLocal()
    try:
        message_id = data.get('message_id')
        if message_id:
            msg = db.query(Message).filter(Message.id == message_id).first()
            if msg and not msg.is_read:
                msg.is_read = True
                msg.read_at = datetime.utcnow()
                db.commit()

                await sio.emit(
                    'message:read',
                    {'message_id': message_id, 'read_at': msg.read_at.isoformat()},
                    room=f'conversation:{msg.conversation_id}',
                    namespace='/widget',
                )
    finally:
        db.close()


@sio.on('heartbeat', namespace='/agent')
async def heartbeat(sid, data):
    pass  # Keep-alive, no action needed
