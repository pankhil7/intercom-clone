import json
import hmac
import hashlib
import time
import logging
import asyncio
from datetime import datetime, timedelta
from uuid import uuid4
import httpx
from sqlalchemy.orm import Session
from app.models.webhook import Webhook
from app.models.webhook_delivery import WebhookDelivery

logger = logging.getLogger(__name__)

RETRY_DELAYS = [60, 300, 900, 3600, 7200]  # 1m, 5m, 15m, 1h, 2h


def sign_payload(secret: str, body: str) -> str:
    return hmac.new(secret.encode(), body.encode(), hashlib.sha256).hexdigest()


async def fire_event(db: Session, org_id, event_type: str, payload: dict):
    """Find all active webhooks subscribed to this event and deliver."""
    webhooks = db.query(Webhook).filter(
        Webhook.organization_id == org_id,
        Webhook.is_active == True,
        Webhook.events.contains([event_type]),
    ).all()

    for webhook in webhooks:
        asyncio.create_task(_deliver(db, str(webhook.id), event_type, payload, attempt=1))


async def _deliver(
    db: Session, webhook_id: str, event_type: str, payload: dict, attempt: int = 1
):
    from app.database import SessionLocal

    db = SessionLocal()
    try:
        webhook = db.query(Webhook).filter(Webhook.id == webhook_id).first()
        if not webhook or not webhook.is_active:
            return

        body = json.dumps(
            {
                "id": str(uuid4()),
                "event": event_type,
                "created_at": datetime.utcnow().isoformat(),
                "data": payload,
            }
        )
        signature = sign_payload(webhook.secret, body)

        delivery = WebhookDelivery(
            webhook_id=webhook.id,
            event_type=event_type,
            payload=payload,
            attempt_count=attempt,
        )
        db.add(delivery)
        db.flush()

        start = time.monotonic()
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    webhook.url,
                    content=body,
                    headers={
                        "Content-Type": "application/json",
                        "X-Webhook-Signature": f"sha256={signature}",
                        "X-Webhook-Event": event_type,
                        "X-Delivery-ID": str(delivery.id),
                        "User-Agent": "IntercomClone-Webhooks/1.0",
                    },
                )
            duration_ms = int((time.monotonic() - start) * 1000)
            delivery.response_status = response.status_code
            delivery.response_body = response.text[:1000]
            delivery.duration_ms = duration_ms
            delivery.delivered_at = datetime.utcnow()

            if 200 <= response.status_code < 300:
                webhook.last_triggered_at = datetime.utcnow()
                webhook.failure_count = 0
            else:
                raise Exception(f"HTTP {response.status_code}")

        except Exception as e:
            logger.error(f"Webhook delivery failed (attempt {attempt}): {e}")
            webhook.failure_count = (webhook.failure_count or 0) + 1
            if attempt <= 5:
                delay = RETRY_DELAYS[min(attempt - 1, len(RETRY_DELAYS) - 1)]
                delivery.next_retry_at = datetime.utcnow() + timedelta(seconds=delay)
            if webhook.failure_count >= 50:
                webhook.is_active = False
                logger.warning(f"Webhook {webhook_id} disabled after 50 failures")

        db.commit()
    except Exception as e:
        logger.error(f"Webhook service error: {e}")
        db.rollback()
    finally:
        db.close()


async def retry_pending_deliveries():
    """Called by background job every minute."""
    from app.database import SessionLocal

    db = SessionLocal()
    try:
        now = datetime.utcnow()
        due = (
            db.query(WebhookDelivery)
            .filter(
                WebhookDelivery.next_retry_at <= now,
                WebhookDelivery.response_status == None,
            )
            .limit(50)
            .all()
        )

        for delivery in due:
            delivery.next_retry_at = None
            db.flush()
            asyncio.create_task(
                _deliver(
                    db,
                    str(delivery.webhook_id),
                    delivery.event_type,
                    delivery.payload,
                    attempt=delivery.attempt_count + 1,
                )
            )
        db.commit()
    finally:
        db.close()
