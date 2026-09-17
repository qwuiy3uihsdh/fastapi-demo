from sqlalchemy import select

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.permission import Permission
from app.models.role import Role
from app.models.user import User

PERMISSIONS = [
    ("user:info", "查看当前用户", "user", "read"),
    ("user:list", "查看用户列表", "user", "list"),
    ("user:update", "修改用户", "user", "update"),
    ("user:delete", "删除用户", "user", "delete"),
    ("role:list", "查看角色", "role", "list"),
]

ROLES = {
    "admin": ("管理员", ["user:info", "user:list", "user:update", "user:delete", "role:list"]),
    "user": ("普通用户", ["user:info"]),
}

ADMIN_USERNAME = "admin"
ADMIN_EMAIL = "admin@example.com"
ADMIN_PASSWORD = "Admin@12345"

def seed() -> None:
    db = SessionLocal()
    try:
        perm_map: dict[str, Permission] = {}
        for code, name, resource, action in PERMISSIONS:
            perm = db.execute(
                select(Permission).where(Permission.code == code)
            ).scalar_one_or_none()
            if perm is None:
                perm = Permission(code=code, name=name, resource=resource, action=action)
                db.add(perm)
            perm_map[code] = perm
        db.flush()

        role_map: dict[str, Role] = {}
        for code, (name, codes) in ROLES.items():
            role = db.execute(
                select(Role).where(Role.code == code)
            ).scalar_one_or_none()
            if role is None:
                role = Role(code=code, name=name, is_system=True)
                db.add(role)
            role.permissions = [perm_map[c] for c in codes]
            role_map[code] = role
        db.flush()

        admin = db.execute(
            select(User).where(User.username == ADMIN_USERNAME)
        ).scalar_one_or_none()
        if admin is None:
            admin = User(
                username=ADMIN_USERNAME,
                email=ADMIN_EMAIL,
                hashed_password=hash_password(ADMIN_PASSWORD),
                nickname="超级管理员",
                is_superuser=True,
                is_active=True,
            )
            db.add(admin)
            db.flush()
        admin.roles = [role_map["admin"]]

        db.commit()
        print(f"seed ok: admin={ADMIN_USERNAME} / {ADMIN_PASSWORD}")
    finally:
        db.close()

if __name__ == "__main__":
    seed()