from sentence_transformers import SentenceTransformer
import chromadb
import requests


# ==========================================
# 1. LOAD THE EMBEDDING MODEL
# ==========================================

embedding_model = SentenceTransformer("all-MiniLM-L6-v2")


# ==========================================
# 2. CONNECT TO THE EXISTING CHROMADB
# ==========================================

client = chromadb.PersistentClient(
    path="data/chroma_db"
)


# ==========================================
# 3. GET OUR DOCUMENT COLLECTION
# ==========================================

collection = client.get_collection(
    name="sih_documents"
)


# ==========================================
# 4. FUNCTION TO ASK A QUESTION
# ==========================================

def ask_question(question):

    # --------------------------------------
    # Convert the question into an embedding
    # --------------------------------------

    question_embedding = embedding_model.encode(
        [question]
    ).tolist()


    # --------------------------------------
    # Search ChromaDB
    # --------------------------------------

    results = collection.query(
        query_embeddings=question_embedding,
        n_results=3
    )


    # --------------------------------------
    # Get the retrieved document chunks
    # --------------------------------------

    retrieved_chunks = results["documents"][0]


    # --------------------------------------
    # Combine the chunks into one context
    # --------------------------------------

    context = "\n\n".join(
        retrieved_chunks
    )


    # --------------------------------------
    # Create the prompt for Qwen
    # --------------------------------------

    prompt = f"""
You are VaultAI, a private AI assistant for confidential
industrial documents.

Answer the user's question using ONLY the information
provided in the context.

If the answer cannot be found in the context, say:

"I could not find the answer in the provided document."

Do not invent or assume information that is not present
in the context.

Context:
{context}

User Question:
{question}

Give a clear and concise answer.
"""


    # --------------------------------------
    # Send the prompt to local Ollama
    # --------------------------------------

    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "qwen3.5:latest",
            "prompt": prompt,
            "stream": False
        }
    )


    # --------------------------------------
    # Check whether Ollama responded correctly
    # --------------------------------------

    response.raise_for_status()


    # --------------------------------------
    # Extract Qwen's answer
    # --------------------------------------

    answer = response.json()["response"]


    # --------------------------------------
    # Return the answer and retrieved chunks
    # --------------------------------------

    return {
        "answer": answer,
        "sources": retrieved_chunks
    }


# ==========================================
# 5. TEST THE FUNCTION
# ==========================================

if __name__ == "__main__":

    question = "What is the recommended technology stack?"

    result = ask_question(question)

    print("\nUSER QUESTION:")
    print(question)

    print("\nFINAL ANSWER:")
    print(result["answer"])

    print("\nNUMBER OF SOURCES RETRIEVED:")
    print(len(result["sources"]))