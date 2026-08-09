import secrets
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_admin, get_current_user
from app.models.inbox import Inbox
from app.models.user import User

from app.logging_config import get_logger

router = APIRouter(prefix="/inboxes", tags=["inboxes"])
logger = get_logger(__name__)


class InboxCreate(BaseModel):
    name: str
    channel: str  # chat | email
    email_address: Optional[str] = None


class InboxUpdate(BaseModel):
    name: Optional[str] = None
    email_address: Optional[str] = None
    is_active: Optional[bool] = None


def _inbox_dict(inbox: Inbox) -> dict:
    return {
        "id": str(inbox.id),
        "organization_id": str(inbox.organization_id),
        "name": inbox.name,
        "channel": inbox.channel,
        "email_address": inbox.email_address,
        "widget_key": inbox.widget_key,
        "is_active": inbox.is_active,
        "created_at": inbox.created_at.isoformat(),
    }


@router.get("")
def list_inboxes(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    inboxes = (
        db.query(Inbox)
        .filter(Inbox.organization_id == current_user.organization_id)
        .order_by(Inbox.created_at)
        .all()
    )
    return {"inboxes": [_inbox_dict(i) for i in inboxes]}


@router.post("", status_code=status.HTTP_201_CREATED)
def create_inbox(
    payload: InboxCreate,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    widget_key = None
    if payload.channel == "chat":
        widget_key = secrets.token_urlsafe(32)

    inbox = Inbox(
        organization_id=current_user.organization_id,
        name=payload.name,
        channel=payload.channel,
        email_address=payload.email_address,
        widget_key=widget_key,
    )
    db.add(inbox)
    db.commit()
    db.refresh(inbox)
    logger.info("inbox_created", inbox_id=str(inbox.id), channel=inbox.channel, org_id=str(current_user.organization_id))
    return {"inbox": _inbox_dict(inbox)}


@router.patch("/{inbox_id}")
def update_inbox(
    inbox_id: UUID,
    payload: InboxUpdate,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    inbox = db.query(Inbox).filter(
        Inbox.id == inbox_id,
        Inbox.organization_id == current_user.organization_id,
    ).first()
    if not inbox:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inbox not found")

    if payload.name is not None:
        inbox.name = payload.name
    if payload.email_address is not None:
        inbox.email_address = payload.email_address
    if payload.is_active is not None:
        inbox.is_active = payload.is_active

    db.commit()
    db.refresh(inbox)
    return {"inbox": _inbox_dict(inbox)}


@router.delete("/{inbox_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_inbox(
    inbox_id: UUID,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    inbox = db.query(Inbox).filter(
        Inbox.id == inbox_id,
        Inbox.organization_id == current_user.organization_id,
    ).first()
    if not inbox:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inbox not found")

    db.delete(inbox)
    db.commit()
