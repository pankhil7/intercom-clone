import secrets
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_admin, get_current_user
from app.models.custom_domain import CustomDomain
from app.models.user import User

router = APIRouter(prefix="/domains", tags=["domains"])


class DomainCreate(BaseModel):
    domain: str


class DomainResponse(BaseModel):
    id: UUID
    organization_id: UUID
    domain: str
    verification_token: str
    dns_record_type: str
    is_verified: bool
    verified_at: Optional[datetime] = None
    last_checked_at: Optional[datetime] = None
    ssl_status: str
    created_at: datetime

    model_config = {"from_attributes": True}


@router.get("", response_model=List[DomainResponse])
def list_domains(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    domains = (
        db.query(CustomDomain)
        .filter(CustomDomain.organization_id == current_user.organization_id)
        .order_by(CustomDomain.created_at.desc())
        .all()
    )
    return domains


@router.post("", response_model=DomainResponse, status_code=status.HTTP_201_CREATED)
def add_domain(
    payload: DomainCreate,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    existing = db.query(CustomDomain).filter(CustomDomain.domain == payload.domain.lower()).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Domain already registered",
        )

    verification_token = "ic-verify-" + secrets.token_urlsafe(32)

    domain = CustomDomain(
        organization_id=current_user.organization_id,
        domain=payload.domain.lower(),
        verification_token=verification_token,
    )
    db.add(domain)
    db.commit()
    db.refresh(domain)
    return domain


@router.post("/{domain_id}/verify", response_model=DomainResponse)
def verify_domain(
    domain_id: UUID,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    domain = db.query(CustomDomain).filter(
        CustomDomain.id == domain_id,
        CustomDomain.organization_id == current_user.organization_id,
    ).first()
    if not domain:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Domain not found")

    domain.last_checked_at = datetime.utcnow()

    try:
        import dns.resolver

        answers = dns.resolver.resolve(domain.domain, "TXT")
        txt_records = [str(rdata).strip('"') for rdata in answers]

        if domain.verification_token in txt_records:
            domain.is_verified = True
            domain.verified_at = datetime.utcnow()
            domain.ssl_status = "provisioning"
        else:
            domain.is_verified = False
    except Exception:
        domain.is_verified = False

    db.commit()
    db.refresh(domain)
    return domain


@router.delete("/{domain_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_domain(
    domain_id: UUID,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    domain = db.query(CustomDomain).filter(
        CustomDomain.id == domain_id,
        CustomDomain.organization_id == current_user.organization_id,
    ).first()
    if not domain:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Domain not found")

    db.delete(domain)
    db.commit()
