from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.response import ApiResponse
from app.db.session import get_db
from app.deps.auth import require_permissions
from app.models.user import User
from app.schemas.user import LoginIn, RegisterIn, TokenOut, UserBrief, UserInfoOut
from app.services.user import login as login_service
from app.services.user import register_user, to_user_info

router = APIRouter(prefix="/user", tags=["user"])

@router.post(
    "/register",
    response_model=ApiResponse[UserBrief],
    status_code=status.HTTP_201_CREATED,
    summary="用户注册",
)
def register(payload: RegisterIn, db: Session = Depends(get_db)) -> dict:
    return ApiResponse.ok(data=register_user(db, payload), message="注册成功")

@router.post(
    "/login",
    response_model=ApiResponse[TokenOut],
    summary="用户登录",
)
def login(payload: LoginIn, db: Session = Depends(get_db)) -> dict:
    return ApiResponse.ok(data=login_service(db, payload), message="登录成功")

@router.get(
    "/info",
    response_model=ApiResponse[UserInfoOut],
    summary="获取当前用户信息",
)
def info(user: User = Depends(require_permissions("user:info"))) -> dict:
    return ApiResponse.ok(data=to_user_info(user))