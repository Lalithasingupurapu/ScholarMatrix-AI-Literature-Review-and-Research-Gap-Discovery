import re
from typing import Any, Dict, List, Optional, Tuple


class ResearchGapAnalyzer:
    GAP_MARKERS = (
        "limitation",
        "future work",
        "future research",
        "further work",
        "remains unclear",
        "remain unclear",
        "not address",
        "not explore",
        "does not",
        "do not",
        "lack",
        "challenge",
        "we leave",
        "open question",
        "out of scope",
        "unresolved",
        "not evaluate",
        "not test",
    )

    @staticmethod
    def _normalize_text(value: str) -> str:
        return re.sub(r"\s+", " ", value or "").strip()

    @classmethod
    def _find_gap_evidence(
        cls, paper: Dict[str, Any]
    ) -> Tuple[Optional[str], Optional[str]]:
        page_evidence = paper.get("page_evidence") or []
        candidates = [
            (
                cls._normalize_text(item.get("quote", "")),
                cls._normalize_text(item.get("section", "")) or "Paper text",
            )
            for item in page_evidence
        ]
        extracted_text = cls._normalize_text(paper.get("extracted_text", ""))
        if extracted_text:
            extracted_text = re.split(
                r"\b(?:references|bibliography)\b", extracted_text, maxsplit=1, flags=re.IGNORECASE
            )[0]
            candidates.extend(
                (cls._normalize_text(sentence), "Extracted paper text")
                for sentence in re.split(r"(?<=[.!?])\s+", extracted_text)
            )
        abstract = cls._normalize_text(paper.get("abstract", ""))
        candidates.extend(
            (cls._normalize_text(sentence), "Abstract")
            for sentence in re.split(r"(?<=[.!?])\s+", abstract)
        )

        marker_candidates = [
            (quote, section)
            for quote, section in candidates
            if quote and any(marker in quote.lower() for marker in cls.GAP_MARKERS)
        ]
        if not marker_candidates:
            return None, None

        # Prefer direct limitation/future-work statements over general contrast words.
        marker_candidates.sort(
            key=lambda candidate: (
                min(
                    index
                    for index, marker in enumerate(cls.GAP_MARKERS)
                    if marker in candidate[0].lower()
                ),
                len(candidate[0]) > 500,
            )
        )
        quote, section = marker_candidates[0]
        if len(quote) > 500:
            quote = quote[:497].rsplit(" ", 1)[0] + "..."
        return quote, section

    def analyze_gaps(
        self,
        papers: List[Dict[str, Any]],
        topic: str,
        research_question: str,
    ) -> List[Dict[str, Any]]:
        """Return one evidence-grounded research-gap entry for every paper."""
        gaps = []
        for index, paper in enumerate(papers, start=1):
            paper_id = paper.get("id") or f"paper_{index}"
            title = self._normalize_text(paper.get("title", "")) or "Untitled paper"
            authors = paper.get("authors") or []
            year = paper.get("year")
            venue = paper.get("venue") or "Publication details not available"
            url = paper.get("pdf_url") or paper.get("url") or ""

            first_author = authors[0].split()[-1] if authors else "Unknown author"
            citation = (
                f"{first_author} et al. ({year})"
                if len(authors) > 1 and year
                else f"{first_author} ({year})"
                if year
                else first_author
            )

            quote, section = self._find_gap_evidence(paper)
            if quote:
                research_gap = (
                    "The paper explicitly discusses a limitation or future-work "
                    f"gap: {quote}"
                )
                gap_basis = f"Extracted from the paper's {section}."
            else:
                research_gap = (
                    "No explicit limitation or future-research gap was found in the "
                    "available paper text. The gap cannot be reliably determined "
                    "without additional full-text evidence."
                )
                gap_basis = (
                    "No limitation or future-work statement was found in the "
                    "available abstract or extracted PDF text."
                )

            evidence = []
            if quote:
                evidence.append(
                    {
                        "paper_id": paper_id,
                        "citation": citation,
                        "title": title,
                        "year": year,
                        "venue": venue,
                        "url": url,
                        "section": section,
                        "evidence_quote": quote,
                    }
                )

            gaps.append(
                {
                    "id": f"gap_{paper_id}",
                    "paper_id": paper_id,
                    "paper_title": title,
                    "citation": citation,
                    "category": "Paper-specific research gap",
                    "title": title,
                    "description": research_gap,
                    "detailed_analysis": research_gap,
                    "research_gap": research_gap,
                    "gap_basis": gap_basis,
                    "has_explicit_gap": bool(quote),
                    "context_excerpt": (
                        self._normalize_text(paper.get("abstract", ""))
                        if not self._normalize_text(paper.get("abstract", "")).lower().startswith(
                            "study investigating "
                        )
                        else ""
                    ),
                    "url": url,
                    "supporting_evidence": evidence,
                    "evidence_count": len(evidence),
                    "research_agenda": [],
                    "future_directions": [],
                }
            )

        return gaps
