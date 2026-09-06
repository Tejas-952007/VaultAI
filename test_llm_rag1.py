import requests
import re
from document_selector import select_document, retrieve_from_document

# ============================================================
# 1. OLLAMA SETTINGS
# ============================================================
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen3.5:latest"


# ============================================================
# 2. GENERATE ANSWER USING OLLAMA
# ============================================================
def generate_answer(question, retrieved_results):

    # Combine retrieved chunks into one context
    context_parts = []
    for i, result in enumerate(retrieved_results, start=1):
        source = result["metadata"].get("source", "Unknown")
        text = result["document"]
        context_parts.append(
            f"""
SOURCE {i}
PDF: {source}
{text}
"""
        )
    context = "\n".join(context_parts)

    # --------------------------------------------------------
    # Prompt for the LLM
    # --------------------------------------------------------
    prompt = f"""
You are a document-based question answering assistant.
Answer the user's question ONLY using the information
provided in the retrieved context below.
Do NOT use outside knowledge.
If the answer cannot be found in the retrieved context,
say:
"I could not find the answer in the selected document."
Give a clear, concise and well-structured answer.
USER QUESTION:
{question}
RETRIEVED CONTEXT:
{context}
FINAL ANSWER:
"""

    # --------------------------------------------------------
    # Send request to Ollama
    # --------------------------------------------------------
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False,
        "think": False,          # Qwen3.5 is a thinking model - turn
                                  # reasoning off so it doesn't burn its
                                  # whole output budget before answering.
        "options": {
            "num_predict": 800,  # enough room for a full final answer
            "num_ctx": 8192      # enough context for multi-PDF retrieval
        }
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=120)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        return f"Error contacting Ollama: {e}"

    result = response.json()
    answer = result.get("response", "")

    # Safety net: strip any leftover <think>...</think> block in case
    # the model still emits one despite think=False.
    answer = re.sub(r"<think>.*?</think>", "", answer, flags=re.DOTALL).strip()

    if not answer:
        print("\n[WARNING] Ollama returned an empty response. Raw payload:")
        print(result)
        answer = "I could not find the answer in the selected document."

    return answer


# ============================================================
# 3. MAIN
# ============================================================
if __name__ == "__main__":

    print("\n" + "=" * 60)
    print("LOCAL RAG QUESTION ANSWERING")
    print("=" * 60)

    question = input("\nEnter your question: ")

    selected_document = select_document(question)

    results = retrieve_from_document(
        question,
        selected_document,
        top_k=6
    )

    print("\n" + "=" * 60)
    print("GENERATING ANSWER WITH QWEN")
    print("=" * 60)

    answer = generate_answer(question, results)

    print("\n" + "=" * 60)
    print("FINAL ANSWER")
    print("=" * 60)
    print(answer)

    print("\n" + "-" * 60)
    print("SOURCE DOCUMENT(S):")
    print(selected_document)
    print("-" * 60)