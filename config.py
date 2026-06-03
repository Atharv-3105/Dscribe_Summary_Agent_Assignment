from pathlib import Path 
from dotenv import load_dotenv
import os

load_dotenv()
ROOT_DIR = Path(__file__).parent 

OUTPUT_DIR = ROOT_DIR / "outputs"

SUMMARY_DIR = OUTPUT_DIR / "summaries"

TRACE_DIR = OUTPUT_DIR / "traces"

GROQ_API_KEY= os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL")