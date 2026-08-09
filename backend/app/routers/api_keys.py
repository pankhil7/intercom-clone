import hashlib
import secrets
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_admin, get_current_user
from app.models.api_key import APIKey
from app.models.user import User

from app.logging_config import get_logger

router = APIRouter(prefix="/api-keys", tags=["api-keys"])
logger = get_logger(__name__)


class APIKeyResponse(BaseModel):
    id: UUID
    name: str
    key_prefix: str
    scopes: List[str]
    is_active: bool
    created_at: str

    model_config = {"from_attributes": False}


class APIKeyCreateRequest(BaseModel):
    name: str
    scopes: List[str] = []


class APIKeyCreateResponse(BaseModel):
    id: UUID
    name: str
    key: str  # Full key returned only once
    key_prefix: str
    scopes: List[str]
    is_active: bool


@router.get("", response_model=List[APIKeyResponse])
def list_api_keys(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    keys = (
        db.query(APIKey)
        .filter(
            APIKey.organization_id == current_user.organization_id,
            APIKey.is_active == True,
        )
        .order_by(APIKey.created_at.desc())
        .all()
    )
    return [
        APIKeyResponse(
            id=k.id,
            name=k.name,
            key_prefix=k.key_prefix,
            scopes=k.scopes or [],
            is_active=k.is_active,
            created_at=k.created_at.isoformat(),
        )
        for k in keys
    ]


@router.post("", response_model=APIKeyCreateResponse, status_code=status.HTTP_201_CREATED)
def create_api_key(
    payload: APIKeyCreateRequest,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    raw_key = "ic_live_" + secrets.token_urlsafe(32)
    key_prefix = raw_key[:16]  # first 16 chars as prefix for display
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()

    api_key = APIKey(
        organization_id=current_user.organization_id,
        created_by=current_user.id,
        name=payload.name,
        key_hash=key_hash,
        key_prefix=key_prefix,
        scopes=payload.scopes,
    )
    db.add(api_key)
    db.commit()
    db.refresh(api_key)

    logger.info("api_key_created", key_id=str(api_key.id), name=api_key.name, scopes=payload.scopes, org_id=str(current_user.organization_id))
    return APIKeyCreateResponse(
        id=api_key.id,
        name=api_key.name,
        key=raw_key,
        key_prefix=api_key.key_prefix,
        scopes=api_key.scopes or [],
        is_active=api_key.is_active,
    )


@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
def deactivate_api_key(
    key_id: UUID,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    api_key = db.query(APIKey).filter(
        APIKey.id == key_id,
        APIKey.organization_id == current_user.organization_id,
    ).first()
    if not api_key:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found")

    api_key.is_active = False
    db.commit()
    logger.info("api_key_revoked", key_id=str(key_id), org_id=str(current_user.organization_id))
