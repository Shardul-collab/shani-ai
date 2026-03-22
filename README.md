# 🔬 SHANI --- Scientific Harvesting and Analysis of Networked Information

SHANI is a **deterministic research workflow system** designed to
automatically generate structured literature reviews from scientific
papers.

It transforms raw research papers into: - structured scientific
knowledge - organized literature sections - a compiled review document

------------------------------------------------------------------------

## 🚀 Key Features

-   🔁 **End-to-End Automation**
    -   From query generation → paper retrieval → final review document
-   🧠 **Hybrid Knowledge Extraction**
    -   Rule-based NLP + LLM-assisted interpretation
-   🗂️ **Structured Scientific Database**
    -   Stores materials, methods, techniques, and applications
-   ⚙️ **Deterministic Workflow Engine**
    -   Fully controlled pipeline (no random agent behavior)
-   📄 **Automated Literature Review Generation**
    -   Outputs a structured `.docx` review paper

------------------------------------------------------------------------

## 🏗️ System Architecture

SHANI follows a layered architecture:

CLI Layer\
Workflow Layer (Orchestrator)\
Repository Layer (Database)\
Tool Layer (Processing Units)\
Service Layer (LLM + Utilities)

------------------------------------------------------------------------

## Workflow Pipeline

S1 → Generate Queries\
S2 → Search Papers\
S3 → Process Papers\
S4 → Extract Paper Content\
S5 → Extract Research Knowledge\
S6 → Draft Sections\
S7 → Synthesize Final Paper

Each stage is executed sequentially and deterministically.

------------------------------------------------------------------------

## 🧠 Core Concept

Knowledge Extraction ≠ Writing

Pipeline:

Papers → Structured Knowledge → Section Generation → Final Document

------------------------------------------------------------------------

## 📦 Project Structure

core/ → orchestrator, CLI\
tools/ → pipeline tools (S1--S7)\
repositories/ → database access layer\
services/ → LLM + utilities\
database/ → SQLite DB\
papers/ → downloaded PDFs\
results/ → generated outputs\
scripts/ → helpers & runners

------------------------------------------------------------------------

## ⚙️ Installation

### 1. Clone repository

git clone https://github.com/`<your-username>`{=html}/SHANI.git\
cd SHANI

### 2. Create environment

python -m venv venv\
source venv/bin/activate

### 3. Install dependencies

pip install -r requirements.txt

### 4. Initialize database

python scripts/init_db.py

------------------------------------------------------------------------

## ▶️ Usage

### Create workflow

python core/shani.py create "Your Research Topic"

### Start workflow

python core/shani.py start `<workflow_id>`{=html}

### Check status

python core/shani.py status `<workflow_id>`{=html}

------------------------------------------------------------------------

## 📊 Output

results/review_paper.docx

------------------------------------------------------------------------

## ⚠️ Current Limitations

-   LLM-based section generation may fail under large context sizes
    (timeout issues)\
-   Some sections may be incomplete in current version\
-   Writing quality depends on local LLM performance\
-   No parallel processing

------------------------------------------------------------------------

## 🔮 Future Improvements

-   Prompt compression\
-   Retry mechanisms\
-   Better synthesis\
-   Fine-tuned models

------------------------------------------------------------------------

## 👨‍🔬 Author

Shardul Khanduri

------------------------------------------------------------------------

## 📜 License

MIT License
