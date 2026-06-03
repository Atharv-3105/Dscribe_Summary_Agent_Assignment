from pathlib import Path 
from tools.pdf_reader import PDFReaderTool

reader = PDFReaderTool()

doc = reader.read_pdf(Path("data/patient_3.pdf"))

print(doc.filename)
print(len(doc.pages))
print(doc.text[:1000])