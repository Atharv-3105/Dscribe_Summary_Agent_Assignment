import re 
from logger import get_logger

logger = get_logger(__name__)

class MedicalReconcilerTool:
    
    def reconcile(self, admission_meds: list[str], discharge_meds: list[str]) -> dict:
        """  
            This function compares Admission Meds and Discharge Meds. Flags changes for REVIEW
        """
        
        logger.info("Starting medication reconciliation...")
        
        if not admission_meds and not discharge_meds:
            logger.warning("No medications found in either list. Skipping Reconciliation.")
            return {"added": [], "stopped": [], "unchanges":[], "flags": []}
        
        #Normalize the Meds for comparison(i.e convert to samecase)
        norm_adm = {self._normalize(m): m for m in admission_meds}
        norm_dis = {self._normalize(m): m for m in discharge_meds}
        
        added_meds = []
        stopped_meds = []
        unchanged_meds = []
        flags = []
        
        #Find the Added Meds(i.e present in Discharge List but not in Admission List)
        for key, med in norm_dis.items():
            if key not in norm_adm:
                added_meds.append(med)
                flags.append(f"[REVIEW REQUIRED] Added: {med} (No document reason)")
            else:
                unchanged_meds.append(med)
                
        #Find the Stopped Meds(i.e absent in Discharge List but present in Admission List)
        for key, med in norm_adm.items():
            if key not in norm_dis:
                stopped_meds.append(med)
                flags.append(f"[REVIEW REQUIRED] Stopped: {med} (No document reason)")
                
        result = {
            "added": added_meds,
            "stopped": stopped_meds,
            "unchanged": unchanged_meds,
            "flags": flags
        }
        
        logger.info(f"Reconciliation complete: {len(added_meds)} added, {len(stopped_meds)} stopped.")
        return result
    
    def _normalize(self, text: str) -> str:
        
        return re.sub(r'[^a-z0-9]', '', text.lower())