from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session
from typing import Optional

from app.logging_config import get_logger
from app.config import settings

logger = get_logger(__name__)
from app.database import get_db
from app.dependencies import get_current_user
from app.models.organization import Organization
from app.models.user import User
from app.schemas.auth import (
    ForgotPasswordRequest,
    LoginRequest,
    MeResponse,
    OrganizationResponse,
    ResetPasswordRequest,
    SignupRequest,
    UserResponse,
)
from app.services.auth_service import (
    authenticate_user,
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    generate_org_slug,
    hash_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])

REFRESH_COOKIE_NAME = "refresh_token"
COOKIE_MAX_AGE = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60  # seconds


def _set_refresh_cookie(response: Response, refresh_token: str) -> None:
    """Write the refresh token as an HttpOnly, Secure, SameSite=lax cookie."""
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=refresh_token,
        httponly=True,                        # JS cannot read it
        secure=not settings.DEBUG,            # HTTPS only in production
        samesite="lax",                       # sent on top-level navigations, blocks CSRF
        max_age=COOKIE_MAX_AGE,
        path="/api/v1/auth",                  # scoped — only sent to auth endpoints
    )


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(
        key=REFRESH_COOKIE_NAME,
        path="/api/v1/auth",
        httponly=True,
        secure=not settings.DEBUG,
        samesite="lax",
    )


@router.post("/signup", status_code=status.HTTP_201_CREATED)
def signup(payload: SignupRequest, response: Response, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email.lower()).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    slug = generate_org_slug(payload.organization_name, db)
    org = Organization(name=payload.organization_name, slug=slug)
    db.add(org)
    db.flush()

    user = User(
        organization_id=org.id,
        email=payload.email.lower(),
        password_hash=hash_password(payload.password),
        full_name=payload.full_name,
        role="admin",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    db.refresh(org)

    access_token = create_access_token(str(user.id), str(org.id), user.role)
    refresh_token = create_refresh_token(str(user.id))

    _set_refresh_cookie(response, refresh_token)

    logger.info("user_signed_up", user_id=str(user.id), org_id=str(org.id), role=user.role)
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": UserResponse.model_validate(user).model_dump(),
        "organization": OrganizationResponse.model_validate(org).model_dump(),
    }


@router.post("/login")
def login(payload: LoginRequest, response: Response, db: Session = Depends(get_db)):
    user = authenticate_user(db, payload.email, payload.password)
    if not user:
        logger.warning("login_failed", email_domain=payload.email.split("@")[-1])  # domain only, not full email
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    org = db.query(Organization).filter(Organization.id == user.organization_id).first()

    access_token = create_access_token(str(user.id), str(user.organization_id), user.role)
    refresh_token = create_refresh_token(str(user.id))

    _set_refresh_cookie(response, refresh_token)

    logger.info("user_logged_in", user_id=str(user.id), org_id=str(user.organization_id), role=user.role)
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": UserResponse.model_validate(user).model_dump(),
        "organization": OrganizationResponse.model_validate(org).model_dump(),
    }


@router.post("/refresh")
def refresh(
    response: Response,
    db: Session = Depends(get_db),
    refresh_token: Optional[str] = Cookie(default=None, alias=REFRESH_COOKIE_NAME),
):
    """
    Client never touches the refresh token — it arrives automatically via
    the HttpOnly cookie. Returns a new access token in the body and
    rotates the refresh cookie.
    """
    if not refresh_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No refresh token")

    token_data = decode_refresh_token(refresh_token)
    if not token_data:
        _clear_refresh_cookie(response)
        logger.warning("token_refresh_failed", reason="invalid_or_expired")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token")

    user = db.query(User).filter(User.id == token_data["sub"], User.is_active == True).first()
    if not user:
        _clear_refresh_cookie(response)
        logger.warning("token_refresh_failed", reason="user_not_found")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    org = db.query(Organization).filter(Organization.id == user.organization_id).first()

    new_access_token = create_access_token(str(user.id), str(user.organization_id), user.role)
    new_refresh_token = create_refresh_token(str(user.id))   # rotate — old token is discarded

    _set_refresh_cookie(response, new_refresh_token)

    logger.info("token_refreshed", user_id=str(user.id), org_id=str(user.organization_id))
    return {
        "access_token": new_access_token,
        "token_type": "bearer",
        "user": UserResponse.model_validate(user).model_dump(),
        "organization": OrganizationResponse.model_validate(org).model_dump(),
    }


@router.post("/logout")
def logout(response: Response, current_user: User = Depends(get_current_user)):
    _clear_refresh_cookie(response)
    logger.info("user_logged_out", user_id=str(current_user.id))
    return {"message": "ok"}


@router.get("/me", response_model=MeResponse)
def me(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    org = db.query(Organization).filter(Organization.id == current_user.organization_id).first()
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")
    return MeResponse(
        user=UserResponse.model_validate(current_user),
        organization=OrganizationResponse.model_validate(org),
    )


@router.post("/forgot-password")
def forgot_password(payload: ForgotPasswordRequest):
    return {"message": "ok"}


@router.post("/reset-password")
def reset_password(payload: ResetPasswordRequest):
    return {"message": "ok"}
