import chromadb

client = chromadb.PersistentClient(
    path="data/chroma_db"
)

collection = client.get_collection(
    name="sih_documents"
)

print("\n==============================")
print("COLLECTION CHECK")
print("==============================")

print("Total chunks:", collection.count())

results = collection.get(
    include=["metadatas"]
)

print("\nMetadata entries:")

for i, metadata in enumerate(results["metadatas"]):
    
    print(f"\nChunk {i + 1}:")
    print(metadata)