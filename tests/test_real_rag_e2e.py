import pytest
import asyncio
from pathlib import Path
from pypdf import PdfWriter
from backend.app.rag.ingestion import ingest_pdf
from backend.app.services.document_store import document_store
from backend.app.services.chat_service import chat_service
from backend.app.schemas import ChatRequest
from backend.app.config import settings


def create_sample_engineering_pdf(output_path: Path) -> Path:
    """Create a minimal real PDF with known confidential engineering facts."""
    writer = PdfWriter()
    page = writer.add_blank_page(width=612, height=792)
    
    # Simple PDF containing engineering specifications
    # pypdf PdfWriter add_blank_page + annotation / text stream
    # To keep it standard and extractable by pypdf, we write standard PDF objects:
    from pypdf.generic import NameObject, create_string_object
    
    # We can write a simple valid PDF with text stream content
    pdf_content = (
        "%PDF-1.4\n"
        "1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n"
        "2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n"
        "3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >> endobj\n"
        "4 0 obj << /Length 210 >>\n"
        "stream\n"
        "BT\n"
        "/F1 12 Tf\n"
        "50 700 Td\n"
        "(VaultAI Confidential Engineering Report - MRPL Refinery Unit 4) Tj\n"
        "0 -20 Td\n"
        "(Safety operating pressure limit for Reactor 4B is exactly 320 PSI.) Tj\n"
        "0 -20 Td\n"
        "(Emergency shutoff valve trigger temperature is set to 240 degrees Celsius.) Tj\n"
        "ET\n"
        "endstream\n"
        "endobj\n"
        "5 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj\n"
        "xref\n"
        "0 6\n"
        "0000000000 65535 f\n"
        "0000000010 00000 n\n"
        "0000000060 00000 n\n"
        "0000000118 00000 n\n"
        "0000000262 00000 n\n"
        "0000000523 00000 n\n"
        "trailer << /Size 6 /Root 1 0 R >>\n"
        "startxref\n"
        "595\n"
        "%%EOF"
    )
    output_path.write_bytes(pdf_content.encode("latin1"))
    return output_path


@pytest.mark.asyncio
@pytest.mark.e2e
async def test_real_rag_e2e_pipeline(tmp_path):
    """Real end-to-end local test using real pypdf, real embeddings, real Chroma, and real Ollama Qwen3.5."""
    pdf_file = tmp_path / "engineering_report.pdf"
    create_sample_engineering_pdf(pdf_file)
    
    file_bytes = pdf_file.read_bytes()
    
    # 1. Real PDF ingestion
    doc_record = ingest_pdf(file_bytes=file_bytes, original_filename="engineering_report.pdf")
    assert doc_record["status"] == "ready"
    assert doc_record["chunks_count"] > 0
    doc_id = doc_record["id"]

    # 2. Query supported factual question
    req_supported = ChatRequest(
        message="What is the safety operating pressure limit for Reactor 4B?",
        document_ids=[doc_id]
    )
    res_supported = await chat_service.handle_chat(req_supported)
    
    assert res_supported.status == "success"
    assert res_supported.model == settings.OLLAMA_MODEL
    assert "320" in res_supported.answer or "320 PSI" in res_supported.answer
    assert len(res_supported.evidence) > 0
    assert res_supported.evidence[0].document_id == doc_id
    assert res_supported.duration_ms > 0

    # 3. Query unsupported question (Abstention check)
    req_unsupported = ChatRequest(
        message="What is the annual marketing budget for the corporate office?",
        document_ids=[doc_id]
    )
    res_unsupported = await chat_service.handle_chat(req_unsupported)
    
    assert res_unsupported.status == "insufficient"
    assert "not have enough information" in res_unsupported.answer.lower()
