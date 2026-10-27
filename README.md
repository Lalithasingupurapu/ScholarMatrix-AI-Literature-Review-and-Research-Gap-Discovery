# ScholarMatrix AI

ScholarMatrix AI creates a literature review from the papers selected for the current run. Choose live online search or upload PDFs, enter a topic and research question, and generate a paper list, comparative matrix, paper-by-paper research gaps, and a Markdown report.

## Interface

![ScholarMatrix AI interface](assets/interface.png)

## Features

- **Choose the source for each review:** search OpenAlex and arXiv, or upload research-paper PDFs.
- **Set review inputs:** research topic, research question, publication year range, and target paper count.
- **Review paper metadata and abstracts:** inspect titles, available authors, year, venue, citation count when provided by the source, abstract, and manuscript link.
- **Compare papers in a literature matrix:** extract each paper's research focus, methodology, named datasets and benchmarks, stated metrics and comparisons, results, limitations, and future work from its available text.
- **Analyze research gaps paper by paper:** each selected paper gets a separate entry. The app reports an explicit limitation/future-work statement when found, and says when available text does not support a reliable gap.
- **Generate a Markdown literature-review report:** the report and matrix are built from the papers selected for that generation.
- **Export results:** download the matrix as CSV or the report as Markdown; copy the matrix as Markdown from the matrix view.

The app avoids substituting shared example datasets, metrics, results, or research gaps when a paper does not report them. Missing facts are labeled as unavailable or not reported.

## Technology stack

| Area | Technologies |
|---|---|
| Backend language | Python |
| Web API and server | FastAPI, Uvicorn |
| Online paper sources | OpenAlex Works API and arXiv API |
| Online requests | Python standard-library `urllib` |
| PDF processing | `pypdf` |
| Frontend | HTML, CSS, vanilla JavaScript |
| Markdown rendering | Marked.js |
| Typography | Inter from Google Fonts |
| Upload handling | FastAPI multipart support via `python-multipart` |

Python dependencies are listed in [`requirements.txt`](requirements.txt).

## Requirements

- Python with `pip`
- Internet access for live online paper search and CDN-hosted frontend assets

## Run locally

From the project directory, create and activate a virtual environment in PowerShell, then install dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Start the app:

```powershell
python run.py
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000). The runner starts the local FastAPI server and attempts to open the browser.

Alternatively, run Uvicorn directly:

```powershell
python -m uvicorn backend.app:app --host 127.0.0.1 --port 8000 --reload
```

## Using the application

1. Select **Live Online Search** or **Upload PDF Files**.
2. Enter a research topic and question, and set the year range and paper count.
3. For PDF mode, upload or select the PDFs to include.
4. Click **Generate Literature Review**. The generated outputs use the papers selected for that run.
5. Browse the papers, matrix, paper-specific gaps, and report. Use the CSV and Markdown export options as needed.

## Evidence and extraction notes

- Online search results use the metadata and abstract returned by OpenAlex or arXiv. Full text may not be available for online results; in that case, analysis is limited to the available abstract and the UI indicates the evidence scope.
- For uploaded PDFs, text is extracted from up to the first 100 pages. The quality of extracted information depends on whether the PDF contains machine-readable text; scanned pages may require OCR, which is not currently included.
- Dataset names, metrics, baselines, results, limitations, and future-work statements are included only when found in the available paper text. The application does not claim that an unreported item was evaluated.
- An online search that returns no papers reports an error instead of inserting a synthetic sample corpus.
- Citation counts may be unavailable from a source. An unavailable count should not be interpreted as zero citations.

## API endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/api/health` | Check service health |
| `GET` | `/api/uploaded-pdfs` | List and parse PDFs already in the uploads directory |
| `POST` | `/api/upload-pdfs` | Upload and parse PDF files |
| `POST` | `/api/generate-full-review` | Generate outputs from online search or selected PDFs |
| `GET` | `/api/export/csv` | Download the latest literature matrix as CSV |
| `GET` | `/api/export/markdown` | Download the latest report as Markdown |

## Project structure

```text
FSI_Main_project/
├── assets/
│   └── interface.png
├── backend/
│   ├── app.py
│   ├── config.py
│   └── services/
│       ├── citation_graph.py
│       ├── export_service.py
│       ├── gap_analyzer.py
│       ├── matrix_generator.py
│       ├── paper_fetcher.py
│       ├── pdf_parser.py
│       └── report_generator.py
├── frontend/
│   ├── index.html
│   ├── css/
│   │   └── style.css
│   └── js/
│       ├── app.js
│       ├── gaps.js
│       ├── graph.js
│       ├── matrix.js
│       └── report.js
├── uploads/                 # Uploaded PDF storage
├── requirements.txt
├── run.py
└── README.md
```
