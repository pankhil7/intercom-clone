import hmac
import hashlib
import logging
import time

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from sqlalchemy.orm import Session
from typing import Optional

from app.config import settings
from app.database import get_db
from app.services.email_service import process_inbound_email

router = APIRouter(prefix="/email", tags=["email"])
logger = logging.getLogger(__name__)


def _verify_mailgun_signature(timestamp: str, token: str, signature: str) -> bool:
    """
    Mailgun signs every inbound webhook with HMAC-SHA256.
    key  = MAILGUN_WEBHOOK_SIGNING_KEY  (from dashboard → Webhooks)
    msg  = timestamp + token
    Docs: https://documentation.mailgun.com/docs/mailgun/user-manual/webhooks/#verify-webhook-signings
    """
    if not settings.MAILGUN_WEBHOOK_SIGNING_KEY:
        # Signing key not configured — skip verification (dev only)
        logger.warning("MAILGUN_WEBHOOK_SIGNING_KEY not set; skipping signature check")
        return True

    # Reject replayed requests older than 5 minutes
    try:
        if abs(time.time() - int(timestamp)) > 300:
            logger.warning("Mailgun webhook timestamp too old — possible replay attack")
            return False
    except (ValueError, TypeError):
        return False

    computed = hmac.new(
        key=settings.MAILGUN_WEBHOOK_SIGNING_KEY.encode("utf-8"),
        msg=(timestamp + token).encode("utf-8"),
        digestmod=hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(computed, signature)


@router.post("/inbound")
async def inbound_email(
    request: Request,
    db: Session = Depends(get_db),
    # Mailgun sends multipart/form-data — these are the standard fields
    sender: Optional[str] = Form(default=None),        # From address
    recipient: Optional[str] = Form(default=None),     # To address (your inbox)
    subject: Optional[str] = Form(default=None),
    body_plain: Optional[str] = Form(default=None, alias="body-plain"),
    body_html: Optional[str] = Form(default=None, alias="body-html"),
    message_id: Optional[str] = Form(default=None, alias="Message-Id"),
    in_reply_to: Optional[str] = Form(default=None, alias="In-Reply-To"),
    references: Optional[str] = Form(default=None, alias="References"),
    # Mailgun signature fields
    timestamp: Optional[str] = Form(default=None),
    token: Optional[str] = Form(default=None),
    signature: Optional[str] = Form(default=None),
):
    # Verify the request genuinely came from Mailgun
    if not _verify_mailgun_signature(timestamp or "", token or "", signature or ""):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid Mailgun signature")

    # Normalise into the shape email_service expects
    payload = {
        "from_email": sender or "",
        "to_email": (recipient or "").lower().strip(),
        "subject": subject or "(no subject)",
        "plain": body_plain or "",
        "html": body_html or "",
        "message_id": (message_id or "").strip("<>").strip(),
        "in_reply_to": (in_reply_to or "").strip("<>").strip(),
        "references": references or "",
    }

    await process_inbound_email(db=db, payload=payload)
    return {"message": "ok"}
