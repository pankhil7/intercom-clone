import logging
import asyncio
from datetime import datetime, timedelta
from app.database import SessionLocal
from app.models.conversation import Conversation
from app.models.sla_policy import SLAPolicy
from app.socket.server import sio

logger = logging.getLogger(__name__)


async def check_sla_breaches():
    db = SessionLocal()
    try:
        now = datetime.utcnow()
        conversations = (
            db.query(Conversation)
            .filter(
                Conversation.status.in_(['open', 'snoozed']),
                Conversation.sla_policy_id != None,
                Conversation.sla_breach == False,
            )
            .all()
        )

        for conv in conversations:
            policy = db.query(SLAPolicy).filter(SLAPolicy.id == conv.sla_policy_id).first()
            if not policy:
                continue

            first_response_deadline = conv.created_at + timedelta(
                hours=policy.first_response_hours
            )
            breached = False

            if not conv.first_response_at and now > first_response_deadline:
                breached = True

            resolution_deadline = conv.created_at + timedelta(hours=policy.resolution_hours)
            if conv.status != 'resolved' and now > resolution_deadline:
                breached = True

            if breached:
                conv.sla_breach = True
                db.flush()
                try:
                    await sio.emit(
                        'sla:breach',
                        {
                            'conversation_id': str(conv.id),
                            'breach_type': (
                                'first_response' if not conv.first_response_at else 'resolution'
                            ),
                            'breached_at': now.isoformat(),
                        },
                        room=f'org:{conv.organization_id}',
                        namespace='/agent',
                    )
                except Exception:
                    pass

        db.commit()
    except Exception as e:
        logger.error(f"SLA checker error: {e}")
        db.rollback()
    finally:
        db.close()
