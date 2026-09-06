from fastapi import APIRouter
from backend.app.routes.health import router as health_router
from backend.app.routes.chat import router as chat_router
from backend.app.routes.documents import router as documents_router
from backend.app.routes.auth import router as auth_router
from backend.app.routes.admin import router as admin_router
from backend.app.routes.security import router as security_router
from backend.app.routes.telemetry import router as telemetry_router


api_router = APIRouter()

api_router.include_router(health_router, tags=["Health"])
api_router.include_router(chat_router, tags=["Chat"])
api_router.include_router(documents_router, tags=["Documents"])
api_router.include_router(auth_router, tags=["Authentication"])
api_router.include_router(admin_router, tags=["Administration"])
api_router.include_router(security_router, tags=["Security"])
api_router.include_router(telemetry_router, tags=["Telemetry"])
api_router.include_router(__import__("backend.app.routes.sandbox", fromlist=["router"]).router, tags=["Sandbox"])
api_router.include_router(__import__("backend.app.routes.audit", fromlist=["router"]).router, tags=["Audit"])
