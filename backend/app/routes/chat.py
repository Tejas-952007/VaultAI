from fastapi import APIRouter, Depends, HTTPException, status
from backend.app.auth.authorization import require_chat_permission
from backend.app.db.models import Employee
from backend.app.schemas import ChatRequest, ChatResponse, ErrorResponse, ErrorDetail
from backend.app.services.chat_service import chat_service
from backend.app.services.ollama_service import OllamaServiceError
from backend.app.rate_limit import router_limiter

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def post_chat(request: ChatRequest, employee: Employee = Depends(require_chat_permission)):
    client_ip = "chat:unknown"
    if not router_limiter.allow(client_ip):
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail={"status": "error", "error": {"code": "RATE_LIMITED", "message": "Too many chat requests. Please wait a moment and try again."}})

    try:
        return await chat_service.handle_chat(
            request,
            employee_position=employee.position.name if employee.position else None,
        )
    except OllamaServiceError as e:
        status_code = status.HTTP_503_SERVICE_UNAVAILABLE if e.code in ["MODEL_UNAVAILABLE", "MODEL_TIMEOUT"] else status.HTTP_500_INTERNAL_SERVER_ERROR
        raise HTTPException(
            status_code=status_code,
            detail=ErrorResponse(
                status="error",
                error=ErrorDetail(
                    code=e.code,
                    message=e.message,
                    details=e.details
                )
            ).model_dump()
        )
