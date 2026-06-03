import re 

def is_invalid_text(text: str, min_length: int = 10) -> bool:
    """  
        Checks if Text is likely OCR grabage or is Valid
        Returns TRUE if text is INVALID/UNREADABLE/GARBAGE
    """
    
    if not text or len(text.strip()) < min_length:
        return True 
    
    cleaned = text.strip()
    
    #Check High Ratio of special characters
    special_chars = len(re.findall(r'[^a-zA-Z0-9\s.,;:!?-]', cleaned))
    if special_chars / len(cleaned) > 0.3:
        return True
    
    #check for very low vowel ratio
    vowels = len(re.findall(r'[aeiouAEIOU]',cleaned))
    alpha_chars = len(re.findall(r'[a-zA-Z]', cleaned))
    if alpha_chars > 0 and (vowels / alpha_chars) < 0.1:
        return True 
    
    return False 

def validate_extraction(raw_text:str, section_name:str) -> dict:
    
    if is_invalid_text(raw_text):
        return {
            "is_valid":False,
            "status":"UNREADABLE",
            "cleaned_text": "",
            "flag": f"[MISSING - OCR FAILED/GARBAGE - REQUIRES CLINICIAN REVIEW]"
        }
        
    return {
        "is_valid":True,
        "status": "VALID",
        "cleaned_text": raw_text,
        "flag": None 
    }
            