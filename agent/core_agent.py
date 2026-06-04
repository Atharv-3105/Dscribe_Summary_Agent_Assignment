from pathlib import Path 
from typing import List
from logger import get_logger
from models.model import AgentState, TraceStep, Document
from tools.pdf_reader import PDFReaderTool
from tools.section_extractor import SectionExtractorTool
from tools.fact_extractor import FactExtractorTool
from tools.medication_reconciler import MedicalReconcilerTool
from tools.conflict_detector import ConflictDetectorTool
from tools.summary_generator import SummaryGeneratorTool
logger = get_logger(__name__)

class CoreAgent:
    def __init__(self, max_iterations: int = 10):
        self.pdf_reader = PDFReaderTool()
        self.section_extractor = SectionExtractorTool()
        self.med_reconciler = MedicalReconcilerTool()
        self.fact_extractor = FactExtractorTool()
        self.conflict_detector = ConflictDetectorTool()
        self.summary_generator = SummaryGeneratorTool()
        self.max_iterations = max_iterations
        self.current_step = 0
        
    def run(self, patient_id: str, pdf_paths: List[Path]) -> AgentState:
        logger.info(f"------Starting Agent For Patient: {patient_id}----------")
        state = AgentState(patient_id=patient_id)
        
        #Re-ACT LOOP 
        while not state.completed and self.current_step < self.max_iterations:
            self.current_step += 1
            
            #REASON: Decide what next action to take based on current State
            action = self._reason_next_action(state)
            
            #ACT:   Execute the tool needed
            result = self._execute_action(action, state, pdf_paths)
            
            #OBSERVER: Log the trace
            state.trace.append(TraceStep(
                step = self.current_step,
                reasoning = action["reasoning"],
                action = action["tool"],
                result = result["message"],
                next_decision= action["next"]
            ))
            
            if action["tool"] ==  "COMPLETED":
                state.completed = True 
                
        if not state.completed:
            logger.warning("Max iteration reached. Forcing Completion")
            state.completed = True 
            
        return state
    
    def _reason_next_action(self, state: AgentState) -> dict:
        
        if not state.documents:
            return {"reasoning": "No documents loaded. Need to ingest raw PDFs.", "tool": "INGEST_PDF", "next": "Extract sections."}
        elif state.raw_sections is None:
            return {"reasoning": "Documents loaded. Need to extract raw text sections.", "tool": "EXTRACT_SECTIONS", "next": "Parse structured facts."}
        elif state.extracted_facts is None:
            return {"reasoning": "Raw sections extracted. Need to parse structured clinical facts (dates, meds).", "tool": "EXTRACT_FACTS", "next": "Reconcile medications."}
        elif state.reconciled_meds is None:
            return {"reasoning": "Facts extracted. Need to compare admission vs discharge meds for safety.", "tool": "RECONCILE_MEDS", "next": "Detect conflicts."}
        elif not state.conflicts_checked: 
            return {"reasoning": "Meds reconciled. Need to check for logical conflicts (e.g. dates).", "tool": "DETECT_CONFLICTS", "next": "Generate LLM summary."}
        elif not state.summary_generated:
            return {"reasoning": "All safety checks done. Calling Groq LLM to generate final clinical draft.", "tool": "GENERATE_SUMMARY", "next": "Agent run complete."}
        else:
            return {"reasoning": "All tasks complete. Draft generated.", "tool": "COMPLETED", "next": "Terminate."}
    
    def _execute_action(self, action: dict, state: AgentState, pdf_paths: List[Path]) -> dict:
        tool_name = action['tool']
        
        try:
            if tool_name == "INGEST_PDF":
                doc = self.pdf_reader.read_pdf(pdf_paths[0])
                state.documents.append(doc)
                return {"message": f"Loaded {len(doc.pages)} pages."}
                
            elif tool_name == "EXTRACT_SECTIONS":
                sections = self.section_extractor.extract_sections(state.documents[0].text)
                state.raw_sections = sections
                return {"message": f"Extracted raw sections."}
                
            elif tool_name == "EXTRACT_FACTS":
                facts = self.fact_extractor.extract_facts(state.raw_sections)
                state.extracted_facts = facts
                return {"message": f"Parsed facts: {len(facts.diagnoses)} diagnoses, {len(facts.admission_meds)} adm meds."}
                
            elif tool_name == "RECONCILE_MEDS":
                facts = state.extracted_facts
                med_result = self.med_reconciler.reconcile(facts.admission_meds, facts.discharge_meds)
                state.reconciled_meds = med_result
                # Add flags to safety list
                state.safety_flags.extend(med_result.get("flags", []))
                return {"message": f"Reconciled meds. Flags: {len(med_result.get('flags', []))}"}
                
            elif tool_name == "DETECT_CONFLICTS":
                conflicts = self.conflict_detector.check_conflict(state.extracted_facts)
                state.conflicts.extend(conflicts)
                state.conflicts_checked = True
                return {"message": f"Checked conflicts. Found: {len(conflicts)}"}
                
            elif tool_name == "GENERATE_SUMMARY":
                # Pass all structured data + safety flags to LLM
                draft = self.summary_generator.generate_summary(state)
                state.final_draft = draft
                state.summary_generated = True
                Path("outputs").mkdir(exist_ok=True)
                with open(f"outputs/{state.patient_id}_summary.md", "w") as f:
                    f.write(draft)
                return {"message": "LLM Summary generated and saved."}
            
        except Exception as e:
            logger.error(f"Tool  {tool_name} failed : {e}")
            return {"message": f"ERROR in {tool_name} : {str(e)}"}
        
        return {"message": "Unknown Tool"}