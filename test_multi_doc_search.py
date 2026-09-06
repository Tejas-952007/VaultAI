import chromadb
from sentence_transformers import SentenceTransformer


# ============================================================
# 1. LOAD THE EMBEDDING MODEL
# ============================================================

model = SentenceTransformer("all-MiniLM-L6-v2")


# ============================================================
# 2. CONNECT TO EXISTING CHROMADB
# ============================================================

client = chromadb.PersistentClient(
    path="data/chroma_db"
)


# ============================================================
# 3. CONNECT TO MULTI-DOCUMENT COLLECTION
# ============================================================

collection = client.get_collection(
    name="sih_multidocuments"
)


# ============================================================
# 4. RETRIEVE RELEVANT DOCUMENT CHUNKS
# ============================================================

def retrieve_documents(question, top_k=5):

    # Convert the question into an embedding
    question_embedding = model.encode(
        question
    ).tolist()

    # Search ChromaDB
    results = collection.query(
        query_embeddings=[question_embedding],
        n_results=top_k
    )

    return results


# ============================================================
# 5. TEST QUESTION
# ============================================================

question = "What are the environment setups we need to do in week 1 for this project?"


# ============================================================
# 6. RETRIEVE RESULTS
# ============================================================

results = retrieve_documents(question)


# ============================================================
# 7. DISPLAY RESULTS
# ============================================================

print("\n" + "=" * 60)
print("USER QUESTION")
print("=" * 60)

print(question)


documents = results["documents"][0]
metadatas = results["metadatas"][0]
distances = results["distances"][0]


print("\n" + "=" * 60)
print("RETRIEVED DOCUMENT CHUNKS")
print("=" * 60)


for i, (document, metadata, distance) in enumerate(
    zip(documents, metadatas, distances),
    start=1
):

    print(f"\n--- RESULT {i} ---")

    print(
        f"Document: {metadata.get('source', 'Unknown')}"
    )

    print(
        f"Similarity distance: {distance:.4f}"
    )

    print("\nContent:")

    print(document)


print("\n" + "=" * 60)
print(
    f"TOTAL RESULTS RETRIEVED: {len(documents)}"
)
print("=" * 60)