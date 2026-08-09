import asyncio
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_widget_session
from app.models.contact import Contact
from app.models.conversation import Conversation
from app.models.kb_article import KBArticle
from app.models.message import Message
from app.models.organization import Organization
from app.models.page_view import PageView
from app.services.auth_service import create_widget_session_token
from app.socket.server import sio

router = APIRouter(prefix="/widget", tags=["widget"])


# ---------------------------------------------------------------------------
# Request / Response schemas (local, widget-specific)
# ---------------------------------------------------------------------------

class SessionRequest(BaseModel):
    # Accept either widget_key (new) or organization_slug (legacy)
    widget_key: Optional[str] = None
    organization_slug: Optional[str] = None
    visitor_id: Optional[str] = None
    email: Optional[str] = None
    name: Optional[str] = None


class SessionResponse(BaseModel):
    session_token: str
    token: str  # alias for JS client
    contact_id: str
    conversation_id: Optional[str] = None
    socket_url: str


class IdentifyRequest(BaseModel):
    email: Optional[str] = None
    name: Optional[str] = None
    user_id: Optional[str] = None
    custom_attributes: Optional[dict] = None


class WidgetContactResponse(BaseModel):
    id: str
    email: Optional[str] = None
    name: Optional[str] = None
    custom_attributes: Optional[dict] = None


class WidgetConversationCreate(BaseModel):
    message: str
    inbox_id: Optional[UUID] = None


class WidgetConversationResponse(BaseModel):
    conversation_id: str
    session_token: str


class PageViewRequest(BaseModel):
    url: str
    title: Optional[str] = None
    referrer: Optional[str] = None
    session_id: str


class PageLeaveRequest(BaseModel):
    url: str
    duration_seconds: int
    session_id: str


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.post("/sessions", status_code=status.HTTP_201_CREATED)
def create_session(
    payload: SessionRequest,
    db: Session = Depends(get_db),
):
    from app.models.inbox import Inbox

    # Resolve organization via widget_key or slug
    org = None
    if payload.widget_key:
        inbox = db.query(Inbox).filter(Inbox.widget_key == payload.widget_key).first()
        if inbox:
            org = db.query(Organization).filter(Organization.id == inbox.organization_id).first()
    if not org and payload.organization_slug:
        org = db.query(Organization).filter(Organization.slug == payload.organization_slug).first()
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")

    contact = None
    if payload.visitor_id:
        contact = db.query(Contact).filter(
            Contact.visitor_id == payload.visitor_id,
            Contact.organization_id == org.id,
        ).first()
    if not contact and payload.email:
        contact = db.query(Contact).filter(
            Contact.email == payload.email,
            Contact.organization_id == org.id,
        ).first()

    if not contact:
        contact = Contact(
            organization_id=org.id,
            visitor_id=payload.visitor_id,
            email=payload.email,
            name=payload.name,
        )
        db.add(contact)
        db.commit()
        db.refresh(contact)
    elif payload.email and not contact.email:
        contact.email = payload.email
        if payload.name:
            contact.name = payload.name
        db.commit()

    session_token = create_widget_session_token(
        contact_id=str(contact.id),
        org_id=str(org.id),
        visitor_id=payload.visitor_id or str(contact.id),
    )

    return {
        "session_token": session_token,
        "token": session_token,  # alias for JS client
        "contact_id": str(contact.id),
        "conversation_id": None,
        "socket_url": "/socket.io",
    }


@router.post("/identify", response_model=WidgetContactResponse)
def identify(
    payload: IdentifyRequest,
    session: dict = Depends(get_widget_session),
    db: Session = Depends(get_db),
):
    contact = db.query(Contact).filter(Contact.id == session["contact_id"]).first()
    if not contact:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")

    if payload.email is not None:
        contact.email = payload.email
    if payload.name is not None:
        contact.name = payload.name
    if payload.user_id is not None:
        contact.external_id = payload.user_id
    if payload.custom_attributes:
        contact.custom_attributes = {**(contact.custom_attributes or {}), **payload.custom_attributes}

    contact.last_seen_at = datetime.utcnow()
    db.commit()
    db.refresh(contact)

    return WidgetContactResponse(
        id=str(contact.id),
        email=contact.email,
        name=contact.name,
        custom_attributes=contact.custom_attributes,
    )


@router.post("/conversations", response_model=WidgetConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_widget_conversation(
    payload: WidgetConversationCreate,
    session: dict = Depends(get_widget_session),
    db: Session = Depends(get_db),
):
    contact_id = session["contact_id"]
    org_id = session["org_id"]

    contact = db.query(Contact).filter(
        Contact.id == contact_id,
        Contact.organization_id == org_id,
    ).first()
    if not contact:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")

    conv = Conversation(
        organization_id=org_id,
        contact_id=contact.id,
        channel="chat",
        inbox_id=payload.inbox_id,
    )
    db.add(conv)
    db.flush()

    msg = Message(
        conversation_id=conv.id,
        sender_type="contact",
        sender_id=contact.id,
        content=payload.message,
        content_type="text",
    )
    db.add(msg)
    db.commit()
    db.refresh(conv)

    asyncio.create_task(
        sio.emit(
            "new_conversation",
            {
                "conversation_id": str(conv.id),
                "contact_id": str(contact.id),
            },
            room=str(org_id),
        )
    )

    new_session_token = create_widget_session_token(
        contact_id=str(contact.id),
        org_id=str(org_id),
        visitor_id=session.get("visitor_id", str(contact.id)),
    )

    return WidgetConversationResponse(
        conversation_id=str(conv.id),
        session_token=new_session_token,
    )


@router.get("/conversations")
def list_widget_conversations(
    session: dict = Depends(get_widget_session),
    db: Session = Depends(get_db),
):
    contact_id = session["contact_id"]
    org_id = session["org_id"]

    conversations = (
        db.query(Conversation)
        .filter(
            Conversation.contact_id == contact_id,
            Conversation.organization_id == org_id,
        )
        .order_by(Conversation.updated_at.desc())
        .all()
    )

    result = []
    for conv in conversations:
        last_message = (
            db.query(Message)
            .filter(Message.conversation_id == conv.id)
            .order_by(Message.created_at.desc())
            .first()
        )
        result.append(
            {
                "id": str(conv.id),
                "status": conv.status,
                "channel": conv.channel,
                "subject": conv.subject,
                "last_message": {
                    "content": last_message.content,
                    "sender_type": last_message.sender_type,
                    "created_at": last_message.created_at.isoformat(),
                }
                if last_message
                else None,
                "created_at": conv.created_at.isoformat(),
                "updated_at": conv.updated_at.isoformat(),
            }
        )

    return result


@router.get("/conversations/{conversation_id}/messages")
def get_widget_conversation_messages(
    conversation_id: UUID,
    session: dict = Depends(get_widget_session),
    db: Session = Depends(get_db),
):
    contact_id = session["contact_id"]
    org_id = session["org_id"]

    conv = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.contact_id == contact_id,
        Conversation.organization_id == org_id,
    ).first()
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    messages = (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.created_at)
        .all()
    )

    return [
        {
            "id": str(m.id),
            "sender_type": m.sender_type,
            "content": m.content,
            "content_type": m.content_type,
            "attachments": m.attachments,
            "is_read": m.is_read,
            "created_at": m.created_at.isoformat(),
        }
        for m in messages
    ]


@router.post("/page-view")
def track_page_view(
    payload: PageViewRequest,
    session: dict = Depends(get_widget_session),
    db: Session = Depends(get_db),
):
    contact_id = session["contact_id"]

    pv = PageView(
        contact_id=contact_id,
        session_id=payload.session_id,
        url=payload.url,
        title=payload.title,
        referrer=payload.referrer,
    )
    db.add(pv)

    # Update contact's last_seen_at
    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if contact:
        contact.last_seen_at = datetime.utcnow()

    db.commit()
    return {"message": "ok"}


@router.post("/page-leave")
def track_page_leave(
    payload: PageLeaveRequest,
    session: dict = Depends(get_widget_session),
    db: Session = Depends(get_db),
):
    contact_id = session["contact_id"]

    # Update the most recent matching PageView for this session+url
    pv = (
        db.query(PageView)
        .filter(
            PageView.contact_id == contact_id,
            PageView.session_id == payload.session_id,
            PageView.url == payload.url,
        )
        .order_by(PageView.created_at.desc())
        .first()
    )

    if pv:
        pv.duration_seconds = payload.duration_seconds
        db.commit()

    return {"message": "ok"}


@router.post("/session")
def create_session_v2(
    payload: SessionRequest,
    db: Session = Depends(get_db),
):
    """Alias for /sessions (singular) used by the widget JS client."""
    return create_session(payload, db)


class SendMessageRequest(BaseModel):
    content: str
    sender_type: str = "contact"


@router.post("/conversations/{conversation_id}/messages")
async def send_widget_message(
    conversation_id: UUID,
    payload: SendMessageRequest,
    session: dict = Depends(get_widget_session),
    db: Session = Depends(get_db),
):
    contact_id = session["contact_id"]
    org_id = session["org_id"]

    conv = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.contact_id == contact_id,
        Conversation.organization_id == org_id,
    ).first()
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    msg = Message(
        conversation_id=conv.id,
        organization_id=org_id,
        sender_type="contact",
        sender_id=contact_id,
        content=payload.content,
        content_type="text",
    )
    db.add(msg)
    conv.last_activity_at = datetime.utcnow()
    db.commit()
    db.refresh(msg)

    asyncio.create_task(
        sio.emit(
            "message:created",
            {
                "id": str(msg.id),
                "conversation_id": str(conv.id),
                "sender_type": "contact",
                "content": msg.content,
                "created_at": msg.created_at.isoformat(),
            },
            room=f"conversation:{conv.id}",
        )
    )

    return {"message": {"id": str(msg.id), "content": msg.content, "sender_type": "contact", "created_at": msg.created_at.isoformat()}}


@router.post("/page-views")
def track_page_view_v2(
    payload: PageViewRequest,
    session: dict = Depends(get_widget_session),
    db: Session = Depends(get_db),
):
    """Alias for /page-view used by the widget JS client."""
    return track_page_view(payload, session, db)


@router.get("/kb/search")
def widget_kb_search(
    q: str = Query(..., min_length=1),
    org: Optional[str] = Query(None),
    limit: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db),
):
    query = db.query(KBArticle).filter(KBArticle.status == "published")

    if org:
        organization = db.query(Organization).filter(Organization.slug == org).first()
        if organization:
            query = query.filter(KBArticle.organization_id == organization.id)

    articles = (
        query.filter(
            KBArticle.search_vector.op("@@")(func.to_tsquery("english", q))
        )
        .order_by(
            func.ts_rank(KBArticle.search_vector, func.to_tsquery("english", q)).desc()
        )
        .limit(limit)
        .all()
    )

    return [
        {
            "id": str(a.id),
            "title": a.title,
            "excerpt": (a.content_text or "")[:200],
            "slug": a.slug,
        }
        for a in articles
    ]
