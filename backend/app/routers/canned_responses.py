from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.canned_response import CannedResponse
from app.models.user import User

router = APIRouter(prefix="/canned-responses", tags=["canned-responses"])


class CannedResponseCreate(BaseModel):
    name: str
    shortcut: Optional[str] = None
    content: str
    tags: List[str] = []


class CannedResponseUpdate(BaseModel):
    name: Optional[str] = None
    shortcut: Optional[str] = None
    content: Optional[str] = None
    tags: Optional[List[str]] = None


class CannedResponseSchema(BaseModel):
    id: UUID
    organization_id: UUID
    created_by: Optional[UUID] = None
    name: str
    shortcut: Optional[str] = None
    content: str
    tags: List[str] = []

    model_config = {"from_attributes": True}


@router.get("", response_model=List[CannedResponseSchema])
def list_canned_responses(
    search: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(CannedResponse).filter(
        CannedResponse.organization_id == current_user.organization_id
    )

    if search:
        pattern = f"%{search}%"
        q = q.filter(
            or_(
                CannedResponse.name.ilike(pattern),
                CannedResponse.shortcut.ilike(pattern),
                CannedResponse.content.ilike(pattern),
            )
        )

    return q.order_by(CannedResponse.name).all()


@router.post("", response_model=CannedResponseSchema, status_code=status.HTTP_201_CREATED)
def create_canned_response(
    payload: CannedResponseCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    cr = CannedResponse(
        organization_id=current_user.organization_id,
        created_by=current_user.id,
        name=payload.name,
        shortcut=payload.shortcut,
        content=payload.content,
        tags=payload.tags,
    )
    db.add(cr)
    db.commit()
    db.refresh(cr)
    return cr


@router.patch("/{canned_response_id}", response_model=CannedResponseSchema)
def update_canned_response(
    canned_response_id: UUID,
    payload: CannedResponseUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    cr = db.query(CannedResponse).filter(
        CannedResponse.id == canned_response_id,
        CannedResponse.organization_id == current_user.organization_id,
    ).first()
    if not cr:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Canned response not found")

    if payload.name is not None:
        cr.name = payload.name
    if payload.shortcut is not None:
        cr.shortcut = payload.shortcut
    if payload.content is not None:
        cr.content = payload.content
    if payload.tags is not None:
        cr.tags = payload.tags

    db.commit()
    db.refresh(cr)
    return cr


@router.delete("/{canned_response_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_canned_response(
    canned_response_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    cr = db.query(CannedResponse).filter(
        CannedResponse.id == canned_response_id,
        CannedResponse.organization_id == current_user.organization_id,
    ).first()
    if not cr:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Canned response not found")

    db.delete(cr)
    db.commit()
