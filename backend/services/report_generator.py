import datetime
from typing import Any, Dict, List


class ResearchReportGenerator:
    def generate_report(
        self,
        topic: str,
        research_question: str,
        papers: List[Dict[str, Any]],
        matrix: List[Dict[str, Any]],
        gaps: List[Dict[str, Any]],
        start_year: int = 2021,
        end_year: int = 2026,
        source_mode: str = "online",
    ) -> Dict[str, Any]:
        """Compile a report exclusively from the papers and extracted facts supplied."""
        now = datetime.datetime.now().strftime("%B %d, %Y")
        mode_label = "uploaded PDFs" if source_mode == "pdf" else "live online search"
        gap_by_paper = {gap.get("paper_id"): gap for gap in gaps}

        paper_sections = []
        matrix_rows = []
        for index, paper in enumerate(papers, start=1):
            paper_id = paper.get("id")
            row = next(
                (item for item in matrix if item.get("paper_id") == paper_id),
                {},
            )
            gap = gap_by_paper.get(paper_id, {})
            authors = ", ".join(paper.get("authors") or []) or "Author details unavailable"
            title = paper.get("title") or "Untitled paper"
            abstract = paper.get("abstract") or "Abstract not available from the selected source."
            citation = f"{authors} ({paper.get('year') or 'Year unavailable'}). *{title}*. {paper.get('venue') or 'Publication details unavailable'}."

            paper_sections.append(
                f"""#### {index}. {title}
**Citation:** {citation}

**Abstract (source text):** {abstract}

**Research focus extracted from this paper:** {row.get('research_focus', 'Not reported in available paper text.')}

**Methodology described in available text:** {row.get('methodology', 'Not described in available paper text.')}

**Datasets and benchmarks named in available text:** {row.get('datasets', 'Not reported in available paper text.')}

**Metrics and baselines named in available text:** {row.get('metrics_and_baselines', 'Not reported in available paper text.')}

**Results stated in available text:** {row.get('results', 'No specific result found in available paper text.')}

**Limitations stated in available text:** {row.get('limitations', 'No explicit limitation found in available paper text.')}

**Future work stated in available text:** {row.get('future_scope', 'No explicit future-work statement found in available paper text.')}

**Paper-specific research gap:** {gap.get('research_gap', 'No gap analysis available.')}
"""
            )
            matrix_rows.append(
                "| {title} | {method} | {datasets} | {metrics} | {results} | {limitations} |".format(
                    title=title.replace("|", "\\|"),
                    method=(row.get("methodology") or "Not reported").replace("|", "\\|"),
                    datasets=(row.get("datasets") or "Not reported").replace("|", "\\|"),
                    metrics=(row.get("metrics_and_baselines") or "Not reported").replace("|", "\\|"),
                    results=(row.get("results") or "Not reported").replace("|", "\\|"),
                    limitations=(row.get("limitations") or "Not reported").replace("|", "\\|"),
                )
            )

        references = []
        for index, paper in enumerate(papers, start=1):
            authors = ", ".join(paper.get("authors") or []) or "Author details unavailable"
            title = paper.get("title") or "Untitled paper"
            year = paper.get("year") or "Year unavailable"
            venue = paper.get("venue") or "Publication details unavailable"
            url = paper.get("url") or paper.get("pdf_url")
            link = f" [Source]({url})" if url else ""
            references.append(f"{index}. {authors} ({year}). *{title}*. {venue}.{link}")

        markdown = f"""# Literature Review: {topic}

**Research question:** {research_question or 'Not specified'}<br>
**Publication year filter:** {start_year}–{end_year}<br>
**Source selected:** {mode_label}<br>
**Papers analyzed:** {len(papers)}<br>
**Generated:** {now}

## Scope and evidence note

This report was generated from the papers returned or uploaded for this review. Paper-level findings below are drawn from each paper's available abstract or extracted PDF text. Dataset names, metrics, baselines, results, limitations, and future-work items are not inferred when the available text does not state them.

## Comparative literature matrix

| Paper | Methodology | Datasets / benchmarks | Metrics / baselines | Results | Limitations |
|---|---|---|---|---|---|
{chr(10).join(matrix_rows) if matrix_rows else '| No papers found | — | — | — | — | — |'}

## Paper-by-paper analysis

{chr(10).join(paper_sections) if paper_sections else 'No papers were returned for this review.'}

## References

{chr(10).join(references) if references else 'No references are available.'}
"""

        return {
            "title": f"Literature Review: {topic}",
            "research_question": research_question,
            "publication_year_span": f"{start_year}–{end_year}",
            "paper_count": len(papers),
            "source_mode": source_mode,
            "generated_date": now,
            "markdown": markdown,
            "executive_summary": (
                f"Generated a paper-specific review from {len(papers)} papers using {mode_label}. "
                "Only information present in each paper's available text is reported."
            ),
        }
