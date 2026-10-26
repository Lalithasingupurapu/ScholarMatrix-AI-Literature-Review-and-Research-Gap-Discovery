# 📚 LitAutoResearch: Autonomous Literature Review & Citation Synthesis Engine

An AI-powered academic research assistant that automates the literature review process from paper discovery to comprehensive scholarly synthesis.

## 🖥️ Interface Preview

The interface brings paper discovery, citation visualization, literature comparison, research-gap analysis, and report generation together in one workspace.

![LitAutoResearch interface](assets/interface.png)

---

## 🎯 Project Capabilities & Specifications

### 1. User Inputs
* **Research Topic:** e.g., *Retrieval-Augmented Generation (RAG)*
* **Research Question:** e.g., *How can RAG reduce AI hallucinations?*
* **Publication Year Span:** e.g., *2021–2026*
* **Number of Papers:** e.g., *20*
* **Source Selection:** Live Online Search (arXiv & OpenAlex APIs) or Drag-and-Drop PDF Uploads (with hybrid mode support)

### 2. Generated Outputs
1. **Research Papers List:** Detailed paper cards with titles, authors, publication years, venues, citation counts, expandable abstract previews, and direct manuscript links.
2. **Citation Graph:** Force-directed network visualization (powered by Vis.js) mapping direct citations and semantic similarities between papers, clustered by research themes with an interactive Node Inspector Drawer.
3. **Literature-Review Matrix:** Interactive comparison table analyzing *Proposed Methodologies*, *Datasets & Benchmarks*, *Quantitative/Qualitative Results*, and *Identified Limitations & Bottlenecks*. Supports instant search, column sorting, and CSV/Markdown export.
4. **Research Gaps:** Categorized vulnerability cards (Priority: Critical, High, Medium) with empirical citations, extracted quotes, and actionable future research directions/hypotheses.
5. **Synthesized Literature Review Report:** Publication-grade systematic literature review formatted in academic markdown with a dynamic Table of Contents, comparative synthesis table, and full bibliography in IEEE/APA style with export to `.md` and `.bib`.

---

## 🧰 Tech Stack

| Area | Technologies |
|---|---|
| **Language** | Python 3.14 |
| **Backend & API** | FastAPI, Uvicorn |
| **Paper sources** | OpenAlex REST API, arXiv API |
| **PDF processing** | `pypdf` |
| **Citation graph & analysis** | NetworkX, scikit-learn (TF-IDF and cosine similarity) |
| **Frontend** | HTML5, CSS3, vanilla JavaScript |
| **Visualizations & rendering** | vis-network, Marked.js |
| **Typography** | Inter (Google Fonts) |

---

## 🚀 Quickstart Guide

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Launch the Application
```bash
python run.py
```
Or with uvicorn directly:
```bash
uvicorn backend.app:app --host 127.0.0.1 --port 8000 --reload
```

Then open your browser to **[http://127.0.0.1:8000](http://127.0.0.1:8000)**.

---

## 📁 Project Structure

```
FSI_Main_project/
├── backend/
│   ├── __init__.py
│   ├── app.py                     # FastAPI REST API endpoints & static routing
│   ├── config.py                  # Environment config & SSL context helpers
│   └── services/
│       ├── __init__.py
│       ├── paper_fetcher.py       # OpenAlex & arXiv fetchers with fallback corpus
│       ├── pdf_parser.py          # PyPDF parser for uploaded manuscripts
│       ├── citation_graph.py      # NetworkX citation & semantic similarity builder
│       ├── matrix_generator.py    # Methods, datasets, results & limitations extractor
│       ├── gap_analyzer.py        # Categorized research gap synthesizer with evidence
│       ├── report_generator.py    # Publication-grade systematic literature review compiler
│       └── export_service.py      # CSV matrix and BibTeX export generator
├── frontend/
│   ├── index.html                 # Modern responsive user interface
│   ├── css/
│   │   └── style.css              # Dark glassmorphic design system
│   └── js/
│       ├── app.js                 # App coordinator, preset management & pipeline caller
│       ├── graph.js               # Interactive Vis.js network graph & inspector drawer
│       ├── matrix.js              # Literature matrix table, filters, & sorting
│       ├── gaps.js                # Research gap evidence cards renderer
│       └── report.js              # Markdown report renderer with dynamic TOC
├── assets/
│   └── interface.png              # Application interface screenshot
├── uploads/                       # Temporary storage for uploaded PDF manuscripts
├── requirements.txt               # Python package dependencies
├── run.py                         # One-click startup runner
└── README.md                      # Documentation
```
