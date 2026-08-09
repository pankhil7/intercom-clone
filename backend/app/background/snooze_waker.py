import logging
from datetime import datetime
from app.database import SessionLocal
from app.models.conversation import Conversation
from app.socket.server import sio

logger = logging.getLogger(__name__)


async def wake_snoozed_conversations():
    db = SessionLocal()
    try:
        now = datetime.utcnow()
        snoozed = (
            db.query(Conversation)
            .filter(
                Conversation.status == 'snoozed',
                Conversation.snoozed_until <= now,
            )
            .all()
        )

        for conv in snoozed:
            conv.status = 'open'
            conv.snoozed_until = None
            db.flush()
            try:
                await sio.emit(
                    'conversation:updated',
                    {'conversation_id': str(conv.id), 'changes': {'status': 'open'}},
                    room=f'org:{conv.organization_id}',
                    namespace='/agent',
                )
            except Exception:
                pass

        db.commit()
    except Exception as e:
        logger.error(f"Snooze waker error: {e}")
        db.rollback()
    finally:
        db.close()
