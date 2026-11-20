import uuid
from datetime import datetime, timedelta, timezone
from enum import Enum

import bcrypt
import jwt
from cryptography.fernet import Fernet, InvalidToken

from app.core.config import Settings


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))


class TokenType(str, Enum):
    ACCESS = "access"
    REFRESH = "refresh"


def create_token(
    user_id: uuid.UUID,
    token_type: TokenType,
    settings: Settings,
) -> str:
    now = datetime.now(timezone.utc)
    if token_type is TokenType.ACCESS:
        expires_delta = timedelta(minutes=settings.access_token_expire_minutes)
    else:
        expires_delta = timedelta(days=settings.refresh_token_expire_days)

    payload = {
        "sub": str(user_id),
        "type": token_type.value,
        "iat": now,
        "exp": now + expires_delta,
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def decode_token(token: str, settings: Settings) -> dict:
    return jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])


def encrypt_secret(value: str, settings: Settings) -> str:
    fernet = Fernet(settings.encryption_key.encode("utf-8"))
    return fernet.encrypt(value.encode("utf-8")).decode("utf-8")


def decrypt_secret(value: str, settings: Settings) -> str | None:
    fernet = Fernet(settings.encryption_key.encode("utf-8"))
    try:
        return fernet.decrypt(value.encode("utf-8")).decode("utf-8")
    except InvalidToken:
        return None
