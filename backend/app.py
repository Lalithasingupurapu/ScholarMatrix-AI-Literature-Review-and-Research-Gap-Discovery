import os
import re
import shutil
from pathlib import Path
from typing import List, Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel

from backend.config import UPLOAD_DIR
from backend.services.paper_fetcher import PaperFetcher
from backend.services.pdf_parser import PDFParser
from backend.services.citation_graph import CitationGraphBuilder
from backend.services.matrix_generator import LiteratureMatrixGenerator
from backend.services.gap_analyzer import ResearchGapAnalyzer
from backend.services.report_generator import ResearchReportGenerator
from backend.services.export_service import ExportService

app = FastAPI(
    title="LitAutoResearch API",
    description="Autonomous Literature Review & Research Assistant Engine",
    version="1.0.0"
)

# Enable CORS for local testing & web clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Services
paper_fetcher = PaperFetcher()
pdf_parser = PDFParser()
graph_builder = CitationGraphBuilder()
matrix_generator = LiteratureMatrixGenerator()
gap_analyzer = ResearchGapAnalyzer()
report_generator = ResearchReportGenerator()

# In-memory session cache for latest generated review
latest_review_cache = {
    "topic": "Retrieval-Augmented Generation (RAG)",
    "research_question": "How can RAG reduce AI hallucinations?",
    "papers": [],
    "graph": {},
    "matrix": [],
    "gaps": [],
    "report": {}
}


class FullReviewRequest(BaseModel):
    topic: str = "Retrieval-Augmented Generation (RAG)"
    research_question: str = "How can RAG reduce AI hallucinations?"
    start_year: int = 2021
    end_year: int = 2026
    num_papers: int = 20
    mode: str = "online"  # 'online' or 'pdf'
    uploaded_papers: Optional[List[dict]] = None


@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "service": "LitAutoResearch",
        "version": "1.0.0",
        "ready": True
    }


@app.get("/api/uploaded-pdfs")
def get_uploaded_pdfs():
    """
    Returns list of already uploaded and parsed PDF papers.
    """
    pdf_files = sorted(list(UPLOAD_DIR.glob("*.pdf")), key=os.path.getmtime, reverse=True)
    parsed_papers = []
    seen_titles = set()

    for p_file in pdf_files:
        try:
            parsed = pdf_parser.parse_pdf(str(p_file), p_file.name)
            norm_title = re.sub(r'[^a-z0-9]', '', parsed.get("title", "").lower())
            if norm_title and norm_title not in seen_titles:
                seen_titles.add(norm_title)
                parsed_papers.append(parsed)
        except Exception as e:
            print(f"[Warning] Failed to read {p_file.name}: {e}")

    return {
        "uploaded_count": len(parsed_papers),
        "papers": parsed_papers
    }


@app.post("/api/upload-pdfs")
async def upload_pdfs(files: List[UploadFile] = File(...)):
    """
    Upload and parse one or more research paper PDF documents.
    """
    parsed_papers = []

    for file in files:
        if not file.filename.lower().endswith(".pdf"):
            continue

        clean_filename = f"{Path(file.filename).stem[:30]}_{os.urandom(4).hex()}.pdf"
        target_path = UPLOAD_DIR / clean_filename

        try:
            with open(target_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            parsed = pdf_parser.parse_pdf(str(target_path), file.filename)
            parsed_papers.append(parsed)
        except Exception as e:
            print(f"[Error] Failed to parse {file.filename}: {e}")

    if not parsed_papers:
        raise HTTPException(status_code=400, detail="No valid PDF documents could be processed.")

    return {
        "uploaded_count": len(parsed_papers),
        "papers": parsed_papers
    }


@app.post("/api/generate-full-review")
def generate_full_review(req: FullReviewRequest):
    """
    Unified end-to-end autonomous research workflow:
    1. Fetches/extracts papers (Online Search OR Uploaded PDFs)
    2. Builds interactive citation & conceptual graph
    3. Generates comparative literature matrix
    4. Synthesizes evidenced research gaps
    5. Compiles comprehensive academic literature review report
    """
    topic = req.topic.strip()
    question = req.research_question.strip()
    start_year = max(2010, req.start_year)
    end_year = min(2030, req.end_year)
    num_papers = max(5, min(req.num_papers, 50))

    papers = []

    # Step 1: Paper acquisition based on mode
    if req.mode == "pdf":
        if req.uploaded_papers and len(req.uploaded_papers) > 0:
            papers.extend(req.uploaded_papers)
        else:
            # Load from uploads folder
            pdf_files = sorted(list(UPLOAD_DIR.glob("*.pdf")), key=os.path.getmtime, reverse=True)
            seen_titles = set()
            for p_file in pdf_files[:num_papers]:
                try:
                    parsed = pdf_parser.parse_pdf(str(p_file), p_file.name)
                    norm_t = re.sub(r'[^a-z0-9]', '', parsed.get("title", "").lower())
                    if norm_t and norm_t not in seen_titles:
                        seen_titles.add(norm_t)
                        papers.append(parsed)
                except Exception as e:
                    print(f"[Warning] PDF parse error during review: {e}")

        if not papers:
            raise HTTPException(
                status_code=400,
                detail="No uploaded PDF files found. Please drop your PDF manuscripts into the upload zone first."
            )
    else:
        # Online mode (arXiv & OpenAlex)
        fetched = paper_fetcher.fetch_papers(
            topic=topic,
            research_question=question,
            start_year=start_year,
            end_year=end_year,
            max_papers=num_papers
        )
        papers.extend(fetched)
        if not papers:
            papers = paper_fetcher.fetch_papers(topic, question, start_year, end_year, num_papers)

    # Ensure paper count matches target and sequential IDs
    papers = papers[:num_papers]
    for idx, p in enumerate(papers):
        p["id"] = f"paper_{idx + 1}"

    # Step 2: Build Citation Graph
    graph_data = graph_builder.build_graph(papers)

    # Step 3: Generate Literature-Review Matrix
    matrix_data = matrix_generator.generate_matrix(papers, question)

    # Step 4: Synthesize Research Gaps
    gaps_data = gap_analyzer.analyze_gaps(papers, topic, question)

    # Step 5: Compile Academic Literature Review Report
    report_data = report_generator.generate_report(
        topic=topic,
        research_question=question,
        papers=papers,
        matrix=matrix_data,
        gaps=gaps_data,
        start_year=start_year,
        end_year=end_year
    )

    # Cache for direct exports
    latest_review_cache["topic"] = topic
    latest_review_cache["research_question"] = question
    latest_review_cache["papers"] = papers
    latest_review_cache["graph"] = graph_data
    latest_review_cache["matrix"] = matrix_data
    latest_review_cache["gaps"] = gaps_data
    latest_review_cache["report"] = report_data

    return {
        "meta": {
            "topic": topic,
            "research_question": question,
            "publication_year_span": f"{start_year}–{end_year}",
            "papers_analyzed": len(papers),
            "mode": req.mode
        },
        "papers_list": papers,
        "citation_graph": graph_data,
        "literature_matrix": matrix_data,
        "research_gaps": gaps_data,
        "research_report": report_data
    }


@app.get("/api/export/csv")
def export_csv():
    matrix = latest_review_cache.get("matrix", [])
    if not matrix:
        raise HTTPException(status_code=400, detail="No literature matrix generated yet.")
    csv_str = ExportService.export_matrix_csv(matrix)
    return Response(
        content=csv_str,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=literature_review_matrix.csv"}
    )


@app.get("/api/export/bibtex")
def export_bibtex():
    papers = latest_review_cache.get("papers", [])
    if not papers:
        raise HTTPException(status_code=400, detail="No papers generated yet.")
    bib_str = ExportService.export_bibtex(papers)
    return Response(
        content=bib_str,
        media_type="application/x-bibtex",
        headers={"Content-Disposition": "attachment; filename=literature_citations.bib"}
    )


@app.get("/api/export/markdown")
def export_markdown():
    report = latest_review_cache.get("report", {})
    md_content = report.get("markdown", "")
    if not md_content:
        raise HTTPException(status_code=400, detail="No report generated yet.")
    return Response(
        content=md_content,
        media_type="text/markdown",
        headers={"Content-Disposition": "attachment; filename=literature_review_report.md"}
    )


# Serve frontend static assets
frontend_dir = Path(__file__).resolve().parent.parent / "frontend"
if frontend_dir.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_dir)), name="static")

    @app.get("/")
    def serve_index():
        index_file = frontend_dir / "index.html"
        if index_file.exists():
            return FileResponse(str(index_file))
        return HTMLResponse("<h1>LitAutoResearch Frontend Loading...</h1>")
