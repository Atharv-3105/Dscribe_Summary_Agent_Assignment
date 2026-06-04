import os 
from dotenv import load_dotenv
from logger import get_logger
from groq import Groq
from models.model import AgentState

load_dotenv()
logger = get_logger(__name__)

class SummaryGeneratorTool:
    def __init__(self):
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        
    def generate_summary(self, state:AgentState) -> str:
        
        logger.info("Calling Groq LLM for final summary generation...")
        
        facts = state.extracted_facts
        meds = state.reconciled_meds
        flags = state.safety_flags
        prompt = f"""
        You are a clinical AI assistant. Generate a structured Discharge Summary Draft based on the following extracted data.
        
        EXTRACTED FACTS:
        - Admission Date: {facts.admission_date or 'MISSING'}
        - Discharge Date: {facts.discharge_date or 'MISSING'}
        - Diagnoses: {facts.diagnoses}
        - Hospital Course: {state.raw_sections.hospital_course[:1000]}
        
        MEDICATION RECONCILIATION:
        - Admission Meds: {facts.admission_meds}
        - Discharge Meds: {facts.discharge_meds}
        - Changes: Added: {meds.get('added', [])}, Stopped: {meds.get('stopped', [])}
        
        SAFETY FLAGS & CONFLICTS (CRITICAL):
        {flags if flags else 'None'}
        
        STRICT RULES (CRITICAL):
        1. NEVER invent, guess, or hallucinate clinical facts. 
        2. If a section is missing from the facts, explicitly write: "[MISSING - REQUIRES CLINICIAN REVIEW]".
        3. Include a "Medication Reconciliation" section. If there are safety flags, list them explicitly.
        4. Format cleanly in Markdown.
        """
        
        try:
            
            completion = self.client.chat.completions.create(
                model = "llama-3.3-70b-versatile",
                messages= [
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                temperature=0.1,
                max_tokens = 3000
            )
            return completion.choices[0].message.content
        
        except Exception as e:
            logger.error(f"Groq API call failed: {e}")
            return f"[ERROR: LLM GENERATION FAILED - {str(e)}]"