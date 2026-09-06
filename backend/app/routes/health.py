from fastapi import APIRouter
from backend.app.schemas import HealthResponse
from backend.app.services.ollama_service import ollama_service
from backend.app.config import settings

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def get_health():
    ollama_info = ollama_service.check_health()
    status_str = "available" if ollama_info.get("available") else "unavailable"
    
    # Filter available models to exclude any cloud tags if listed
    raw_models = ollama_info.get("models", [])
    local_models = [m for m in raw_models if "-cloud" not in m.lower()]
    
    return HealthResponse(
        status="ok",
        version=settings.VERSION,
        ollama_status=status_str,
        ollama_model=settings.OLLAMA_MODEL,
        available_models=local_models
    )
