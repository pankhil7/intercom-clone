import json
from typing import Optional

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.email_service import process_inbound_email

router = APIRouter(prefix="/email", tags=["email"])


@router.post("/inbound")
async def inbound_email(
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Cloudmailin webhook endpoint.
    Expects multipart form data with: headers (JSON string), envelope (JSON string), plain, html.
    """
    content_type = request.headers.get("content-type", "")

    headers_data = {}
    envelope_data = {}
    plain_body = ""
    html_body = ""

    if "multipart/form-data" in content_type or "application/x-www-form-urlencoded" in content_type:
        form = await request.form()

        raw_headers = form.get("headers", "{}")
        raw_envelope = form.get("envelope", "{}")
        plain_body = form.get("plain", "") or ""
        html_body = form.get("html", "") or ""

        try:
            headers_data = json.loads(raw_headers) if isinstance(raw_headers, str) else {}
        except (json.JSONDecodeError, TypeError):
            headers_data = {}

        try:
            envelope_data = json.loads(raw_envelope) if isinstance(raw_envelope, str) else {}
        except (json.JSONDecodeError, TypeError):
            envelope_data = {}
    else:
        # Try JSON body as fallback
        try:
            body = await request.json()
            headers_data = body.get("headers", {})
            envelope_data = body.get("envelope", {})
            plain_body = body.get("plain", "")
            html_body = body.get("html", "")
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unable to parse request body",
            )

    await process_inbound_email(
        headers=headers_data,
        envelope=envelope_data,
        plain=plain_body,
        html=html_body,
        db=db,
    )

    return {"message": "ok"}
