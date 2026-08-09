import re
import json
import hmac
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Optional
from email.utils import parseaddr
import httpx
from sqlalchemy.orm import Session
from app.config import settings
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.contact import Contact
from app.models.inbox import Inbox

logger = logging.getLogger(__name__)


def parse_email_address(raw: str) -> tuple:
    """Returns (name, email) from 'Name <email@domain.com>' format."""
    name, email = parseaddr(raw)
    return name.strip(), email.strip().lower()


def normalize_subject(subject: str) -> str:
    """Strip Re:, Fwd:, etc. from subject."""
    return re.sub(r'^(re|fwd|fw|回复|转发):\s*', '', subject, flags=re.IGNORECASE).strip()


def parse_references(refs_str: str) -> list:
    """Parse References header into list of message IDs."""
    if not refs_str:
        return []
    return [r.strip('<>') for r in refs_str.split() if r.strip()]


def find_or_create_contact(db: Session, org_id, email: str, name: str = None) -> Contact:
    contact = None
    if email:
        contact = db.query(Contact).filter(
            Contact.organization_id == org_id,
            Contact.email == email.lower()
        ).first()
    if not contact:
        contact = Contact(
            organization_id=org_id,
            email=email.lower() if email else None,
            name=name or (email.split('@')[0] if email else 'Anonymous'),
            last_seen_at=datetime.utcnow()
        )
        db.add(contact)
        db.flush()
    elif name and not contact.name:
        contact.name = name
    return contact


async def process_inbound_email(db: Session, payload: dict):
    """Process a Cloudmailin inbound email payload."""
    try:
        headers = payload.get('headers', {})
        if isinstance(headers, str):
            headers = json.loads(headers)

        envelope = payload.get('envelope', {})
        plain = payload.get('plain', '')
        html = payload.get('html', '')

        message_id = headers.get('Message-ID', headers.get('message-id', '')).strip('<>').strip()
        in_reply_to = headers.get('In-Reply-To', headers.get('in-reply-to', '')).strip('<>').strip()
        references_raw = headers.get('References', headers.get('references', ''))
        references = parse_references(references_raw)

        from_raw = headers.get('From', headers.get('from', envelope.get('from', '')))
        from_name, from_email = parse_email_address(from_raw)

        to_email = envelope.get('to', headers.get('To', '')).lower().strip()
        subject = headers.get('Subject', headers.get('subject', '(no subject)')).strip()

        # Find inbox by email address
        inbox = db.query(Inbox).filter(
            Inbox.email_address == to_email,
            Inbox.channel_type == 'email',
            Inbox.is_active == True
        ).first()

        if not inbox:
            # Try matching any email inbox in any org (for demo purposes)
            inbox = db.query(Inbox).filter(
                Inbox.channel_type == 'email',
                Inbox.is_active == True
            ).first()

        if not inbox:
            logger.warning(f"No inbox found for {to_email}")
            return

        org_id = inbox.organization_id
        contact = find_or_create_contact(db, org_id, from_email, from_name)

        # Thread matching
        conversation = None

        # 1. Match by In-Reply-To
        if in_reply_to:
            existing = db.query(Message).filter(
                Message.email_message_id == in_reply_to
            ).join(Conversation).filter(
                Conversation.organization_id == org_id
            ).first()
            if existing:
                conversation = existing.conversation

        # 2. Match by References
        if not conversation and references:
            for ref_id in references:
                existing = db.query(Message).filter(
                    Message.email_message_id == ref_id
                ).join(Conversation).filter(
                    Conversation.organization_id == org_id
                ).first()
                if existing:
                    conversation = existing.conversation
                    break

        # 3. Match by normalized subject + contact + recent
        if not conversation:
            clean_subj = normalize_subject(subject).lower()
            cutoff = datetime.utcnow() - timedelta(days=30)
            recent = db.query(Conversation).filter(
                Conversation.organization_id == org_id,
                Conversation.contact_id == contact.id,
                Conversation.channel == 'email',
                Conversation.created_at > cutoff
            ).order_by(Conversation.created_at.desc()).all()
            for c in recent:
                if c.subject and normalize_subject(c.subject).lower() == clean_subj:
                    conversation = c
                    break

        # Create new conversation if no thread found
        if not conversation:
            conversation = Conversation(
                organization_id=org_id,
                contact_id=contact.id,
                channel='email',
                status='open',
                subject=normalize_subject(subject) or subject,
                inbox_id=inbox.id
            )
            db.add(conversation)
            db.flush()
        elif conversation.status == 'resolved':
            conversation.status = 'open'
            conversation.resolved_at = None

        content = html if html else plain
        message = Message(
            conversation_id=conversation.id,
            sender_type='contact',
            content=content,
            content_type='html' if html else 'text',
            email_message_id=message_id if message_id else None,
            email_in_reply_to=in_reply_to if in_reply_to else None,
            email_references=references if references else None,
        )
        db.add(message)
        conversation.updated_at = datetime.utcnow()
        db.commit()

        # Emit WebSocket event
        try:
            from app.socket.server import sio
            import asyncio
            data = {
                'conversation_id': str(conversation.id),
                'channel': 'email',
                'message': {
                    'id': str(message.id),
                    'content': message.content[:200],
                    'sender_type': 'contact',
                    'created_at': message.created_at.isoformat()
                }
            }
            asyncio.create_task(sio.emit('message:created', data, room=f'org:{org_id}'))
        except Exception as e:
            logger.error(f"WebSocket emit failed: {e}")

        logger.info(f"Processed inbound email for conversation {conversation.id}")

    except Exception as e:
        logger.error(f"Error processing inbound email: {e}", exc_info=True)
        raise


async def send_reply_email(
    to_email: str,
    subject: str,
    content: str,
    conversation_id,
    in_reply_to_message_id: str = None,
    references: list = None,
    our_message_id: str = None,
    from_name: str = "Support"
) -> bool:
    """Send an outbound email reply via Mailgun."""
    if not settings.MAILGUN_API_KEY or not settings.MAILGUN_DOMAIN:
        logger.warning("Mailgun not configured, skipping email send")
        return False

    from_email = settings.MAILGUN_FROM_EMAIL or f"support@{settings.MAILGUN_DOMAIN}"

    data = {
        'from': f"{from_name} <{from_email}>",
        'to': to_email,
        'subject': f"Re: {subject}" if not subject.startswith('Re:') else subject,
        'html': content,
        'h:Message-ID': f"<{our_message_id}>",
    }

    if in_reply_to_message_id:
        data['h:In-Reply-To'] = f"<{in_reply_to_message_id}>"

    if references:
        data['h:References'] = ' '.join(f"<{r}>" for r in references)

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://api.mailgun.net/v3/{settings.MAILGUN_DOMAIN}/messages",
                auth=("api", settings.MAILGUN_API_KEY),
                data=data,
                timeout=15.0
            )
            if response.status_code == 200:
                return True
            else:
                logger.error(f"Mailgun error: {response.status_code} {response.text}")
                return False
    except Exception as e:
        logger.error(f"Email send failed: {e}")
        return False
