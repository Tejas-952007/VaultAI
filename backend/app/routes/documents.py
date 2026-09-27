from pathlib import Path
from uuid import uuid4
from typing import List
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status, Depends
from backend.app.auth.authorization import require_permission
from backend.app.db.models import Employee
from backend.app.rag.ingestion import ingest_pdf, IngestionError
from backend.app.config import settings
from backend.app.services.document_store import document_store
from backend.app.schemas import ErrorResponse, ErrorDetail
from backend.app.rate_limit import upload_limiter
from backend.app.security import resolve_safe_upload_path

router = APIRouter()


@router.post("/vision/upload")
async def upload_vision_image(
    file: UploadFile = File(...),
    employee: Employee = Depends(require_permission("VISION_ANALYSIS")),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No image filename supplied.")
    suffix = Path(file.filename).suffix.lower()
    if suffix not in {".png", ".jpg", ".jpeg", ".webp"}:
        raise HTTPException(status_code=400, detail="Supported image formats: PNG, JPG, JPEG, WEBP.")
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded image is empty.")
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Image exceeds the 10MB limit.")

    image_root = settings.BASE_DATA_DIR / "images"
    image_path = resolve_safe_upload_path(f"{uuid4()}{suffix}", root=image_root)
    image_path.write_bytes(content)
    return {"image_path": str(image_path), "filename": Path(file.filename).name, "size_bytes": len(content)}


@router.post("/documents", status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    okf_concept_id: str | None = Form(default=None),
    employee: Employee = Depends(require_permission("DOCUMENT_UPLOAD")),
):
    client_ip = "unknown"
    if not upload_limiter.allow(client_ip):
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail={"status": "error", "error": {"code": "RATE_LIMITED", "message": "Too many document uploads. Try again shortly."}})

    try:
        if not file.filename:
            raise IngestionError("No filename supplied.")
        if not file.filename.lower().endswith(".pdf"):
            raise IngestionError("Only PDF files are supported.")

        if file.size is not None and file.size > settings.UPLOAD_MAX_BYTES:
            raise IngestionError(f"PDF file exceeds maximum allowed size ({settings.UPLOAD_MAX_BYTES} bytes).")

        content = await file.read()
        if len(content) == 0:
            raise IngestionError("Uploaded PDF file is empty.")
        if len(content) > settings.UPLOAD_MAX_BYTES:
            raise IngestionError(f"PDF file exceeds maximum allowed size ({settings.UPLOAD_MAX_BYTES} bytes).")

        safe_path = resolve_safe_upload_path(file.filename)
        if safe_path.suffix.lower() != ".pdf":
            raise IngestionError("Only PDF files are supported.")

        doc = ingest_pdf(
            file_bytes=content,
            original_filename=file.filename or "upload.pdf",
            okf_concept_id=okf_concept_id,
        )
        return doc
    except IngestionError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponse(
                status="error",
                error=ErrorDetail(code="INGESTION_ERROR", message=str(e))
            ).model_dump()
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                status="error",
                error=ErrorDetail(code="UPLOAD_FAILED", message=str(e))
            ).model_dump()
        )


@router.get("/documents")
def list_documents(employee: Employee = Depends(require_permission("DOCUMENT_VIEW"))):
    return document_store.list_documents()


@router.get("/documents/{doc_id}")
def get_document(doc_id: str, employee: Employee = Depends(require_permission("DOCUMENT_VIEW"))):
    doc = document_store.get_document(doc_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorResponse(
                status="error",
                error=ErrorDetail(code="DOCUMENT_NOT_FOUND", message=f"Document {doc_id} not found.")
            ).model_dump()
        )
    return doc
