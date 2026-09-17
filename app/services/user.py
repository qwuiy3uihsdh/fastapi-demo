from datetime import datetime, timezone

from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import BizError, ErrorCode
from app.core.security import (
    create_access_token,
    dummy_verify,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.schemas.user import (
    LoginIn,
    RegisterIn,
    RoleOut,
    TokenOut,
    UserBrief,
    UserInfoOut,
)

def to_user_info(user: User) -> UserInfoOut:
    return UserInfoOut(
        id=user.id,
        username=user.username,
        email=user.email,
        nickname=user.nickname, 
        avatar=user.avatar,
        is_active=user.is_active,
        is_superuser=user.is_superuser,
        roles=[RoleOut.model_validate(r) for r in user.roles],
        permissions=sorted(user.permission_codes - {"*"}),
        created_at=user.created_at,
        last_login_at=user.last_login_at,
    )

def register_user(db: Session, data: RegisterIn) -> UserBrief:
    dup = db.execute(
        select(User).where(
            or_(User.username == data.username, User.email == data.email)
        )
    ).scalar_one_or_none()
    if dup is not None:
        which = "用户名" if dup.username == data.username else "邮箱"
        raise BizError(ErrorCode.CONFLICT, f"{which}已被注册", 409)

    user = User(
        username=data.username,
        email=data.email,
        hashed_password=hash_password(data.password),
        nickname=data.nickname,
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise BizError(ErrorCode.CONFLICT, "用户名或邮箱已被注册", 409)

    db.refresh(user)
    return UserBrief.model_validate(user, from_attributes=True)

def authenticate(db: Session, username: str, password: str) -> User:
    user = db.execute(
        select(User).where(User.username == username)
    ).scalar_one_or_none()

    if user is None:
        dummy_verify(password)
        raise BizError(ErrorCode.LOGIN_FAILED, "用户名或密码错误", 401)

    if not verify_password(password, user.hashed_password):
        raise BizError(ErrorCode.LOGIN_FAILED, "用户名或密码错误", 401)

    if not user.is_active:
        raise BizError(ErrorCode.FORBIDDEN, "账号已被禁用", 403)

    return user

def login(db: Session, data: LoginIn) -> TokenOut:
    user = authenticate(db, data.username, data.password)

    user.last_login_at = datetime.now(timezone.utc)
    db.commit()

    settings = get_settings()
    token = create_access_token(
        user_id=user.id,
        username=user.username,
        roles=[r.code for r in user.roles],
    )
    return TokenOut(
        access_token=token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserBrief.model_validate(user, from_attributes=True),
    )