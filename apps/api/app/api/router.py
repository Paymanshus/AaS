from fastapi import APIRouter

from app.api.routes.arguments import router as arguments_router
from app.api.routes.health import router as health_router
from app.api.routes.streaming import router as streaming_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(arguments_router)
api_router.include_router(streaming_router)
