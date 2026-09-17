from fastapi import APIRouter

from app.routers.user import router as user_router

api_router = APIRouter()
api_router.include_router(user_router)

__all__ = ["api_router"]