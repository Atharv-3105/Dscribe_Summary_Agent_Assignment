import os 
from dotenv import load_dotenv
from logger import get_logger
from groq import Groq

load_dotenv()
logger = get_logger(__name__)

class SummaryGeneratorTool:
    def __init__(self):
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        
    def generate_summary(self, facts:dict) -> str:
        
        logger.info("Calling Groq LLM for final summary generation...")
        
        prompt = f"""
        You are a clinical AI assistant. Generate a structured Discharge Summary Draft based on the following extracted facts.
        
        EXTRACTED FACTS:
        {facts}
        
        STRICT RULES (CRITICAL):
        1. NEVER invent, guess, or hallucinate clinical facts. 
        2. If a section (like Demographics, Allergies, or Procedures) is missing from the facts, explicitly write: "[MISSING - REQUIRES CLINICIAN REVIEW]".
        3. Format the output cleanly in Markdown with clear headings.
        4. Include a "Medication Reconciliation" section noting any changes.
        5. End with a disclaimer that this is an AI draft for clinician review.        
        """
        
        try:
            
            completion = self.client.chat.completions.create(
                model = "llama3-8b-8192",
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