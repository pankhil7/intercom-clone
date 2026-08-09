import secrets
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from app.config import settings
from app.models.user import User
from app.models.organization import Organization

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(user_id: str, org_id: str, role: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(user_id),
        "org": str(org_id),
        "role": role,
        "type": "access",
        "exp": expire,
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(user_id: str) -> str:
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": str(user_id),
        "type": "refresh",
        "exp": expire,
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_widget_session_token(contact_id: str, org_id: str, visitor_id: str) -> str:
    expire = datetime.utcnow() + timedelta(hours=settings.WIDGET_SESSION_EXPIRE_HOURS)
    payload = {
        "contact_id": str(contact_id),
        "org_id": str(org_id),
        "visitor_id": visitor_id,
        "type": "widget",
        "exp": expire,
    }
    return jwt.encode(payload, settings.WIDGET_SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("type") != "access":
            return None
        return payload
    except JWTError:
        return None


def decode_refresh_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("type") != "refresh":
            return None
        return payload
    except JWTError:
        return None


def decode_widget_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, settings.WIDGET_SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("type") != "widget":
            return None
        return payload
    except JWTError:
        return None


def generate_invite_token() -> str:
    return secrets.token_urlsafe(32)


def generate_reset_token() -> str:
    return secrets.token_urlsafe(32)


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    user = db.query(User).filter(User.email == email.lower(), User.is_active == True).first()
    if not user or not verify_password(password, user.password_hash):
        return None
    return user


def slugify(text: str) -> str:
    import re
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text)
    return text


def generate_org_slug(name: str, db: Session) -> str:
    base_slug = slugify(name)
    slug = base_slug
    counter = 1
    while db.query(Organization).filter(Organization.slug == slug).first():
        slug = f"{base_slug}-{counter}"
        counter += 1
    return slug
