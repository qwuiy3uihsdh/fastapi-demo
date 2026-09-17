from typing import Callable

from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.core.security import decode_access_token
from app.core.exceptions import BizError, ErrorCode

bearer_scheme = HTTPBearer(auto_error=False)

def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db)
) -> User:
    if not creds:
        raise BizError(ErrorCode.UNAUTHORIZED, "未提供Authorization头", 401)

    payload = decode_access_token(creds.credentials)
    sub = payload.get("sub")
    if not sub or not str(sub).isdigit():
        raise BizError(ErrorCode.UNAUTHORIZED, "令牌载荷无效", 401)
    if payload.get("type") != "access":
        raise BizError(ErrorCode.UNAUTHORIZED, "令牌类型错误", 401)

    user = db.get(User, int(sub))
    if not user:
        raise BizError(ErrorCode.UNAUTHORIZED, "用户不存在或已注销", 401)
    if not user.is_active:
        raise BizError(ErrorCode.FORBIDDEN, "账号已被禁用", 403)

    return user


def require_roles(*required: str) -> Callable:
    """Depends(require_roles('admin', 'editor'))"""
    def dep(user: User = Depends(get_current_user)) -> User:
        if not user.is_superuser:
            have = {r.code for r in user.roles}
            if set(required) - have:
                raise BizError(
                    ErrorCode.FORBIDDEN,
                    f"需要角色: {'、'.join(sorted(required))}",
                    403,
                )
        return user
    return dep


def require_permissions(*required: str) -> Callable:
    """Depends(require_permissions('user:delete'))"""
    def dep(user: User = Depends(get_current_user)) -> User:
        if not user.is_superuser:
            have = user.permission_codes
            if "*" not in have and set(required) - have:
                raise BizError(
                    ErrorCode.FORBIDDEN,
                    f"需要权限: {'、'.join(sorted(required))}",
                    403,
                )
        return user
    return dep
