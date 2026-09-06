from typing import TypedDict, Optional
from langgraph.graph import StateGraph, START, END
import ollama

from test_llm_rag1 import generate_answer
from document_selector import select_document, retrieve_from_document

# ============================================================
# 1. STATE
# ============================================================

class VaultAIState(TypedDict):
    question: str
    route: Optional[str]
    answer: Optional[str]


# ============================================================
# 2. ROUTER
# ============================================================

def router(state: VaultAIState):
    question = state["question"].lower().strip()

    # Vision-related keywords
    vision_words = [
        "image", "photo", "picture", "certificate",
        "screenshot", "scan", "visual", "shown",
        "look at", "what do you see", "in this"
    ]

    # Coding-related keywords
    coding_words = [
        "code", "coding", "python", "java", "program",
        "programming", "debug", "error", "function",
        "algorithm", "implement", "write a program",
        "write code", "fix this code"
    ]

    # Check vision first
    if any(word in question for word in vision_words):
        route = "vision"

    # Then check coding
    elif any(word in question for word in coding_words):
        route = "coding"

    # Otherwise treat it as a document question
    else:
        route = "document"

    print(f"\n[LangGraph Router] Selected: {route}")

    return {"route": route}


# ============================================================
# 3. DOCUMENT NODE
# ============================================================

def document_node(state: VaultAIState):

    print("\n[Document Agent] Using Qwen3.5 + RAG")

    question = state["question"]

    # Select the most relevant PDF
    selected_document = select_document(question)

    # Retrieve relevant chunks from that PDF
    results = retrieve_from_document(
        question,
        selected_document,
        top_k=6
    )

    # Generate the final answer using Qwen3.5
    answer = generate_answer(
        question,
        results
    )

    return {
        "answer": answer
    }


# ============================================================
# 4. CODING NODE
# ============================================================

def coding_node(state: VaultAIState):

    print("\n[Coding Agent] Using DeepSeek Coder 1.3B Q4_K_M")

    question = state["question"]

    response = ollama.chat(
        model="deepseek-coder:1.3b-instruct-q4_K_M",
        messages=[
            {
                "role": "user",
                "content": question
            }
        ]
    )

    return {
        "answer": response["message"]["content"]
    }


# ============================================================
# 5. VISION NODE
# ============================================================

def vision_node(state: VaultAIState):
    print("\n[Vision Agent] Using Qwen3-VL:8B")

    question = state["question"]

    # Ask the user for the image
    image_path = input("Enter the image path: ").strip().strip('"')

    # Send image + question to Qwen3-VL
    response = ollama.chat(
        model="qwen3-vl:8b",
        messages=[
            {
                "role": "user",
                "content": question,
                "images": [image_path]
            }
        ]
    )

    answer = response["message"]["content"]

    return {
        "answer": answer
    }


# ============================================================
# 6. BUILD LANGGRAPH
# ============================================================

graph_builder = StateGraph(VaultAIState)

graph_builder.add_node("router", router)
graph_builder.add_node("document", document_node)
graph_builder.add_node("coding", coding_node)
graph_builder.add_node("vision", vision_node)


# ============================================================
# 7. CONNECT ROUTER TO THE CORRECT NODE
# ============================================================

graph_builder.add_edge(START, "router")

graph_builder.add_conditional_edges(
    "router",
    lambda state: state["route"],
    {
        "document": "document",
        "coding": "coding",
        "vision": "vision"
    }
)


# ============================================================
# 8. END EACH BRANCH
# ============================================================

graph_builder.add_edge("document", END)
graph_builder.add_edge("coding", END)
graph_builder.add_edge("vision", END)


# ============================================================
# 9. COMPILE GRAPH
# ============================================================

graph = graph_builder.compile()


# ============================================================
# 10. RUN VAULTAI
# ============================================================

if __name__ == "__main__":

    print("=" * 60)
    print("VAULTAI - LANGGRAPH ORCHESTRATOR")
    print("=" * 60)

    question = input("\nWhat questions do you have? ")

    result = graph.invoke({
        "question": question,
        "route": None,
        "answer": None
    })

    print("\n" + "=" * 60)
    print("RESULT")
    print("=" * 60)

    print(result["answer"])