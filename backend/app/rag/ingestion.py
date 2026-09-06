import hashlib
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Tuple
from pypdf import PdfReader
from backend.app.config import settings
from backend.app.services.document_store import document_store
from backend.app.rag.vector_store import vector_store
from backend.app.audit.audit import audit_logger


class IngestionError(Exception):
    pass


def validate_pdf(file_bytes: bytes, filename: str) -> None:
    if not filename.lower().endswith(".pdf"):
        raise IngestionError("Only PDF files are supported.")
    if len(file_bytes) == 0:
        raise IngestionError("Uploaded PDF file is empty.")
    if len(file_bytes) > 50 * 1024 * 1024:  # 50MB limit
        raise IngestionError("PDF file exceeds maximum allowed size (50MB).")


def compute_sha256(file_bytes: bytes) -> str:
    return hashlib.sha256(file_bytes).hexdigest()


def extract_text_from_pdf(file_path: Path) -> List[Dict[str, Any]]:
    pages_data = []
    try:
        reader = PdfReader(str(file_path))
        for page_idx, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            text = text.strip()
            if text:
                pages_data.append({
                    "page_number": page_idx + 1,
                    "text": text
                })
    except Exception as e:
        raise IngestionError(f"Failed to extract text from PDF using pypdf: {str(e)}")

    if not pages_data:
        raise IngestionError("PDF file contains no extractable text.")

    return pages_data


def chunk_pages(pages_data: List[Dict[str, Any]], chunk_size: int = 600, overlap: int = 100) -> List[Dict[str, Any]]:
    chunks = []
    chunk_counter = 0

    for page in pages_data:
        text = page["text"]
        page_num = page["page_number"]
        
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunk_str = text[start:end].strip()
            if chunk_str:
                chunk_counter += 1
                chunks.append({
                    "chunk_index": chunk_counter,
                    "page_number": page_num,
                    "text": chunk_str
                })
            start += (chunk_size - overlap)

    return chunks


def ingest_pdf(file_bytes: bytes, original_filename: str) -> Dict[str, Any]:
    validate_pdf(file_bytes, original_filename)
    sha256_hash = compute_sha256(file_bytes)

    # Check for existing duplicate document
    existing = document_store.get_document_by_sha256(sha256_hash)
    if existing and existing.get("status") == "ready":
        audit_logger.log(
            event_type="document_upload_duplicate",
            resource_id=existing["id"],
            details={"filename": original_filename, "sha256": sha256_hash}
        )
        return existing

    doc_id = str(uuid.uuid4())
    safe_filename = f"{doc_id}_{Path(original_filename).name}"
    storage_path = settings.DOC_STORE_PATH / safe_filename

    # Save file locally
    settings.DOC_STORE_PATH.mkdir(parents=True, exist_ok=True)
    with open(storage_path, "wb") as f:
        f.write(file_bytes)

    doc_metadata = {
        "id": doc_id,
        "filename": original_filename,
        "sha256": sha256_hash,
        "size_bytes": len(file_bytes),
        "storage_path": str(storage_path),
        "status": "processing",
        "error": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "chunks_count": 0
    }
    document_store.add_document(doc_metadata)

    audit_logger.log(
        event_type="document_upload",
        resource_id=doc_id,
        details={"filename": original_filename, "size_bytes": len(file_bytes), "sha256": sha256_hash}
    )

    try:
        # Extract & chunk
        pages = extract_text_from_pdf(storage_path)
        chunks = chunk_pages(pages)

        chunk_ids = []
        texts = []
        metadatas = []

        for c in chunks:
            cid = f"{doc_id}_c{c['chunk_index']}"
            chunk_ids.append(cid)
            texts.append(c["text"])
            metadatas.append({
                "document_id": doc_id,
                "source": original_filename,
                "chunk_id": cid,
                "chunk_index": c["chunk_index"],
                "page_number": c["page_number"]
            })

        # Persist vectors
        vector_store.add_chunks(chunk_ids, texts, metadatas)

        document_store.update_status(doc_id, status="ready", chunks_count=len(chunks))
        
        audit_logger.log(
            event_type="document_ingestion_complete",
            resource_id=doc_id,
            status="success",
            details={"chunks_count": len(chunks)}
        )

        return document_store.get_document(doc_id)

    except Exception as e:
        error_msg = str(e)
        document_store.update_status(doc_id, status="failed", error=error_msg)
        audit_logger.log(
            event_type="document_ingestion_failed",
            resource_id=doc_id,
            status="error",
            details={"error": error_msg}
        )
        raise IngestionError(f"Ingestion failed: {error_msg}")
