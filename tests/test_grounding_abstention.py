from unittest.mock import patch
from backend.app.schemas import EvidenceItem
from backend.app.services.grounded_generation import GroundedGenerator, INSUFFICIENT_MESSAGE


def test_grounded_generator_empty_evidence():
    gen = GroundedGenerator()
    ans, model, duration, status = gen.generate("Question?", evidence=[])
    assert status == "insufficient"
    assert ans == INSUFFICIENT_MESSAGE


def test_grounded_generator_success():
    gen = GroundedGenerator()
    evidence = [
        EvidenceItem(
            document_id="doc1",
            source="sop.pdf",
            chunk_id="doc1_c1",
            score=0.85,
            snippet="Pressure limit is 150 PSI."
        )
    ]
    mock_ollama_res = {
        "text": "According to sop.pdf, the maximum pressure limit is 150 PSI.",
        "model": "qwen3.5:latest",
        "duration_ms": 210.0,
        "status": "success"
    }

    with patch("backend.app.services.grounded_generation.ollama_service.generate", return_value=mock_ollama_res):
        ans, model, duration, status = gen.generate("What is the pressure limit?", evidence=evidence)
        assert status == "success"
        assert "150 PSI" in ans
        assert model == "qwen3.5:latest"


def test_grounded_generator_explicit_abstention():
    gen = GroundedGenerator()
    evidence = [
        EvidenceItem(
            document_id="doc1",
            source="sop.pdf",
            chunk_id="doc1_c1",
            score=0.30,
            snippet="General overview of refinery."
        )
    ]
    mock_ollama_res = {
        "text": "I do not have enough information to answer this question based on the provided documents.",
        "model": "qwen3.5:latest",
        "duration_ms": 100.0,
        "status": "success"
    }

    with patch("backend.app.services.grounded_generation.ollama_service.generate", return_value=mock_ollama_res):
        ans, model, duration, status = gen.generate("What is the employee salary?", evidence=evidence)
        assert status == "insufficient"
        assert ans == INSUFFICIENT_MESSAGE
