# Dscribe: Agentic AI for Clinical Discharge Summaries

Dscribe is a privacy-preserving, clinically safe agentic AI system designed to read messy, incomplete, and scanned patient PDFs and produce a structured discharge summary draft for clinician review. 

Built for the Unriddle Technologies AI Agent Assignment, Dscribe prioritizes **clinical safety (zero fabrication)** over raw AI generation, utilizing a dynamic ReAct agent loop, deterministic rule-based tools, and targeted LLM summarization.



---

## 🏗️ Agent Loop Design

Unlike a hardcoded sequential pipeline, Dscribe uses a **State-Driven ReAct (Reasoning + Acting) Loop**. 

1. **Reasoning:** At every step, the `CoreAgent` evaluates explicit `AgentFlags` (e.g., `ingestion_complete`, `meds_reconciled`) and the current data state to dynamically decide the next action.
2. **Conditional Execution:** The agent optimizes compute by skipping unnecessary steps. For example, if no medications are found in the extracted facts, it triggers a `SKIP_MED_RECONCILIATION` action instead of calling an empty tool.
3. **Observability:** Every cycle emits a structured `TraceStep` logging the `Reasoning -> Action -> Result -> Next Decision`, providing full transparency into the agent's cognitive process.
4. **Control:** A hard `max_iterations` cap prevents infinite looping, ensuring the agent always terminates gracefully.

### Why this architecture?
Medical data requires a hybrid approach. We use **deterministic Python tools** (Regex, Set operations) for fact extraction, date parsing, and medication reconciliation to mathematically guarantee no hallucinations. We reserve the **LLM (Groq)** strictly for the final narrative summarization, passing only targeted, extracted chunks to ensure 100% data privacy and minimal API costs.

---

## ️ The "No-Fabrication" Guardrail

The core mandate of this system is: **Never invent or guess a clinical fact.** Dscribe enforces this through multiple layers:

1. **Deterministic Text Validation:** Before any data reaches the LLM, the `TextValidator` checks for OCR garbage (e.g., high special-character ratios, low vowel ratios). If a section like "Diagnosis" is unreadable, it is immediately flagged as `[UNREADABLE - OCR FAILED - REQUIRES CLINICIAN REVIEW]`.
2. **Explicit Missing Data Handling:** If a required section (e.g., Demographics, Allergies) is missing from the source documents, the agent explicitly injects `[MISSING - REQUIRES CLINICIAN REVIEW]` into the final draft. It never attempts to infer missing facts from the hospital course.
3. **Strict LLM Prompting:** The Groq LLM is instructed with a zero-tolerance hallucination prompt. It is only allowed to summarize the exact structured facts provided to it.

---

## ️ Handling Failures, Conflicts, and Messy Data

### Robust Failure Handling (Recovery Path)
Medical PDFs are notoriously messy, and external APIs can fail. The `_execute_action_with_recovery` method wraps every tool call in a `try/except` block. If a tool fails (e.g., a Groq API timeout):
* The agent catches the exception.
* It logs a `[SYSTEM ERROR]` flag for the clinician.
* It forces the completion flag to `True` and falls back to the next step, ensuring the agent **never crashes** and always produces a partial, safe draft.

### Medication Reconciliation & Conflict Detection
* **Med Reconciler:** Compares admission and discharge medication lists. If a medication was added or stopped without a documented reason in the notes, it is explicitly flagged: `[REVIEW REQUIRED] Stopped: [Med Name] (No documented reason)`.
* **Conflict Detector:** Cross-references extracted facts (e.g., ensuring the Discharge Date is not chronologically before the Admission Date) and flags logical inconsistencies.

---

## 📂 Project Structure

```text
dscribe_agent/
├── agent/
│   └── core_agent.py           # Dynamic ReAct Agent Loop
├── tools/
│   ├── pdf_reader.py           # PyMuPDF + Tesseract OCR Ingestion
│   ├── section_extractor.py    # Regex-based document chunking
│   ├── fact_extractor.py       # Deterministic fact parsing
│   ├── medication_reconciler.py # Med list comparison & flagging
│   ├── conflict_detector.py    # Logical inconsistency checks
│   └── summary_generator.py        # Privacy-safe Groq LLM summarization
├── models/
│   └── model.py                # Pydantic models (State, Flags, Facts)
├── utils/
│   └── text_validator.py       # OCR garbage detection guardrails
├── outputs/                    # Generated Markdown drafts
├── data/                       # Input patient PDFs
├── main.py                     # Entry point
└── requirements.txt
```
---
## [Video Demo](https://www.loom.com/share/9eb9009c893b4ed0b56a1abc0627f9b1)
  

---

## ⚙️ Setup and Execution

### Prerequisites
* Python 3.10+
* Tesseract OCR installed on your system and added to your system's PATH.

### Installation

1. Clone the repository and navigate to the project directory:
```bash
git clone <your-repo-url>
cd dscribe_agent
```
2. Install the required Python dependencies:
```
  pip install -r requirements.txt
```
3. Set your Groq API Key as an environment variable:

### Running the Agent 
```
  python main.py
```
