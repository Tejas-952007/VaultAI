import chromadb
from sentence_transformers import SentenceTransformer
import requests


# ============================================================
# 1. LOAD THE EMBEDDING MODEL
# ============================================================

embedding_model = SentenceTransformer("all-MiniLM-L6-v2")


# ============================================================
# 2. CONNECT TO THE EXISTING CHROMADB
# ============================================================

client = chromadb.PersistentClient(
    path="data/chroma_db"
)


# ============================================================
# 3. CONNECT TO OUR MULTI-DOCUMENT COLLECTION
# ============================================================

collection = client.get_collection(
    name="sih_multidocuments"
)


# ============================================================
# 4. OLLAMA SETTINGS
# ============================================================

OLLAMA_URL = "http://localhost:11434/api/generate"

OLLAMA_MODEL = "qwen3.5:latest"


# ============================================================
# 5. RETRIEVE RELEVANT CHUNKS
# ============================================================

def retrieve_chunks(question, top_k=5):

    # Convert the question into an embedding
    question_embedding = embedding_model.encode(
        [question]
    )[0]

    # Search ChromaDB for similar chunks
    results = collection.query(
        query_embeddings=[question_embedding.tolist()],
        n_results=top_k
    )

    documents = results["documents"][0]

    metadatas = results["metadatas"][0]

    return documents, metadatas


# ============================================================
# 6. ASK QWEN THROUGH OLLAMA
# ============================================================

def ask_llm(question, documents, metadatas):

    # Combine retrieved chunks into one context
    context_parts = []

    for i, document in enumerate(documents):

        source = metadatas[i]["source"]

        context_parts.append(
            f"[Source: {source}]\n{document}"
        )

    context = "\n\n".join(context_parts)


    # Create the prompt for Qwen
    prompt = f"""
You are an AI assistant for the SIH project.

Answer the user's question using ONLY the provided context.

If the answer is not present in the context, say:
"I could not find this information in the provided documents."

Do not invent or assume information.

USER QUESTION:
{question}

CONTEXT:
{context}

Give a clear and concise answer.
"""


    # Send the prompt to Ollama
    response = requests.post(
        OLLAMA_URL,
        json={
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.2,
                "num_ctx": 2048
            }
        },
        timeout=120
    )


    # Check whether Ollama responded successfully
    response.raise_for_status()


    # Extract the generated answer
    answer = response.json()["response"]

    return answer


# ============================================================
# 7. COMPLETE RAG PIPELINE
# ============================================================

def ask_question(question):

    print("\nUSER QUESTION:")
    print(question)


    # Retrieve relevant chunks
    documents, metadatas = retrieve_chunks(
        question,
        top_k=5
    )


    # Show retrieved information
    print("\nRETRIEVED SOURCES:")

    for i, metadata in enumerate(metadatas):

        print(
            f"{i + 1}. {metadata['source']}"
        )


    print("\nGENERATING ANSWER...")


    # Ask Qwen using the retrieved context
    answer = ask_llm(
        question,
        documents,
        metadatas
    )


    print("\nFINAL ANSWER:")
    print(answer)


# ============================================================
# 8. TEST QUESTION
# ============================================================

question = "What is the recommended technology stack?"

ask_question(question)