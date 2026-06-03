from pathlib import Path 
from typing import List 
from logger import get_logger
from models.model import AgentState, TraceStep, Document, ExtractedFacts, Sections
from tools.pdf_reader import PDFReaderTool
from tools.section_extractor import SectionExtractorTool
from tools.fact_extractor import FactExtractorTool
from tools.medication_reconciler import MedicalReconcilerTool
from tools.conflict_detector import ConflictDetectorTool
from utils.text_validator import validate_extraction

logger = get_logger(__name__)

class CoreAgent:
    
    def __init__(self, max_iterations: int = 20):
        self.pdf_reader = PDFReaderTool()
        self.section_extractor = SectionExtractorTool()
        self.fact_extractor = FactExtractorTool()
        self.med_reconciler = MedicalReconcilerTool()
        self.conflict_detector = ConflictDetectorTool()
        self.max_iterations = max_iterations
        
        #Required Sections for Final Discharge Summary
        self.required_sections = ["diagnosis", "history", "past_history","physical_exam","investigations",
                                  "hospital_course", "medications", "follow_up", "discharge_condition"]
        
        
    def run(self, patient_id: str, pdf_path: List[Path])-> AgentState:
        
        logger.info(f"----Starting Agent Run for Patiend:{patient_id}-----")
        state = AgentState(patient_id=patient_id)
        
        #Phase-1 : INGESTION
        state = self._phase_ingest(state, pdf_path)
        
        #Phase-2 : EXTRACTION & VALIDATION LOOP
        state, raw_sections = self._phase_extract(state)
        
        #Phase-3:  STRUCTURED FACT EXTRACTION
        state = self._phase_build_facts(state, raw_sections)
        
        #Phase-4:  MED RECONCILIATION & CONFLICT DETECTION
        state = self._phase_safety_checks(state)
        
        state.completed = True
        logger.info(f"-----Agent Run completed for patient: {patient_id}------")
        return state
    
    def _phase_ingest(self, state: AgentState, pdf_path: List[Path])-> AgentState:
        
        logger.info("Phase 1: Document Ingestion")
        step = 1
        
        for path in pdf_path:
            if step > self.max_iterations:
                state.trace.append(TraceStep(
                    step=step, reasoning="Max iterations reached during ingestion",
                    action="STOP", result="Aborted Ingestion", next_decision="Terminate"
                ))
                break
            
            try:
                #ACTION: Call PDF READER TOOL
                doc: Document = self.pdf_reader.read_pdf(path)
                state.documents.append(doc)
                
                #OBSERVE:  Record success in Trace
                state.trace.append(TraceStep(
                    step = step,
                    reasoning = f"Need to read source document {path.name}",
                    action = f"PDFReaderTool.read_pdf({path.name})",
                    result = f"Successfully loaded {len(doc.pages)} pages.",
                    next_decision= "Proceed to next document or extraction phase"
                ))
                
            except Exception as e:
                state.trace.append(TraceStep(
                    step = step,
                    reasoning= f"Failed to read {path.name}",
                    action= f"PDFReaderTool.read_pdf({path.name})",
                    result = f"Error: {str(e)}",
                    next_decision= "Skip document and continue"
                ))
                step += 1
                
        return state
    
    def _phase_extract(self, state:AgentState) -> tuple[AgentState, Sections]:
        logger.info("Phase 2: Section Extraction & Validation")
        
        #Combine all of the document text for the section extractor
        combined_text  = "\n\n".join([doc.text for doc in state.documents])
        
        if not combined_text.strip():
            logger.warning("No text extracted from documents. Skipping section extraction.")
            return state, Sections()
        
        #ACTION: Extract all sections at once using SectionExtractorTool
        sections = self.section_extractor.extract_sections(combined_text)
        
        step = len(state.trace) + 1
        
        for section_name in self.required_sections:
            if step > self.max_iterations:
                logger.warning("Max iteration reached. Terminating extraction loop")
                break 
            
            raw_text = getattr(sections, section_name, "")
            
            #Validate the Text
            validation = validate_extraction(raw_text, section_name)
            
            if validation["is_valid"]:
                # state.extracted_facts[section_name] = validation["cleaned_text"]
                result_msg = f"Extracted {len(validation['cleaned_text'])} chars. Is valid"
            else:
                # state.extracted_facts[section_name] = validation['flag']
                state.pending_results.append(section_name)
                result_msg = f"Flagged as missing/garbage. Do not fabricate"
                
            #OBSERVABILITY
            state.trace.append(TraceStep(
                step = step,
                reasoning=f"Need to extract and validate '{section_name}' for the summary.",
                action= f"SectionExtractorTool & TextValidator on '{section_name}'",
                result = result_msg,
                next_decision= "Move to next required section"
            ))
            
            step += 1
            
        return state, sections
    
    def _phase_build_facts(self, state: AgentState, raw_sections: Sections) -> AgentState:
        
        logger.info("Phase 3: Structured Fact Extraction")
        step = len(state.trace) + 1
        
        if step > self.max_iterations:
            return state
        
        extracted_facts = self.fact_extractor.extract_facts(raw_sections)
        
        state.extracted_facts = extracted_facts
        
        state.trace.append(TraceStep(
            step = step,
            reasoning = "Raw sections extracted. Need to parse them into structured clinical facts.",
            action = "FactExtractorTool.extract_facts()",
            result = f"Extracted {len(extracted_facts.admission_meds)} meds, {len(extracted_facts.diagnoses)} diagnoses.",
            next_decision="Proceed to output generation or conflict detection."
        ))
        
        return state
        
        
    def _phase_safety_checks(self, state: AgentState) -> AgentState:
        
        logger.info("Phase 4: Safety Checks")
        step = len(state.trace) + 1
        
        if step > self.max_iterations:
            return state 
        
        facts = state.extracted_facts
        
        #MEDICATION RECONCILIATION
        med_result = self.med_reconciler.reconcile(facts.admission_meds, facts.discharge_meds)
        
        #If flags are present then add them to pending results
        if med_result["flags"]:
            for flag in med_result["flags"]:
                state.pending_results.append(flag)
                
        #OBSERVABILITY
        state.trace.append(TraceStep(
            step = step,
            reasoning = "Need to compare admission and discharge medications for safety.",
            action = "MedicationReconcilerTool.reconcile()",
            result = f"Added: {len(med_result['added'])}, Stopped: {len(med_result['stopped'])}. Flags: {len(med_result['flags'])}",
            next_decision="Proceed to conflict detection"
        ))
        step += 1
        
        #CONFLICT DETECTION
        conflicts = self.conflict_detector.check_conflict(facts)
        state.conflicts.extend(conflicts)
        
        state.trace.append(TraceStep(
            step = step,
            reasoning = "Need to check for logical inconsistencies in extracted facts.",
            action= "ConflictDetection.check_conflicts()",
            result = f"Found {len(conflicts)} conflicts.",
            next_decision= "Proceed to output generation"
        ))
        
        return state 