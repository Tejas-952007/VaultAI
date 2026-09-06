from sentence_transformers import SentenceTransformer
import chromadb


# LOAD THE EMBEDDING MODEL
model = SentenceTransformer("all-MiniLM-L6-v2")


# CONNECT TO EXISTING CHROMADB
client = chromadb.PersistentClient(path="data/chroma_db")


# GET THE EXISTING COLLECTION
collection = client.get_collection(name="sih_documents")


# USER QUESTION
question = "What is the recommended technology stack?"


# CONVERT THE QUESTION INTO AN EMBEDDING
query_embedding = model.encode([question]).tolist()


# SEARCH CHROMADB FOR THE MOST RELEVANT CHUNKS
results = collection.query(
    query_embeddings=query_embedding,
    n_results=3
)


# PRINT THE USER QUESTION
print("\nUSER QUESTION:")
print(question)


# PRINT THE RETRIEVED CHUNKS
print("\nRETRIEVED CHUNKS:")

for i, chunk in enumerate(results["documents"][0]):
    print(f"\n--- CHUNK {i + 1} ---")
    print(chunk)