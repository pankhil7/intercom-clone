from datetime import datetime, timedelta
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_admin, get_current_user
from app.logging_config import get_logger
from app.models.invitation import Invitation

logger = get_logger(__name__)
from app.models.organization import Organization
from app.models.user import User
from app.schemas.auth import TokenResponse
from app.schemas.team import (
    AcceptInviteRequest,
    InvitationResponse,
    InviteRequest,
    MemberResponse,
    MemberUpdate,
    ValidateInviteResponse,
)
from app.services.auth_service import (
    create_access_token,
    create_refresh_token,
    generate_invite_token,
    hash_password,
)

router = APIRouter(prefix="/team", tags=["team"])


@router.get("/members", response_model=List[MemberResponse])
def list_members(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    members = (
        db.query(User)
        .filter(User.organization_id == current_user.organization_id)
        .order_by(User.created_at)
        .all()
    )
    return members


@router.patch("/members/{user_id}", response_model=MemberResponse)
def update_member(
    user_id: UUID,
    payload: MemberUpdate,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    member = (
        db.query(User)
        .filter(User.id == user_id, User.organization_id == current_user.organization_id)
        .first()
    )
    if not member:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")

    if payload.role is not None:
        member.role = payload.role
    if payload.is_active is not None:
        member.is_active = payload.is_active
    if payload.full_name is not None:
        member.full_name = payload.full_name
    if payload.avatar_url is not None:
        member.avatar_url = payload.avatar_url

    db.commit()
    db.refresh(member)
    return member


@router.delete("/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def deactivate_member(
    user_id: UUID,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    if str(user_id) == str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate yourself",
        )

    member = (
        db.query(User)
        .filter(User.id == user_id, User.organization_id == current_user.organization_id)
        .first()
    )
    if not member:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")

    member.is_active = False
    db.commit()
    logger.info("member_deactivated", user_id=str(user_id), deactivated_by=str(current_user.id))


@router.post("/invitations", response_model=InvitationResponse, status_code=status.HTTP_201_CREATED)
def create_invitation(
    payload: InviteRequest,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    # Check for existing pending invitation
    existing = (
        db.query(Invitation)
        .filter(
            Invitation.organization_id == current_user.organization_id,
            Invitation.email == payload.email.lower(),
            Invitation.accepted_at == None,
            Invitation.expires_at > datetime.utcnow(),
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A pending invitation already exists for this email",
        )

    token = generate_invite_token()
    invitation = Invitation(
        organization_id=current_user.organization_id,
        email=payload.email.lower(),
        role=payload.role,
        token=token,
        invited_by=current_user.id,
        expires_at=datetime.utcnow() + timedelta(days=7),
    )
    db.add(invitation)
    db.commit()
    db.refresh(invitation)
    logger.info("invitation_sent",
        invited_by=str(current_user.id),
        role=payload.role,
        org_id=str(current_user.organization_id),
    )
    return invitation


@router.get("/invitations", response_model=List[InvitationResponse])
def list_invitations(
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    invitations = (
        db.query(Invitation)
        .filter(
            Invitation.organization_id == current_user.organization_id,
            Invitation.accepted_at == None,
            Invitation.expires_at > datetime.utcnow(),
        )
        .order_by(Invitation.created_at.desc())
        .all()
    )
    return invitations


@router.delete("/invitations/{invitation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_invitation(
    invitation_id: UUID,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    invitation = (
        db.query(Invitation)
        .filter(
            Invitation.id == invitation_id,
            Invitation.organization_id == current_user.organization_id,
        )
        .first()
    )
    if not invitation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invitation not found")

    db.delete(invitation)
    db.commit()


@router.get("/invitations/validate/{token}", response_model=ValidateInviteResponse)
def validate_invite(token: str, db: Session = Depends(get_db)):
    invitation = (
        db.query(Invitation)
        .filter(
            Invitation.token == token,
            Invitation.accepted_at == None,
            Invitation.expires_at > datetime.utcnow(),
        )
        .first()
    )
    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation not found or expired",
        )

    org = db.query(Organization).filter(Organization.id == invitation.organization_id).first()
    return ValidateInviteResponse(
        email=invitation.email,
        role=invitation.role,
        organization_name=org.name if org else "",
    )


@router.post("/invitations/accept", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def accept_invite(payload: AcceptInviteRequest, db: Session = Depends(get_db)):
    invitation = (
        db.query(Invitation)
        .filter(
            Invitation.token == payload.token,
            Invitation.accepted_at == None,
            Invitation.expires_at > datetime.utcnow(),
        )
        .first()
    )
    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation not found or expired",
        )

    # Check email not already taken
    existing_user = db.query(User).filter(User.email == invitation.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    user = User(
        organization_id=invitation.organization_id,
        email=invitation.email,
        password_hash=hash_password(payload.password),
        full_name=payload.full_name,
        role=invitation.role,
        invited_by=invitation.invited_by,
    )
    db.add(user)

    invitation.accepted_at = datetime.utcnow()
    db.commit()
    db.refresh(user)

    access_token = create_access_token(str(user.id), str(user.organization_id), user.role)
    refresh_token = create_refresh_token(str(user.id))

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )
