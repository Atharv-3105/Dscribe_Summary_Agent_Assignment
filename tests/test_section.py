from pathlib import Path 
from tools.pdf_reader import PDFReaderTool
from tools.section_extractor import SectionExtractorTool

reader = PDFReaderTool()
document = reader.read_pdf(Path("data/patient_3.pdf"))

extractor = SectionExtractorTool()

sections = (extractor.extract_sections(document.text))

print("\n")

print("DIAGNOSIS")
print("-"*50)
print(sections.diagnosis[:1000])

print("\n")

print("HOSPITAL COURSE")
print("-"*50)
print(sections.hospital_course[:1000])