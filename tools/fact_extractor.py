import re 
from logger import get_logger
from models.model import Sections, ExtractedFacts

logger = get_logger(__name__)

class FactExtractorTool:
    
    def extract_facts(self,sections: Sections) -> ExtractedFacts:
        """  
            This function will convert RAW TEXT BLOCKS(SECTIONS) into structured clinical facts
        """
        
        logger.info("Starting structured fact extraction")
        facts = ExtractedFacts()
        
        #1. Harcoded Regex Extraction
        facts.admission_date = self._extract_date(sections.history, r"Date(?: of)? Admission\s*[:\-]?\s*([0-9]{2}[/-][0-9]{2,4}[/-][0-9]{2,4})")
        facts.discharge_date = self._extract_date(sections.discharge_condition, r"Date(?: of)? Discharge\s*[:\-]?\s*([0-9]{2}[/-][0-9]{2,4}[/-][0-9]{2,4})")
        
        #2. Medications Extraction
        all_meds = self._extract_medications(sections.medications)
        
        #Simple Split Logic: If text contains "discharge", "home", "outpatient" we put it in discharge_meds
        lower_text = sections.medications.lower()
        if any(word in lower_text for word in ["discharge", "home", "outpatient","on discharge"]):
            facts.discharge_meds = all_meds
        else:
            facts.admission_meds = all_meds
        
        #3. Diagnoses Extraction (Handling OCR Garbage)
        facts.diagnoses = self._extract_diagnoses(sections.diagnosis)
        
        #4. Follow-up & Condition
        facts.follow_up = self._clean_list(sections.follow_up)
        facts.discharge_condtion = sections.discharge_condition.strip() if sections.discharge_condition.strip() else None 
        
        logger.info("Structured fact extraction completed")
        return facts
    
    def _extract_date(self, text: str, pattern: str) -> str|None :
        if not text or not text.strip():
            return None 
        
        match =re.search(pattern, text, re.IGNORECASE)
        return match.group(1) if match else None 
    
    def _extract_medications(self, text:str) -> list[str]:
        
        if not text or not text.strip():
            return []
        
        #Words which we need to ignore from our medications extraction
        boilerplate = [
            "doctor", "signature", "weight", "diagnosis", "history", 
            "examination", "route", "dose", "frequency", "date", "time",
            "drug chart", "nebulisation", "fluids", "infusions", "stop order",
            "chief complaints", "referred by", "informants", "allergies",
            "regular prescription", "pallor", "icterus", "clubbing", "edema",
            "cns", "gcs", "pupils", "plantar", "bp", "rr", "spo2", "temp",
            "wt", "gross"
        ]
        
        raw_meds = re.split(r'\n|,', text)
        clean_meds = []
        
        for med in raw_meds:
            cleaned = med.strip()
            
            if len(cleaned) < 4: continue 
            
            if any(phrase in cleaned.lower() for phrase in boilerplate): continue 
            
            special_chars = len(re.findall(r'[^a-zA-Z0-9\s.,;:-]', cleaned))
            if special_chars / len(cleaned) > 0.2: continue
            
            clean_meds.append(cleaned)
                
        return clean_meds
    
    def _extract_diagnoses(self, text: str) -> list[str]:
        
        if not text or not text.strip():
            return ["[MISSING - REQUIRES CLINICIAN REVIEW]"]
        
        special_chars = len(re.findall(r'[^a-zA-Z0-9\s.,;:-]', text))
        if special_chars / len(text) > 0.1:
            return ["[UNREADABLE - OCR FAILED - REQUIRES CLINICIAN REVIEW]"]
        
        #Check for specific garbage pattern
        alpha_chars = len(re.findall(r'[a-zA-Z]', text))
        vowels = len(re.findall(r'[aeiouAEIOU]', text))
        
        if alpha_chars > 0 and (vowels / alpha_chars) < 0.15:
            return ["UREADABLE - OCR FAILED - REQUIRES CLINICIAN REVIEW"]
        
        return [line.strip() for line in text.split("\n") if line.strip()]
    
    def _clean_list(self, text:str)-> list[str]:
        if not text or not text.strip():
            return []
        
        return [line.strip() for line in text.split("\n") if line.strip()]