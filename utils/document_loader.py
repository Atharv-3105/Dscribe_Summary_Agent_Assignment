from pathlib import Path 
from tools.pdf_reader import PDFReaderTool
from logger import get_logger

logger = get_logger(__name__)

def load_document(patient_file_path: Path):
    
    reader = PDFReaderTool()
    
    documents = []
    
    try:
        
        document = reader.read_pdf(patient_file_path)
        
        print(document.filename)
        
        print(len(document.pages))
        
        print(document.text[:1000])
        
    except Exception as e:
        
        logger.error(f"Error while loading file from {patient_file_path}: {e}")
        
        