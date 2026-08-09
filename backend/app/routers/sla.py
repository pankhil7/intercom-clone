from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_admin, get_current_user
from app.models.sla_policy import SLAPolicy
from app.models.user import User

from app.logging_config import get_logger

router = APIRouter(prefix="/sla", tags=["sla"])
logger = get_logger(__name__)


class SLAPolicyCreate(BaseModel):
    name: str
    first_response_hours: int = 8
    resolution_hours: int = 48
    business_hours_only: bool = False


class SLAPolicyUpdate(BaseModel):
    name: Optional[str] = None
    first_response_hours: Optional[int] = None
    resolution_hours: Optional[int] = None
    business_hours_only: Optional[bool] = None


class SLAPolicyResponse(BaseModel):
    id: UUID
    organization_id: UUID
    name: str
    first_response_hours: int
    resolution_hours: int
    business_hours_only: bool

    model_config = {"from_attributes": True}


@router.get("/policies", response_model=List[SLAPolicyResponse])
def list_sla_policies(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    policies = (
        db.query(SLAPolicy)
        .filter(SLAPolicy.organization_id == current_user.organization_id)
        .order_by(SLAPolicy.created_at)
        .all()
    )
    return policies


@router.post("/policies", response_model=SLAPolicyResponse, status_code=status.HTTP_201_CREATED)
def create_sla_policy(
    payload: SLAPolicyCreate,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    policy = SLAPolicy(
        organization_id=current_user.organization_id,
        name=payload.name,
        first_response_hours=payload.first_response_hours,
        resolution_hours=payload.resolution_hours,
        business_hours_only=payload.business_hours_only,
    )
    db.add(policy)
    db.commit()
    db.refresh(policy)
    return policy


@router.patch("/policies/{policy_id}", response_model=SLAPolicyResponse)
def update_sla_policy(
    policy_id: UUID,
    payload: SLAPolicyUpdate,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    policy = db.query(SLAPolicy).filter(
        SLAPolicy.id == policy_id,
        SLAPolicy.organization_id == current_user.organization_id,
    ).first()
    if not policy:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SLA policy not found")

    if payload.name is not None:
        policy.name = payload.name
    if payload.first_response_hours is not None:
        policy.first_response_hours = payload.first_response_hours
    if payload.resolution_hours is not None:
        policy.resolution_hours = payload.resolution_hours
    if payload.business_hours_only is not None:
        policy.business_hours_only = payload.business_hours_only

    db.commit()
    db.refresh(policy)
    return policy


@router.delete("/policies/{policy_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_sla_policy(
    policy_id: UUID,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    policy = db.query(SLAPolicy).filter(
        SLAPolicy.id == policy_id,
        SLAPolicy.organization_id == current_user.organization_id,
    ).first()
    if not policy:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SLA policy not found")

    db.delete(policy)
    db.commit()
