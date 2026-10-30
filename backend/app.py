import os
import re
import shutil
from collections import Counter
from pathlib import Path
from typing import List, Optional
from urllib.parse import unquote, urlparse
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel

from backend.config import UPLOAD_DIR
from backend.services.paper_fetcher import PaperFetcher
from backend.services.pdf_parser import PDFParser
from backend.services.matrix_generator import LiteratureMatrixGenerator
from backend.services.gap_analyzer import ResearchGapAnalyzer
from backend.services.report_generator import ResearchReportGenerator
from backend.services.export_service import ExportService

app = FastAPI(
    title="ScholarMatrix AI API",
    description="Autonomous Literature Review & Research Gap Discovery Engine",
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
matrix_generator = LiteratureMatrixGenerator()
gap_analyzer = ResearchGapAnalyzer()
report_generator = ResearchReportGenerator()

DEFAULT_TOPIC = "Retrieval-Augmented Generation (RAG)"
DEFAULT_RESEARCH_QUESTION = "How can RAG reduce AI hallucinations?"

# In-memory session cache for latest generated review
latest_review_cache = {
    "topic": "Retrieval-Augmented Generation (RAG)",
    "research_question": "How can RAG reduce AI hallucinations?",
    "papers": [],
    "matrix": [],
    "gaps": [],
    "report": {}
}


def _infer_pdf_topic(papers: List[dict]) -> str:
    titles = [paper.get("title", "").strip() for paper in papers if paper.get("title", "").strip()]
    if not titles:
        return "Uploaded research papers"
    if len(titles) == 1:
        return titles[0]

    stop_words = {
        "about", "across", "an", "and", "are", "as", "at", "based", "by", "for",
        "from", "in", "into", "is", "of", "on", "or", "the", "their", "through",
        "to", "toward", "using", "via", "with",
    }
    words_by_title = [
        [
            word for word in re.findall(r"[A-Za-z][A-Za-z0-9-]*", title)
            if word.casefold() not in stop_words and len(word) > 2
        ]
        for title in titles
    ]
    title_counts = Counter(
        word.casefold()
        for words in words_by_title
        for word in set(words)
    )
    shared_words = {
        word for word, count in title_counts.items()
        if count > 1
    }
    if shared_words:
        topic_words = [
            word for word in words_by_title[0]
            if word.casefold() in shared_words
        ]
        if topic_words:
            return " ".join(dict.fromkeys(topic_words))
    return titles[0]


def _public_paper(paper: dict) -> dict:
    return {key: value for key, value in paper.items() if key != "extracted_text"}


def _parse_selected_upload(paper: dict) -> Optional[dict]:
    upload_url = paper.get("pdf_url") or paper.get("url") or ""
    parsed_url = urlparse(upload_url)
    prefix = "/api/uploads/"
    if not parsed_url.path.startswith(prefix):
        return None

    filename = unquote(parsed_url.path[len(prefix):])
    target_path = (UPLOAD_DIR / filename).resolve()
    if (
        not filename
        or Path(filename).name != filename
        or target_path.parent != UPLOAD_DIR.resolve()
        or target_path.suffix.lower() != ".pdf"
        or not target_path.is_file()
    ):
        raise HTTPException(status_code=404, detail="Uploaded PDF not found.")
    return pdf_parser.parse_pdf(str(target_path), target_path.name)


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
        "service": "ScholarMatrix AI",
        "version": "1.0.0",
        "ready": True
    }


@app.get("/api/uploads/{filename}")
def get_uploaded_pdf(filename: str):
    pdf_path = (UPLOAD_DIR / filename).resolve()
    if pdf_path.parent != UPLOAD_DIR.resolve() or pdf_path.suffix.lower() != ".pdf":
        raise HTTPException(status_code=404, detail="Uploaded PDF not found.")
    if not pdf_path.is_file():
        raise HTTPException(status_code=404, detail="Uploaded PDF not found.")
    return FileResponse(
        str(pdf_path),
        media_type="application/pdf",
        filename=pdf_path.name,
        content_disposition_type="inline"
    )


@app.get("/api/uploaded-pdfs")
def get_uploaded_pdfs():
    """
    Returns list of already uploaded and parsed PDF papers.
    """
    UPLOAD_DIR.mkdir(exist_ok=True, parents=True)
    pdf_files = sorted(list(UPLOAD_DIR.glob("*.pdf")), key=os.path.getmtime, reverse=True)
    parsed_papers = []
    seen_titles = set()

    for p_file in pdf_files:
        try:
            parsed = pdf_parser.parse_pdf(str(p_file), p_file.name)
            norm_title = re.sub(r'[^a-z0-9]', '', parsed.get("title", "").lower())
            if norm_title and norm_title not in seen_titles:
                seen_titles.add(norm_title)
                parsed_papers.append(_public_paper(parsed))
        except Exception as e:
            print(f"[Warning] Failed to read {p_file.name}: {e}")

    return {
        "uploaded_count": len(parsed_papers),
        "papers": parsed_papers
    }


@app.delete("/api/uploaded-pdfs")
def delete_uploaded_pdfs():
    """Delete all PDF files currently stored in the uploads directory."""
    pdf_files = list(UPLOAD_DIR.glob("*.pdf"))
    deleted_count = 0
    failed_files = []

    for pdf_file in pdf_files:
        try:
            pdf_file.unlink()
            deleted_count += 1
        except OSError as e:
            failed_files.append(f"{pdf_file.name}: {e}")

    if failed_files:
        raise HTTPException(
            status_code=500,
            detail=(
                f"Deleted {deleted_count} PDF file(s), but could not delete: "
                + "; ".join(failed_files)
            )
        )

    return {"deleted_count": deleted_count}


@app.post("/api/upload-pdfs")
async def upload_pdfs(files: List[UploadFile] = File(...)):
    """
    Upload and parse one or more research paper PDF documents.
    """
    UPLOAD_DIR.mkdir(exist_ok=True, parents=True)
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
            parsed_papers.append(_public_paper(parsed))
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
    4. Extracts paper-specific research gaps from each paper's available text
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
            for uploaded_paper in req.uploaded_papers[:num_papers]:
                parsed = _parse_selected_upload(uploaded_paper)
                if parsed:
                    papers.append(parsed)
                elif uploaded_paper.get("extracted_text"):
                    papers.append(uploaded_paper)
                else:
                    raise HTTPException(
                        status_code=400,
                        detail="An uploaded paper could not be matched to a stored PDF.",
                    )
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

        # In PDF mode, determine topic, research question, and year range strictly from uploaded manuscripts
        topic = _infer_pdf_topic(papers)
        question = (
            f"What methods, findings, and limitations do the uploaded papers "
            f"report about {topic}?"
        )
        pdf_years = [
            p.get("year") for p in papers
            if p.get("year") and isinstance(p.get("year"), int)
        ]
        if pdf_years:
            start_year = min(pdf_years)
            end_year = max(pdf_years)
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
            raise HTTPException(
                status_code=502,
                detail=(
                    "Live search returned no papers. Please retry or choose PDF upload; "
                    "the app will not substitute unrelated sample papers."
                )
            )

    # Ensure paper count matches target and sequential IDs
    papers = papers[:num_papers]
    for idx, p in enumerate(papers):
        p["id"] = f"paper_{idx + 1}"

    # Step 2: Generate Literature-Review Matrix
    matrix_data = matrix_generator.generate_matrix(papers, question)

    # Step 3: Extract one evidence-grounded research gap per paper
    gaps_data = gap_analyzer.analyze_gaps(papers, topic, question)

    # Step 4: Compile Academic Literature Review Report
    report_data = report_generator.generate_report(
        topic=topic,
        research_question=question,
        papers=papers,
        matrix=matrix_data,
        gaps=gaps_data,
        start_year=start_year,
        end_year=end_year,
        source_mode=req.mode
    )

    # Cache for direct exports
    latest_review_cache["topic"] = topic
    latest_review_cache["research_question"] = question
    latest_review_cache["papers"] = papers
    latest_review_cache["matrix"] = matrix_data
    latest_review_cache["gaps"] = gaps_data
    latest_review_cache["report"] = report_data

    public_papers = [_public_paper(paper) for paper in papers]

    return {
        "meta": {
            "topic": topic,
            "research_question": question,
            "publication_year_span": f"{start_year}–{end_year}",
            "papers_analyzed": len(papers),
            "mode": req.mode
        },
        "papers_list": public_papers,
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
            return FileResponse(
                str(index_file),
                headers={
                    "Cache-Control": "no-cache, no-store, must-revalidate, max-age=0",
                    "Pragma": "no-cache",
                    "Expires": "0"
                }
            )
        return HTMLResponse("<h1>ScholarMatrix AI Frontend Loading...</h1>")
