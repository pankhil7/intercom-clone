import asyncio
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.contact import Contact
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.user import User
from app.schemas.conversation import (
    AssigneeMini,
    ContactMini,
    ConversationCreate,
    ConversationDetail,
    ConversationListItem,
    ConversationUpdate,
    MessageCreate,
    MessageResponse,
)
from app.services.email_service import send_reply_email
from app.services.webhook_service import fire_event
from app.socket.server import sio

router = APIRouter(prefix="/conversations", tags=["conversations"])


def _build_list_item(conv: Conversation, db: Session) -> ConversationListItem:
    last_message = (
        db.query(Message)
        .filter(Message.conversation_id == conv.id)
        .order_by(Message.created_at.desc())
        .first()
    )

    unread_count = (
        db.query(func.count(Message.id))
        .filter(
            Message.conversation_id == conv.id,
            Message.is_read == False,
            Message.sender_type == "contact",
        )
        .scalar()
        or 0
    )

    contact_mini = None
    if conv.contact:
        contact_mini = ContactMini(
            id=conv.contact.id,
            email=conv.contact.email,
            name=conv.contact.name,
        )

    assignee_mini = None
    if conv.assignee:
        assignee_mini = AssigneeMini(
            id=conv.assignee.id,
            full_name=conv.assignee.full_name,
            email=conv.assignee.email,
            avatar_url=conv.assignee.avatar_url,
        )

    return ConversationListItem(
        id=conv.id,
        status=conv.status,
        channel=conv.channel,
        subject=conv.subject,
        contact=contact_mini,
        assignee=assignee_mini,
        last_message=MessageResponse.model_validate(last_message) if last_message else None,
        unread_count=unread_count,
        sla_breach=conv.sla_breach,
        created_at=conv.created_at,
        updated_at=conv.updated_at,
    )


@router.get("", response_model=List[ConversationListItem])
def list_conversations(
    status_filter: Optional[str] = Query(None, alias="status"),
    channel: Optional[str] = None,
    assigned_to: Optional[str] = None,
    inbox_id: Optional[UUID] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(Conversation).filter(
        Conversation.organization_id == current_user.organization_id
    )

    if status_filter:
        q = q.filter(Conversation.status == status_filter)
    if channel:
        q = q.filter(Conversation.channel == channel)
    if inbox_id:
        q = q.filter(Conversation.inbox_id == inbox_id)

    if assigned_to:
        if assigned_to == "me":
            q = q.filter(Conversation.assigned_to == current_user.id)
        elif assigned_to == "unassigned":
            q = q.filter(Conversation.assigned_to == None)
        else:
            try:
                assigned_uuid = UUID(assigned_to)
                q = q.filter(Conversation.assigned_to == assigned_uuid)
            except ValueError:
                pass

    q = q.order_by(Conversation.updated_at.desc())
    offset = (page - 1) * limit
    conversations = q.offset(offset).limit(limit).all()

    return [_build_list_item(conv, db) for conv in conversations]


@router.post("", response_model=ConversationListItem, status_code=status.HTTP_201_CREATED)
def create_conversation(
    payload: ConversationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if payload.contact_id:
        contact = db.query(Contact).filter(
            Contact.id == payload.contact_id,
            Contact.organization_id == current_user.organization_id,
        ).first()
        if not contact:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")

    if payload.assigned_to:
        assignee = db.query(User).filter(
            User.id == payload.assigned_to,
            User.organization_id == current_user.organization_id,
        ).first()
        if not assignee:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignee not found")

    conv = Conversation(
        organization_id=current_user.organization_id,
        contact_id=payload.contact_id,
        channel=payload.channel,
        subject=payload.subject,
        inbox_id=payload.inbox_id,
        assigned_to=payload.assigned_to,
    )
    db.add(conv)
    db.commit()
    db.refresh(conv)

    asyncio.create_task(
        sio.emit(
            "conversation_created",
            {"conversation_id": str(conv.id)},
            room=str(current_user.organization_id),
        )
    )
    asyncio.create_task(
        fire_event(
            str(current_user.organization_id),
            "conversation.created",
            {"id": str(conv.id)},
        )
    )

    return _build_list_item(conv, db)


@router.get("/{conversation_id}", response_model=ConversationDetail)
def get_conversation(
    conversation_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    conv = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.organization_id == current_user.organization_id,
    ).first()
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    messages = (
        db.query(Message)
        .filter(Message.conversation_id == conv.id)
        .order_by(Message.created_at)
        .limit(50)
        .all()
    )

    last_message = messages[-1] if messages else None

    unread_count = (
        db.query(func.count(Message.id))
        .filter(
            Message.conversation_id == conv.id,
            Message.is_read == False,
            Message.sender_type == "contact",
        )
        .scalar()
        or 0
    )

    contact_mini = None
    if conv.contact:
        contact_mini = ContactMini(
            id=conv.contact.id,
            email=conv.contact.email,
            name=conv.contact.name,
        )

    assignee_mini = None
    if conv.assignee:
        assignee_mini = AssigneeMini(
            id=conv.assignee.id,
            full_name=conv.assignee.full_name,
            email=conv.assignee.email,
            avatar_url=conv.assignee.avatar_url,
        )

    return ConversationDetail(
        id=conv.id,
        status=conv.status,
        channel=conv.channel,
        subject=conv.subject,
        contact=contact_mini,
        assignee=assignee_mini,
        last_message=MessageResponse.model_validate(last_message) if last_message else None,
        unread_count=unread_count,
        sla_breach=conv.sla_breach,
        created_at=conv.created_at,
        updated_at=conv.updated_at,
        messages=[MessageResponse.model_validate(m) for m in messages],
    )


@router.patch("/{conversation_id}", response_model=ConversationListItem)
def update_conversation(
    conversation_id: UUID,
    payload: ConversationUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    conv = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.organization_id == current_user.organization_id,
    ).first()
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    if payload.status is not None:
        conv.status = payload.status
        if payload.status == "resolved":
            conv.resolved_at = datetime.utcnow()
    if payload.assigned_to is not None:
        conv.assigned_to = payload.assigned_to
    if payload.snoozed_until is not None:
        conv.snoozed_until = payload.snoozed_until
        conv.status = "snoozed"
    if payload.subject is not None:
        conv.subject = payload.subject
    if payload.sla_policy_id is not None:
        conv.sla_policy_id = payload.sla_policy_id

    db.commit()
    db.refresh(conv)

    asyncio.create_task(
        sio.emit(
            "conversation_updated",
            {"conversation_id": str(conv.id)},
            room=str(current_user.organization_id),
        )
    )

    return _build_list_item(conv, db)


@router.post("/{conversation_id}/messages", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
def send_message(
    conversation_id: UUID,
    payload: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    conv = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.organization_id == current_user.organization_id,
    ).first()
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    is_first_agent_message = conv.first_response_at is None

    msg = Message(
        conversation_id=conv.id,
        sender_type="agent",
        sender_id=current_user.id,
        content=payload.content,
        content_type=payload.content_type,
    )
    db.add(msg)

    if is_first_agent_message:
        conv.first_response_at = datetime.utcnow()

    conv.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(msg)

    if conv.channel == "email":
        asyncio.create_task(
            send_reply_email(conversation=conv, message=msg, db=db)
        )

    asyncio.create_task(
        sio.emit(
            "new_message",
            {
                "conversation_id": str(conv.id),
                "message_id": str(msg.id),
            },
            room=str(current_user.organization_id),
        )
    )
    asyncio.create_task(
        fire_event(
            str(current_user.organization_id),
            "message.created",
            {"conversation_id": str(conv.id), "message_id": str(msg.id)},
        )
    )

    return MessageResponse.model_validate(msg)


@router.get("/{conversation_id}/messages", response_model=List[MessageResponse])
def get_messages(
    conversation_id: UUID,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    before_id: Optional[UUID] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    conv = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.organization_id == current_user.organization_id,
    ).first()
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    q = db.query(Message).filter(Message.conversation_id == conversation_id)

    if before_id:
        pivot = db.query(Message).filter(Message.id == before_id).first()
        if pivot:
            q = q.filter(Message.created_at < pivot.created_at)

    messages = q.order_by(Message.created_at.desc()).limit(limit).all()
    messages.reverse()
    return [MessageResponse.model_validate(m) for m in messages]


@router.post("/{conversation_id}/assign", response_model=ConversationListItem)
def assign_conversation(
    conversation_id: UUID,
    body: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    conv = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.organization_id == current_user.organization_id,
    ).first()
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    user_id = body.get("user_id")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="user_id is required")

    assignee = db.query(User).filter(
        User.id == user_id,
        User.organization_id == current_user.organization_id,
    ).first()
    if not assignee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    conv.assigned_to = assignee.id
    conv.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(conv)

    asyncio.create_task(
        sio.emit(
            "conversation_assigned",
            {"conversation_id": str(conv.id), "assigned_to": str(assignee.id)},
            room=str(current_user.organization_id),
        )
    )

    return _build_list_item(conv, db)


@router.post("/{conversation_id}/unassign", response_model=ConversationListItem)
def unassign_conversation(
    conversation_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    conv = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.organization_id == current_user.organization_id,
    ).first()
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    conv.assigned_to = None
    conv.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(conv)

    asyncio.create_task(
        sio.emit(
            "conversation_unassigned",
            {"conversation_id": str(conv.id)},
            room=str(current_user.organization_id),
        )
    )

    return _build_list_item(conv, db)


@router.post("/{conversation_id}/resolve", response_model=ConversationListItem)
def resolve_conversation(
    conversation_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    conv = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.organization_id == current_user.organization_id,
    ).first()
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    conv.status = "resolved"
    conv.resolved_at = datetime.utcnow()
    conv.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(conv)

    asyncio.create_task(
        sio.emit(
            "conversation_resolved",
            {"conversation_id": str(conv.id)},
            room=str(current_user.organization_id),
        )
    )
    asyncio.create_task(
        fire_event(
            str(current_user.organization_id),
            "conversation.resolved",
            {"id": str(conv.id)},
        )
    )

    return _build_list_item(conv, db)


@router.post("/{conversation_id}/reopen", response_model=ConversationListItem)
def reopen_conversation(
    conversation_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    conv = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.organization_id == current_user.organization_id,
    ).first()
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    conv.status = "open"
    conv.resolved_at = None
    conv.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(conv)

    asyncio.create_task(
        sio.emit(
            "conversation_reopened",
            {"conversation_id": str(conv.id)},
            room=str(current_user.organization_id),
        )
    )

    return _build_list_item(conv, db)
