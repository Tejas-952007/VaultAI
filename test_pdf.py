from pypdf import PdfReader

pdf_path = "data/test.pdf"
reader  = PdfReader(pdf_path)
print("No. of pages:", len(reader.pages))

for i, page in enumerate(reader.pages):
    text = page.extract_text()
    
    print(f"\n--- PAGE {i + 1} ---")
    print(text[:1000])