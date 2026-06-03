from pydantic import BaseModel
from typing import List

class Document(BaseModel):
    
    filename: str 
    text:     str 
    pages:    List[str]
    
    
class Conflict(BaseModel):
    
    field_name:     str 
    value_a:        str 
    value_b:        str
    source_a:       str
    source_b:       str 
    
class TraceStep(BaseModel):
    
    step:       int 
    reasoning:  str
    action:     str
    result:     str
    next_decision: str 
    
    
class ExtractedFacts(BaseModel):
    
    demographies:  dict = {}
    admission_date:  str | None = None 
    discharge_date:  str | None = None 
    diagnoses:       list[str] = []
    allergies:       list[str] = []
    # medications:     list[str] = []
    admission_meds:  list[str] = []
    discharge_meds:  list[str] = []
    procedures:      list[str] = []
    labs:            list[str] = []
    follow_up:       list[str] = []
    discharge_condtion:   str | None = None 
    
class AgentState(BaseModel):
    
    patient_id:     str
    documents:      List[Document] = []
    extracted_facts:  ExtractedFacts = ExtractedFacts()
    conflicts:        List[Conflict] = []
    pending_results:   List[str]  = []
    trace:           List[TraceStep] = []
    completed:      bool = False 
    final_draft:      str = ""  
    
    
class Sections(BaseModel):
    
    diagnosis:          str = ""
    history:            str = ""
    past_history:       str = ""
    physical_exam:      str = ""
    investigations:     str =  ""
    hospital_course:    str = ""
    medications:        str = ""
    follow_up:          str = ""
    discharge_condition:str = ""
    miscellaneous:      str = ""