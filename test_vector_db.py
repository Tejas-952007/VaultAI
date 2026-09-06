from sentence_transformers import SentenceTransformer
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
import chromadb


# LOAD THE PDF
pdf_path = "data/test.pdf"
reader = PdfReader(pdf_path)

text = ""

for page in reader.pages:
    text += page.extract_text() + "\n"


# SPLIT THE TEXT INTO CHUNKS
splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=50
)

chunks = splitter.split_text(text)

print("Number of chunks:", len(chunks))


# LOAD THE EMBEDDING MODEL
model = SentenceTransformer("all-MiniLM-L6-v2")


# CREATE EMBEDDINGS
embeddings = model.encode(chunks)

print("Embedding shape:", embeddings.shape)


# CREATE CHROMADB CLIENT
client = chromadb.PersistentClient(path="data/chroma_db")


# CREATE A COLLECTION
collection = client.get_or_create_collection(
    name="sih_documents"
)


# ADD CHUNKS AND EMBEDDINGS TO CHROMADB
collection.add(
    ids=[str(i) for i in range(len(chunks))],
    documents=chunks,
    embeddings=embeddings.tolist()
)


# CHECK HOW MANY DOCUMENTS ARE STORED
print("Documents stored in ChromaDB:", collection.count())