from sentence_transformers import SentenceTransformer
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter


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


# CONVERT ALL CHUNKS INTO EMBEDDINGS
chunk_embeddings = model.encode(chunks)


# SHOW RESULTS
print("Embedding shape:", chunk_embeddings.shape)

print("\nFirst chunk:")
print(chunks[0])

print("\nFirst chunk embedding (first 10 numbers):")
print(chunk_embeddings[0][:10])