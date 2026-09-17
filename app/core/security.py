from datetime import datetime, timedelta, timezone
import secrets

import jwt
from pwdlib import PasswordHash

from app.core.config import get_settings
from app.core.exceptions import BizError, ErrorCode


pwd = PasswordHash.recommended()

_DUMMY_HASH: str = pwd.hash("dummy-timing-guard")

def hash_password(plain: str) -> str:
    return pwd.hash(plain)

def verify_password(plain: str, hashed: str) -> bool:
    try:
        return pwd.verify(plain, hashed)
    except Exception:
        return False

def dummy_verify(plain: str) -> None:
    pwd.verify(plain, _DUMMY_HASH)

def create_access_token(
    user_id: int | str,
    username: str,
    roles: list[str],
    expire_minutes: int | None = None
) -> str:
    settings = get_settings()
    exp_min = expire_minutes or settings.ACCESS_TOKEN_EXPIRE_MINUTES
    now = datetime.now(timezone.utc)

    payload = {
        "sub": str(user_id),
        "username": username,
        "roles": roles,
        "type": "access",
        "iat": now,
        "exp": now + timedelta(minutes=exp_min),
        "jti": secrets.token_urlsafe(16),
    }

    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise BizError(ErrorCode.UNAUTHORIZED, "登录已过期，请重新登录", 401)
    except jwt.InvalidTokenError:
        raise BizError(ErrorCode.UNAUTHORIZED, "令牌无效或已被篡改", 401)
