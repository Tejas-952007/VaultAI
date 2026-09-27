import uuid
from backend.app.schemas import ChatRequest, ChatResponse
from backend.app.services.ollama_service import ollama_service
from backend.app.graph.state import VaultAIState
from backend.app.graph.workflow import vaultai_graph_app
from backend.app.audit.audit import audit_logger


class ChatService:
    async def handle_chat(
        self,
        request: ChatRequest,
        employee_position: str | None = None,
    ) -> ChatResponse:
        request_id = str(uuid.uuid4())

        audit_logger.log(
            event_type="chat_request",
            resource_id=request_id,
            details={"message": request.message, "document_ids": request.document_ids}
        )

        initial_state: VaultAIState = {
            "request_id": request_id,
            "message": request.message,
            "document_ids": request.document_ids,
            "employee_position": employee_position,
            "image_path": request.image_path,
            "route": "document",
            "selected_documents": [],
            "evidence": [],
            "model": ollama_service.default_model,
            "duration_ms": 0.0,
            "answer": "",
            "status": "processing",
            "error": None,
            "tool_results": [],
            "artifacts": []
        }

        # Invoke LangGraph routing & agent workflow
        # Since coding_agent_node is now async, we must await the graph invocation if it's async
        # vaultai_graph_app.invoke is typically sync unless using ainvoke.
        # However, if the nodes are async, we should use ainvoke.
        final_state = await vaultai_graph_app.ainvoke(initial_state)

        return ChatResponse(
            request_id=request_id,
            answer=final_state.get("answer", ""),
            route=final_state.get("route", "document"),
            model=final_state.get("model", ollama_service.default_model),
            duration_ms=final_state.get("duration_ms", 0.0),
            evidence=final_state.get("evidence", []),
            status=final_state.get("status", "success"),
            generated_code=final_state.get("generated_code"),
            sandbox_result=final_state.get("sandbox_result"),
            coding_attempts=final_state.get("coding_attempts"),
            coding_status=final_state.get("coding_status"),
            coding_error=final_state.get("coding_error"),
            vision_status=final_state.get("vision_status"),
            vision_result=final_state.get("vision_result"),
            vision_error=final_state.get("vision_error"),
        )


chat_service = ChatService()
