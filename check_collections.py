import chromadb

client = chromadb.PersistentClient(
    path="data/chroma_db"
)

print("\nAVAILABLE COLLECTIONS:")
print("======================")

collections = client.list_collections()

for collection in collections:

    print(f"\nCollection: {collection.name}")

    col = client.get_collection(collection.name)

    print("Total chunks:", col.count())

    # Get all metadata entries
    data = col.get(
        include=["metadatas"]
    )

    # Find unique PDF sources
    sources = set()

    for metadata in data["metadatas"]:
        if metadata:
            sources.add(metadata.get("source", "Unknown"))

    print("\nPDF sources found:")

    for source in sorted(sources):
        print(f"- {source}")

    print("-" * 50)