from datetime import datetime
from logger import get_logger
from models.model import ExtractedFacts, Conflict

logger = get_logger(__name__)

class ConflictDetectorTool:
    
    def check_conflict(self, facts: ExtractedFacts)-> list[Conflict]:
        
        logger.info("Starting Conflict Detection...")
        conflicts = []
        
        #Check conflict in Date
        if facts.admission_date and facts.discharge_date:
            try:
                adm_date = self._parse_date(facts.admission_date)
                dis_date = self._parse_date(facts.discharge_date)
                
                if adm_date and dis_date and  dis_date < adm_date:
                    conflicts.append(Conflict(
                        field_name="Dates",
                        value_a = f"Admission: {facts.admission_date}",
                        value_b = f"Discharge: {facts.discharge_date}",
                        source_a = "History Section",
                        source_b = "Discharge Condition Section"
                    ))
                    logger.warning("CONFLICT DETECTED: Discharge date is before Admission Date")
            except Exception:
                pass
            
        logger.info(f"Conflict detection complete. Found {len(conflicts)} conflicts")
        return conflicts
    
    def _parese_date(self, date_str: str) -> datetime | None:
        
        formats = ["%d%m%Y", "%d-%m-%Y", "%Y-%m-%d", "%m%d%Y"]
        for fmt in formats:
            try:
                return datetime.strptime(date_str.strip(),fmt)
            except ValueError:
                continue
            
        return None