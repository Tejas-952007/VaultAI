import chromadb
from sentence_transformers import SentenceTransformer
import requests


# LOAD THE EMBEDDING MODEL
model = SentenceTransformer("all-MiniLM-L6-v2")


# CONNECT TO EXISTING CHROMADB
client = chromadb.PersistentClient(path="data/chroma_db")

collection = client.get_collection(name="sih_documents")


# USER QUESTION
question = "What is the recommended technology stack?"


# CONVERT QUESTION INTO EMBEDDING
question_embedding = model.encode([question])


# SEARCH CHROMADB
results = collection.query(
    query_embeddings=question_embedding.tolist(),
    n_results=3
)


# GET RETRIEVED CHUNKS
retrieved_chunks = results["documents"][0]


# COMBINE THE CHUNKS
context = "\n\n".join(retrieved_chunks)


# CREATE PROMPT FOR QWEN
prompt = f"""
You are an AI assistant for the SIH 2026 project.

Answer the user's question using ONLY the information provided in the context.

If the answer is not present in the context, say:
"I could not find the answer in the provided document."

Context:
{context}

Question:
{question}

Give a clear and complete answer.
"""


# SEND PROMPT TO OLLAMA
response = requests.post(
    "http://localhost:11434/api/generate",
    json={
        "model": "qwen3.5:latest",
        "prompt": prompt,
        "stream": False
    }
)


# GET FINAL ANSWER
answer = response.json()["response"]


# PRINT RESULTS
print("\nUSER QUESTION:")
print(question)

print("\nRETRIEVED CHUNKS:")
for i, chunk in enumerate(retrieved_chunks):
    print(f"\n--- CHUNK {i+1} ---")
    print(chunk)

print("\nFINAL ANSWER:")
print(answer)