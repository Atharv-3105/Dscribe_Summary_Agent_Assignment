import re 
from logger import get_logger
from models.model import Sections

logger = get_logger(__name__)

class SectionExtractorTool:
    
    SECTION_PATTERNS = {
        "diagnosis": [r"DIAGNOSIS\s*:?"],
        "history": [r"HISTORY\s*:?"],
        "past_history": [r"PAST HISTORY\s*:?"],
        "physical_exam": [r"PHYSICAL EXAMINATION\s*:?"],
        "investigations": [r"INVESTIGATIONS\s*:?"],
        "hospital_course": [r"COURSE IN THE HOSPITAL\s*:?"],
        "medications": [r"MEDICATIONS\s*:?|DRUG CHART\s*:?"],
        "follow_up": [r"FOLLOW[- ]?UP\s*:?"],
        "discharge_condition": [r"DISCHARGE CONDITION\s*:?|CONDITION AT DISCHARGE\s*:?"]
    }
    
    #Enforce a Max Window of Characters to prevent a section getting all the 70-page characters
    MAX_SECTION_LENGTH = 2000
    
    def extract_sections(self, text: str)-> Sections:
        
        logger.info("Starting section extraction")
        
        sections = Sections()
        
        matches = []
        
        for section_name, patterns in self.SECTION_PATTERNS.items():
            
            for pattern in patterns:
                
                for match in re.finditer(pattern, text, re.IGNORECASE):
                    matches.append((match.start(), section_name))
         
        #Sort the matches and remove duplicates           
        matches.sort(key=lambda x : x[0])
        seen = set()
        unique_matches = []
        for pos, name in matches:
            if name not in seen:
                seen.add(name)
                unique_matches.append((pos,name))
        matches = unique_matches
        
        logger.info(f"Detected {len(matches)} sections")
        
        if not matches:
            logger.warning("No sections detected")
            sections.miscellaneous = text[:1000]
            return sections

        for index, (start_posi, section_name) in enumerate(matches):
            
            if index + 1 < len(matches):
                end_posi = matches[index + 1][0]
                
            else:
                #Instead of giving all the text, we clip to a max window
                end_posi =  min(start_posi + self.MAX_SECTION_LENGTH, len(text))
            
            section_text = (text[start_posi : end_posi]).strip()
            
            setattr(sections,section_name, section_text)
            
        logger.info("Section Extraction completed")
        
        logger.info(f"Diagnosis Length: {len(sections.diagnosis)}")
        logger.info(f"History Extraction: {len(sections.history)}")
        
        return sections                