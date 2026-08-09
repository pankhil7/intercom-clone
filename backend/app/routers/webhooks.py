import asyncio
import hashlib
import hmac
import secrets
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_admin, get_current_user
from app.models.user import User
from app.models.webhook import Webhook
from app.models.webhook_delivery import WebhookDelivery
from app.schemas.webhook import DeliveryResponse, WebhookCreate, WebhookResponse, WebhookUpdate
from app.services.webhook_service import fire_event

from app.logging_config import get_logger

router = APIRouter(prefix="/webhooks", tags=["webhooks"])
logger = get_logger(__name__)


@router.get("", response_model=List[WebhookResponse])
def list_webhooks(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(Webhook)
        .filter(Webhook.organization_id == current_user.organization_id)
        .order_by(Webhook.created_at.desc())
        .all()
    )


@router.post("", response_model=WebhookResponse, status_code=status.HTTP_201_CREATED)
def create_webhook(
    payload: WebhookCreate,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    secret = payload.secret or secrets.token_hex(32)

    webhook = Webhook(
        organization_id=current_user.organization_id,
        url=payload.url,
        secret=secret,
        events=payload.events,
    )
    db.add(webhook)
    db.commit()
    db.refresh(webhook)
    logger.info("webhook_created", webhook_id=str(webhook.id), events=payload.events, org_id=str(current_user.organization_id))
    return webhook


@router.patch("/{webhook_id}", response_model=WebhookResponse)
def update_webhook(
    webhook_id: UUID,
    payload: WebhookUpdate,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    webhook = db.query(Webhook).filter(
        Webhook.id == webhook_id,
        Webhook.organization_id == current_user.organization_id,
    ).first()
    if not webhook:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Webhook not found")

    if payload.url is not None:
        webhook.url = payload.url
    if payload.events is not None:
        webhook.events = payload.events
    if payload.is_active is not None:
        webhook.is_active = payload.is_active

    db.commit()
    db.refresh(webhook)
    return webhook


@router.delete("/{webhook_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_webhook(
    webhook_id: UUID,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    webhook = db.query(Webhook).filter(
        Webhook.id == webhook_id,
        Webhook.organization_id == current_user.organization_id,
    ).first()
    if not webhook:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Webhook not found")

    db.delete(webhook)
    db.commit()
    logger.info("webhook_deleted", webhook_id=str(webhook_id), org_id=str(current_user.organization_id))


@router.get("/{webhook_id}/deliveries", response_model=List[DeliveryResponse])
def list_deliveries(
    webhook_id: UUID,
    page: int = 1,
    limit: int = 25,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    webhook = db.query(Webhook).filter(
        Webhook.id == webhook_id,
        Webhook.organization_id == current_user.organization_id,
    ).first()
    if not webhook:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Webhook not found")

    offset = (page - 1) * limit
    deliveries = (
        db.query(WebhookDelivery)
        .filter(WebhookDelivery.webhook_id == webhook_id)
        .order_by(WebhookDelivery.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return deliveries


@router.post("/{webhook_id}/test")
async def test_webhook(
    webhook_id: UUID,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    webhook = db.query(Webhook).filter(
        Webhook.id == webhook_id,
        Webhook.organization_id == current_user.organization_id,
    ).first()
    if not webhook:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Webhook not found")

    asyncio.create_task(
        fire_event(
            str(current_user.organization_id),
            "test",
            {"message": "This is a test event from your Intercom clone."},
        )
    )

    return {"message": "Test event dispatched"}
