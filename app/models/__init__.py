# app/models/__init__.py
from app.db.base import Base

# 顺序不重要，但要全部 import，让类体执行、挂到 Base.metadata
from app.models.association import user_roles, role_permissions  # noqa: F401
from app.models.role import Role                                 # noqa: F401
from app.models.permission import Permission                     # noqa: F401
from app.models.user import User                                 # noqa: F401

__all__ = ["Base", "User", "Role", "Permission"]