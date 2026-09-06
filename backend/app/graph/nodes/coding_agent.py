from backend.app.graph.state import VaultAIState
from backend.app.services.ollama_service import ollama_service
from backend.app.services.sandbox_service import execute_code
from backend.app.audit.audit import audit_logger
import asyncio
import re


CODING_MODEL = "qwen2.5-coder:7b"
MAX_CODING_ATTEMPTS = 2


async def coding_agent_node(state: VaultAIState) -> VaultAIState:
    """Coding agent node.
    Generates Python code via the local Ollama model and executes it in the sandbox.
    Implements a bounded iterative loop: Initial Generation -> Execution -> (Optional) Correction.
    """
    request_id = state.get("request_id")
    message = state.get("message", "")
    
    # Initialize attempt counter
    attempts = 0

    # 1. Model Availability Check
    health = ollama_service.check_health()
    if not health["available"] or CODING_MODEL not in health.get("models", []):
        state["answer"] = f"Coding model {CODING_MODEL} not available locally. Please run 'ollama pull {CODING_MODEL}'."
        state["model"] = CODING_MODEL
        state["status"] = "not_available"
        state["coding_status"] = "not_available"
        return state

    while attempts < MAX_CODING_ATTEMPTS:
        attempts += 1
        state["coding_attempts"] = attempts

        audit_logger.log(
            event_type="agent_execution",
            resource_id=request_id,
            details={"agent": "coding_agent", "message": message, "attempt": attempts},
        )

        # 2. Generate Code
        try:
            if attempts == 1:
                # Initial Generation
                system_prompt = (
                    "You are a professional Python coding assistant. "
                    "Your goal is to provide executable Python code that solves the user's request. "
                    "IMPORTANT: Return ONLY the raw Python code. Do NOT include markdown code blocks (```python), "
                    "do NOT include explanations, and do NOT include any prose. "
                    "The output must be directly executable by a Python interpreter."
                )
                prompt = message
            else:
                # Correction Generation
                prev_code = state.get("generated_code", "")
                sandbox_res = state.get("sandbox_result", {})
                stderr = sandbox_res.get("stderr", "No stderr available")
                stdout = sandbox_res.get("stdout", "No stdout available")
                exit_code = sandbox_res.get("exit_code", "Unknown")
                timed_out = sandbox_res.get("timed_out", False)

                system_prompt = (
                    "You are a professional Python coding assistant. "
                    "The previous code you generated failed during execution in the sandbox. "
                    "Your task is to analyze the failure and provide the CORRECTED executable Python code. "
                    "IMPORTANT: Return ONLY the raw Python code. Do NOT include markdown code blocks, "
                    "do NOT include explanations, and do NOT include any prose."
                )
                prompt = (
                    f"ORIGINAL REQUEST: {message}\n\n"
                    f"PREVIOUS CODE:\n{prev_code}\n\n"
                    f"EXECUTION FAILURE:\n"
                    f"Exit Code: {exit_code}\n"
                    f"Timed Out: {timed_out}\n"
                    f"STDOUT: {stdout}\n"
                    f"STDERR: {stderr}\n\n"
                    f"Please provide the corrected executable Python code."
                )

            gen = ollama_service.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                model=CODING_MODEL,
                role="coding",
            )
            generated_code = gen.get("text", "").strip()
            
            # Basic cleanup of markdown blocks if the model ignored instructions
            if generated_code.startswith("```"):
                generated_code = re.sub(r'^```(?:python)?\n?', '', generated_code)
                generated_code = re.sub(r'\n?```$', '', generated_code)
                generated_code = generated_code.strip()

        except Exception as exc:
            state["answer"] = f"Failed to generate code: {exc}"
            state["model"] = CODING_MODEL
            state["status"] = "error"
            state["coding_status"] = "error"
            return state

        state["generated_code"] = generated_code

        # 3. Execute in Sandbox
        try:
            sandbox_result = await execute_code(generated_code)
        except Exception as exc:
            state["answer"] = f"Sandbox execution error: {exc}"
            state["status"] = "error"
            return state

        # Store structured result in state
        state["sandbox_result"] = {
            "request_id": request_id,
            "language": "python",
            "stdout": sandbox_result.stdout,
            "stderr": sandbox_result.stderr,
            "exit_code": sandbox_result.exit_code,
            "duration_seconds": sandbox_result.duration,
            "timed_out": sandbox_result.timed_out,
            "error_message": sandbox_result.error_message,
        }

        # 4. Evaluate Result
        success = (sandbox_result.exit_code == 0) and (not sandbox_result.timed_out)

        if success:
            state["answer"] = sandbox_result.stdout or "Code executed successfully (no output)."
            state["model"] = CODING_MODEL
            state["status"] = "success"
            state["coding_status"] = "success"
            state["duration_ms"] = sandbox_result.duration * 1000
            return state

    # 5. Final Failure after all attempts
    state["answer"] = state["sandbox_result"].get("stderr") or "Code execution failed after maximum retries."
    state["model"] = CODING_MODEL
    state["status"] = "error"
    state["coding_status"] = "failed"
    state["duration_ms"] = state["sandbox_result"].get("duration_seconds", 0) * 1000
    return state
