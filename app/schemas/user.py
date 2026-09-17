from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

class RegisterIn(BaseModel):
    username: str = Field(min_length=3, max_length=32, pattern=r"^[A-Za-z0-9_]+$")
    email: EmailStr
    password: str = Field(min_length=8, max_length=64)
    nickname: str | None = Field(default=None, max_length=32)

class LoginIn(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=64)

class RoleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    code: str
    name: str

class UserBrief(BaseModel):
    id: int
    username: str
    email: EmailStr
    created_at: datetime



class UserInfoOut(BaseModel):
    id: int
    username: str
    email: EmailStr
    nickname: str | None = None
    avatar: str | None = None
    is_active: bool
    is_superuser: bool
    roles: list[RoleOut] = Field(default_factory=list)
    permissions: list[str] = Field(default_factory=list)
    created_at: datetime
    last_login_at: datetime | None = None

class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserBrief