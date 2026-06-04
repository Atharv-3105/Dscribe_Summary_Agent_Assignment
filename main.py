from logger import get_logger
from pathlib import Path 
from agent.core_agent import CoreAgent
logger = get_logger(__name__)

def main():
    
    logger.info("Dscribe Summary Agent Initialized")
    
    #Initialize the Agent 
    agent = CoreAgent(max_iterations=15)
    
    #Define the patient data
    patient_id = "patient_3"
    pdf_path = [Path("data/patient_3.pdf")]
    
    #Run the Agent Loop
    final_state = agent.run(patient_id=patient_id, pdf_paths=pdf_path)
    
    #Print Trace
    logger.info("\n======Agent Trace=======")
    for step in final_state.trace:
        print(f"[Step {step.step}] REASON: {step.reasoning}")
        print(f"    -> Action: {step.action}")
        print(f"    -> Result: {step.result}")
        print(f"    -> Next: {step.next_decision}\n")
    
    logger.info("\n===========STRUCTURED FACTS==========")
    facts = final_state.extracted_facts
    print(f"Admission Date: {facts.admission_date}")
    print(f"Discharge Date: {facts.discharge_date}")
    print(f"Diagnoses: {facts.diagnoses}")
    print(f"Medications: {facts.admission_meds}")
    
        
    # #Print Safety flags
    # if final_state.pending_results:
    #     logger.warning(f"\n====== SAFETY FLAGS======")
    #     logger.warning(f"Sections requiring clinician review: {final_state.pending_results}")
    # else:
    #     logger.info("\n=========No safety flags. All sections valid========")
    
    logger.info("==========FINAL REPORT=========")
    print(final_state.final_draft[:1500])
    logger.info(f"\nFull draft saved to outputs/{patient_id}_summary.md")
    
    
if __name__ == "__main__":
    
    main()
    
    