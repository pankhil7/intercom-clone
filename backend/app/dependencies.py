from typing import Optional
from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.organization import Organization
from app.services.auth_service import decode_access_token, decode_widget_token

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    payload = decode_access_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    user = db.query(User).filter(User.id == payload["sub"], User.is_active == True).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    return user


def get_current_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return current_user


def get_current_org(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Organization:
    org = db.query(Organization).filter(Organization.id == current_user.organization_id).first()
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")
    return org


def get_widget_session(
    x_widget_session: Optional[str] = Header(None),
    db: Session = Depends(get_db),
) -> dict:
    if not x_widget_session:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Widget session required")

    payload = decode_widget_token(x_widget_session)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired widget session")

    return payload
