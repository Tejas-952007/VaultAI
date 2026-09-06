import time
from typing import Dict, Any, Optional, List
import httpx
from backend.app.config import settings
from backend.app.security import validate_model_name


class OllamaServiceError(Exception):
    """Custom exception for Ollama model service errors."""
    def __init__(self, code: str, message: str, details: Optional[Dict[str, Any]] = None):
        self.code = code
        self.message = message
        self.details = details or {}
        super().__init__(message)


class OllamaService:
    def __init__(self, base_url: Optional[str] = None, default_model: Optional[str] = None, timeout: Optional[float] = None):
        self.base_url = (base_url or settings.OLLAMA_URL).rstrip("/")
        self.default_model = validate_model_name(default_model or settings.OLLAMA_MODEL, role="document")
        self.timeout = timeout or settings.OLLAMA_TIMEOUT_SECONDS

    def check_health(self) -> Dict[str, Any]:
        """Check connection to local Ollama instance."""
        url = f"{self.base_url}/api/tags"
        try:
            with httpx.Client(timeout=5.0) as client:
                response = client.get(url)
                if response.status_code == 200:
                    models_data = response.json().get("models", [])
                    model_names = [m.get("name") for m in models_data]
                    return {
                        "available": True,
                        "models": model_names,
                        "url": self.base_url
                    }
                return {
                    "available": False,
                    "error": f"Ollama returned HTTP status {response.status_code}",
                    "url": self.base_url
                }
        except httpx.ConnectError:
            return {
                "available": False,
                "error": f"Could not connect to local Ollama service at {self.base_url}",
                "url": self.base_url
            }
        except Exception as e:
            return {
                "available": False,
                "error": str(e),
                "url": self.base_url
            }

    def generate(self, prompt: str, system_prompt: Optional[str] = None, model: Optional[str] = None, images: Optional[List[str]] = None, role: Optional[str] = None, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Send a generation request to the local Ollama instance.
        Supports multimodal input via the 'images' parameter (list of base64 encoded images).
        Returns dict containing text, model, duration_ms, and status.
        """
        target_model = validate_model_name(model or self.default_model, role=role)
        url = f"{self.base_url}/api/generate"

        payload = {
            "model": target_model,
            "prompt": prompt,
            "stream": False,
            # Qwen3.5 can spend the generation budget in its internal
            # thinking stream, leaving the final response empty.
            "think": False,
        }
        if system_prompt:
            payload["system"] = system_prompt
        if images:
            payload["images"] = images
        if options:
            payload["options"] = options

        start_time = time.perf_counter()

        try:
            with httpx.Client(timeout=httpx.Timeout(self.timeout, connect=10.0)) as client:
                response = client.post(url, json=payload)
                elapsed_ms = (time.perf_counter() - start_time) * 1000.0

                if response.status_code == 200:
                    data = response.json()
                    answer_text = data.get("response", "")
                    actual_model = data.get("model", target_model)
                    
                    # Ollama returns total_duration in nanoseconds if present
                    eval_duration_ns = data.get("total_duration")
                    duration_ms = (eval_duration_ns / 1_000_000.0) if eval_duration_ns else round(elapsed_ms, 2)

                    return {
                        "text": answer_text,
                        "model": actual_model,
                        "duration_ms": duration_ms,
                        "status": "success"
                    }
                elif response.status_code == 404:
                    raise OllamaServiceError(
                        code="MODEL_NOT_FOUND",
                        message=f"Local model '{target_model}' is not pulled in Ollama. Run 'ollama pull {target_model}'."
                    )
                else:
                    raise OllamaServiceError(
                        code="MODEL_ERROR",
                        message=f"Ollama returned HTTP error status {response.status_code}: {response.text}"
                    )

        except httpx.ConnectError:
            raise OllamaServiceError(
                code="MODEL_UNAVAILABLE",
                message=f"Local Ollama model service is unavailable at {self.base_url}. Ensure Ollama is running locally."
            )
        except httpx.TimeoutException:
            raise OllamaServiceError(
                code="MODEL_TIMEOUT",
                message=f"Local Ollama model inference timed out after {self.timeout} seconds."
            )
        except OllamaServiceError:
            raise
        except Exception as e:
            raise OllamaServiceError(
                code="MODEL_EXECUTION_ERROR",
                message=f"Error executing local model inference: {str(e)}"
            )


# Singleton instance for general use
ollama_service = OllamaService()
