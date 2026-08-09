from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.contact import Contact
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.page_view import PageView
from app.models.user import User
from app.schemas.contact import ContactCreate, ContactResponse, ContactUpdate

from app.logging_config import get_logger

router = APIRouter(prefix="/contacts", tags=["contacts"])
logger = get_logger(__name__)


@router.get("", response_model=List[ContactResponse])
def list_contacts(
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(Contact).filter(Contact.organization_id == current_user.organization_id)

    if search:
        pattern = f"%{search}%"
        q = q.filter(
            or_(
                Contact.email.ilike(pattern),
                Contact.name.ilike(pattern),
            )
        )

    offset = (page - 1) * limit
    contacts = q.order_by(Contact.created_at.desc()).offset(offset).limit(limit).all()
    return contacts


@router.post("", response_model=ContactResponse, status_code=status.HTTP_201_CREATED)
def create_contact(
    payload: ContactCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    contact = Contact(
        organization_id=current_user.organization_id,
        email=payload.email,
        name=payload.name,
        phone=payload.phone,
        external_id=payload.external_id,
        custom_attributes=payload.custom_attributes,
    )
    db.add(contact)
    db.commit()
    db.refresh(contact)
    logger.info("contact_created", contact_id=str(contact.id), org_id=str(current_user.organization_id))
    return contact


@router.get("/{contact_id}", response_model=ContactResponse)
def get_contact(
    contact_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    contact = db.query(Contact).filter(
        Contact.id == contact_id,
        Contact.organization_id == current_user.organization_id,
    ).first()
    if not contact:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    return contact


@router.patch("/{contact_id}", response_model=ContactResponse)
def update_contact(
    contact_id: UUID,
    payload: ContactUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    contact = db.query(Contact).filter(
        Contact.id == contact_id,
        Contact.organization_id == current_user.organization_id,
    ).first()
    if not contact:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")

    if payload.email is not None:
        contact.email = payload.email
    if payload.name is not None:
        contact.name = payload.name
    if payload.phone is not None:
        contact.phone = payload.phone
    if payload.external_id is not None:
        contact.external_id = payload.external_id
    if payload.custom_attributes is not None:
        contact.custom_attributes = {**(contact.custom_attributes or {}), **payload.custom_attributes}

    db.commit()
    db.refresh(contact)
    return contact


@router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_contact(
    contact_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    contact = db.query(Contact).filter(
        Contact.id == contact_id,
        Contact.organization_id == current_user.organization_id,
    ).first()
    if not contact:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")

    db.delete(contact)
    db.commit()


@router.get("/{contact_id}/conversations")
def get_contact_conversations(
    contact_id: UUID,
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    contact = db.query(Contact).filter(
        Contact.id == contact_id,
        Contact.organization_id == current_user.organization_id,
    ).first()
    if not contact:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")

    offset = (page - 1) * limit
    conversations = (
        db.query(Conversation)
        .filter(
            Conversation.contact_id == contact_id,
            Conversation.organization_id == current_user.organization_id,
        )
        .order_by(Conversation.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    return [
        {
            "id": str(c.id),
            "status": c.status,
            "channel": c.channel,
            "subject": c.subject,
            "created_at": c.created_at.isoformat(),
            "updated_at": c.updated_at.isoformat(),
        }
        for c in conversations
    ]


@router.get("/{contact_id}/timeline")
def get_contact_timeline(
    contact_id: UUID,
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    contact = db.query(Contact).filter(
        Contact.id == contact_id,
        Contact.organization_id == current_user.organization_id,
    ).first()
    if not contact:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")

    page_views = db.query(PageView).filter(PageView.contact_id == contact_id).all()
    conversations = (
        db.query(Conversation)
        .filter(
            Conversation.contact_id == contact_id,
            Conversation.organization_id == current_user.organization_id,
        )
        .all()
    )

    events: List[Dict[str, Any]] = []

    for pv in page_views:
        events.append(
            {
                "type": "page_view",
                "id": pv.id,
                "url": pv.url,
                "title": pv.title,
                "referrer": pv.referrer,
                "duration_seconds": pv.duration_seconds,
                "created_at": pv.created_at.isoformat(),
            }
        )

    for conv in conversations:
        events.append(
            {
                "type": "conversation",
                "id": str(conv.id),
                "status": conv.status,
                "channel": conv.channel,
                "subject": conv.subject,
                "created_at": conv.created_at.isoformat(),
            }
        )

    events.sort(key=lambda e: e["created_at"], reverse=True)

    offset = (page - 1) * limit
    return events[offset : offset + limit]
