from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter

#LOADING THE PDF
pdf_path = "data/test.pdf"
reader = PdfReader(pdf_path)

#EXTRACTING ALL THE TEXT
full_text = ""
for page in reader.pages:
    text = page.extract_text()
    if text:
        full_text += text + "\n"
        
#CREATING A TEXT SPLITTER
splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200
)

#SPLITTING THE TEXT
chunks = splitter.split_text(full_text)

#SHOWING THE RESULTS
print("Total Characters: ", len(full_text))
print("Number of Chunks: ", len(chunks))

for i, chunk in enumerate(chunks[:5]):
    print(f"\n--- CHUNK{i+1} ---")
    print(chunk)