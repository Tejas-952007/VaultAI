from pypdf import PdfReader

# LOAD THE PDF
pdf_path = "data/test.pdf"

reader = PdfReader(pdf_path)

text = ""

for page in reader.pages:
    text += page.extract_text() + "\n"

print("PDF loaded successfully!")
print("Number of pages:", len(reader.pages))

# CHUNK THE TEXT

from langchain_text_splitters import RecursiveCharacterTextSplitter

splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=50
)

chunks = splitter.split_text(text)

print("Number of chunks:", len(chunks))

print("\nFIRST 3 CHUNKS:\n")

for i, chunk in enumerate(chunks[:3]):
    print(f"\n--- CHUNK {i+1} ---")
    print(chunk)