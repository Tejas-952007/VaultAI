from unittest.mock import patch, AsyncMock
import pytest
from backend.app.graph.nodes.coding_agent import coding_agent_node
from backend.app.graph.nodes.vision_agent import vision_agent_node


@pytest.mark.asyncio
async def test_coding_agent_success():
    """Test successful code generation and execution."""
    state = {"request_id": "req_code_success", "message": "print('hello')"}
    
    # Mock Ollama health check to return the required model
    with patch("backend.app.graph.nodes.coding_agent.ollama_service.check_health", return_value={"available": True, "models": ["qwen2.5-coder:7b"]}):
        # Mock Ollama generate to return valid code
        with patch("backend.app.graph.nodes.coding_agent.ollama_service.generate", return_value={"text": "print('hello')", "model": "qwen2.5-coder:7b", "duration_ms": 100.0, "status": "success"}):
            # Mock sandbox execution to return success
            with patch("backend.app.graph.nodes.coding_agent.execute_code", new_callable=AsyncMock) as mock_exec:
                mock_exec.return_value = AsyncMock(stdout="hello", stderr="", exit_code=0, duration=0.1, timed_out=False, error_message=None)
                # Since execute_code is called as 'await execute_code', we need to make sure the mock returns a result object
                # The actual execute_code returns a SandboxResult dataclass.
                from backend.app.services.sandbox_service import SandboxResult
                mock_exec.return_value = SandboxResult(stdout="hello", stderr="", exit_code=0, duration=0.1, timed_out=False)
                
                res = await coding_agent_node(state)
                
                assert res["status"] == "success"
                assert res["answer"] == "hello"
                assert res["model"] == "qwen2.5-coder:7b"
                assert res["coding_attempts"] == 1
                assert res["generated_code"] == "print('hello')"


@pytest.mark.asyncio
async def test_coding_agent_retry_success():
    """Test failure on first attempt, success on second attempt."""
    state = {"request_id": "req_code_retry", "message": "calculate 2+2"}
    
    with patch("backend.app.graph.nodes.coding_agent.ollama_service.check_health", return_value={"available": True, "models": ["qwen2.5-coder:7b"]}):
        # Mock Ollama generate to return broken code first, then fixed code
        with patch("backend.app.graph.nodes.coding_agent.ollama_service.generate") as mock_gen:
            mock_gen.side_effect = [
                {"text": "print(2+2", "model": "qwen2.5-coder:7b", "duration_ms": 100.0, "status": "success"}, # Missing paren
                {"text": "print(2+2)", "model": "qwen2.5-coder:7b", "duration_ms": 100.0, "status": "success"}, # Fixed
            ]
            
            with patch("backend.app.graph.nodes.coding_agent.execute_code", new_callable=AsyncMock) as mock_exec:
                from backend.app.services.sandbox_service import SandboxResult
                # First call fails, second succeeds
                mock_exec.side_effect = [
                    SandboxResult(stdout="", stderr="SyntaxError: unexpected EOF", exit_code=1, duration=0.1, timed_out=False),
                    SandboxResult(stdout="4", stderr="", exit_code=0, duration=0.1, timed_out=False),
                ]
                
                res = await coding_agent_node(state)
                
                assert res["status"] == "success"
                assert res["answer"] == "4"
                assert res["coding_attempts"] == 2
                assert mock_gen.call_count == 2
                assert mock_exec.call_count == 2


@pytest.mark.asyncio
async def test_coding_agent_max_retries():
    """Test that agent stops after MAX_CODING_ATTEMPTS."""
    state = {"request_id": "req_code_fail", "message": "do something"}
    
    with patch("backend.app.graph.nodes.coding_agent.ollama_service.check_health", return_value={"available": True, "models": ["qwen2.5-coder:7b"]}):
        with patch("backend.app.graph.nodes.coding_agent.ollama_service.generate", return_value={"text": "invalid code", "model": "qwen2.5-coder:7b", "duration_ms": 100.0, "status": "success"}):
            with patch("backend.app.graph.nodes.coding_agent.execute_code", new_callable=AsyncMock) as mock_exec:
                from backend.app.services.sandbox_service import SandboxResult
                mock_exec.return_value = SandboxResult(stdout="", stderr="Execution Error", exit_code=1, duration=0.1, timed_out=False)
                
                res = await coding_agent_node(state)
                
                assert res["status"] == "error"
                assert res["coding_attempts"] == 2
                assert mock_exec.call_count == 2
                assert "Execution Error" in res["answer"]


@pytest.mark.asyncio
async def test_coding_agent_model_unavailable():
    """Test behavior when qwen2.5-coder:7b is missing."""
    state = {"request_id": "req_code_none", "message": "write code"}
    
    with patch("backend.app.graph.nodes.coding_agent.ollama_service.check_health", return_value={"available": True, "models": ["qwen3.5:latest"]}):
        res = await coding_agent_node(state)
        assert res["status"] == "not_available"
        assert "qwen2.5-coder:7b not available" in res["answer"]


# ...existing code...
@pytest.mark.asyncio
async def test_vision_agent_success():
    """Test successful vision analysis."""
    state = {"request_id": "req_vis_success", "message": "What is in this image?", "image_path": "tests/test_image.png"}
    
    # Create a dummy image file
    with open("tests/test_image.png", "wb") as f:
        f.write(b"fake image data")

    with patch("backend.app.graph.nodes.vision_agent.ollama_service.check_health", return_value={"available": True, "models": ["qwen3-vl:8b"]}):
        with patch("backend.app.graph.nodes.vision_agent.ollama_service.generate", return_value={"text": "A safety helmet is visible.", "model": "qwen3-vl:8b", "duration_ms": 200.0, "status": "success"}):
            res = await vision_agent_node(state)
            assert res["status"] == "success"
            assert "safety helmet" in res["answer"]
            assert res["vision_status"] == "success"
            assert res["model"] == "qwen3-vl:8b"

@pytest.mark.asyncio
async def test_vision_agent_model_unavailable():
    """Test behavior when qwen3-vl:8b is missing."""
    state = {"request_id": "req_vis_none", "message": "Inspect image", "image_path": "tests/test_image.png"}
    
    with patch("backend.app.graph.nodes.vision_agent.ollama_service.check_health", return_value={"available": True, "models": ["qwen3.5:latest"]}):
        res = await vision_agent_node(state)
        assert res["status"] == "not_available"
        assert "qwen3-vl:8b not available" in res["answer"]

@pytest.mark.asyncio
async def test_vision_agent_invalid_image():
    """Test behavior with missing image file."""
    state = {"request_id": "req_vis_fail", "message": "Inspect image", "image_path": "non_existent.png"}
    
    with patch("backend.app.graph.nodes.vision_agent.ollama_service.check_health", return_value={"available": True, "models": ["qwen3-vl:8b"]}):
        res = await vision_agent_node(state)
        assert res["status"] == "error"
        assert "not found" in res["answer"]
        assert res["vision_status"] == "failed"

def test_vision_agent_node():
    # This is the old sync test, we can remove it or keep it for backward compatibility if it was just a placeholder.
    # Since we converted to async, we should replace it.
    pass

