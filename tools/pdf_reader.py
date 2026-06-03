from pathlib import Path 
import fitz 
import pytesseract
from PIL import Image 
from io import BytesIO

from models.model import Document 
from logger import get_logger

logger = get_logger(__name__)

class PDFReaderTool:
    
    def extract_text(self, pdf_path: Path):
        
        pages = []
        pdf =fitz.open(pdf_path)
        
        try:
            for page in pdf:
                
                page_text = page.get_text()
                pages.append(page_text)
                
        finally:
            pdf.close()
            
        return pages 
    
    def extract_ocr(self,pdf_path: Path):
        
        pdf = fitz.open(pdf_path)
        
        pages = []
        
        try:
            
            for page in pdf:
                
                pix = page.get_pixmap(matrix = fitz.Matrix(2,2))
                
                image = Image.open(BytesIO(pix.tobytes("png")))
                
                page_text = (pytesseract.image_to_string(image))
                
                pages.append(page_text)
                
        finally:
            pdf.close()
            

        return pages
    
    def should_use_ocr(self, pages: list[str]):
        
        combined_text = "\n".join(pages)
        
        return len(combined_text.strip()) < 500
    
    def read_pdf(self, pdf_path: Path):
        
        logger.info(f"Reading {pdf_path.name}")
        
        pages = self.extract_text(pdf_path)
        
        extraction_method = "text"
        
        if self.should_use_ocr(pages):
            logger.info(f"OCR Extraction Required for {pdf_path.name}")
            
            ocr_pages = (self.extract_ocr(pdf_path))
            
            ocr_length = len("\n".join(ocr_pages))
            
            text_length = len("\n".join(pages))
            
            if ocr_length > text_length:
                
                pages = ocr_pages
                extraction_method = "ocr"
                
        combined_text = "\n".join(pages)
        
        document = Document(
            filename= pdf_path.name,
            text = combined_text,
            pages = pages,
        )
        
        logger.info(f"Loded "
                    f"{pdf_path.name} "
                    f"using {extraction_method}")
        
        
        return document     