import os
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer
from langchain_text_splitters import RecursiveCharacterTextSplitter
import chromadb


# ============================================================
# 1. FOLDER PATH
# ============================================================

DOCUMENTS_FOLDER = "data/documents"


# ============================================================
# 2. LOAD EMBEDDING MODEL
# ============================================================

embedding_model = SentenceTransformer("all-MiniLM-L6-v2")


# ============================================================
# 3. CONNECT TO CHROMADB
# ============================================================

client = chromadb.PersistentClient(
    path="data/chroma_db"
)


# ============================================================
# 4. CREATE / GET COLLECTION
# ============================================================

collection = client.get_or_create_collection(
    name="sih_multidocuments"
)


# ============================================================
# 5. CREATE TEXT SPLITTER
# ============================================================

splitter = RecursiveCharacterTextSplitter(
    chunk_size=800,
    chunk_overlap=100
)


# ============================================================
# 6. READ ALL PDF FILES
# ============================================================

all_chunks = []
all_metadata = []


for filename in os.listdir(DOCUMENTS_FOLDER):

    if not filename.lower().endswith(".pdf"):
        continue

    pdf_path = os.path.join(
        DOCUMENTS_FOLDER,
        filename
    )

    print(f"\nProcessing: {filename}")

    reader = PdfReader(pdf_path)

    text = ""

    for page in reader.pages:

        page_text = page.extract_text()

        if page_text:
            text += page_text + "\n"


    # ========================================================
    # 7. SPLIT PDF TEXT INTO CHUNKS
    # ========================================================

    chunks = splitter.split_text(text)

    print(f"Chunks created: {len(chunks)}")


    # ========================================================
    # 8. STORE CHUNKS AND SOURCE INFORMATION
    # ========================================================

    for chunk in chunks:

        all_chunks.append(chunk)

        all_metadata.append({
            "source": filename
        })


# ============================================================
# 9. CREATE EMBEDDINGS
# ============================================================

print("\nCreating embeddings...")

embeddings = embedding_model.encode(
    all_chunks
)


# ============================================================
# 10. CREATE UNIQUE IDS
# ============================================================

ids = [
    f"doc_{i}"
    for i in range(len(all_chunks))
]


# ============================================================
# 11. STORE EVERYTHING IN CHROMADB
# ============================================================

collection.add(
    ids=ids,
    documents=all_chunks,
    embeddings=embeddings.tolist(),
    metadatas=all_metadata
)


# ============================================================
# 12. FINAL INFORMATION
# ============================================================

print("\n===================================")
print("DOCUMENT INGESTION COMPLETE")
print("===================================")

print("Total documents processed:", len(
    set(metadata["source"] for metadata in all_metadata)
))

print("Total chunks stored:", len(all_chunks))