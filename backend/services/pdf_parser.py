import re
from io import BytesIO
from pathlib import Path
from typing import Dict, Any, List, Optional
from urllib.parse import quote
import pypdf


class PDFParser:
    def __init__(self):
        pass

    def parse_pdf(self, file_path: str, filename: str = "") -> Dict[str, Any]:
        """
        Extracts structured paper metadata and content from an uploaded PDF.
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"PDF file not found: {file_path}")

        reader = pypdf.PdfReader(str(path))
        return self._parse_reader(
            reader, filename or path.name, path.stat().st_size, path.name
        )

    def parse_pdf_bytes(self, content: bytes, filename: str = "") -> Dict[str, Any]:
        """Parse PDF bytes without writing a temporary file."""
        reader = pypdf.PdfReader(BytesIO(content))
        return self._parse_reader(reader, filename, len(content), "")

    def _parse_reader(
        self,
        reader: Any,
        filename: str,
        file_size: int,
        stored_filename: str,
    ) -> Dict[str, Any]:
        num_pages = len(reader.pages)
        page_records = []
        for index, page in enumerate(reader.pages):
            page_records.append({
                "page": index + 1,
                "text": page.extract_text() or "",
            })

        full_text = "\n\n".join(record["text"] for record in page_records)
        first_page_text = page_records[0]["text"] if page_records else ""
        last_pages_text = "\n\n".join(
            record["text"] for record in page_records[-2:]
        )
        pages_with_text = sum(
            bool(record["text"].strip()) for record in page_records
        )

        # 1. Title Extraction
        title = self._extract_title(reader.metadata, first_page_text, filename)

        # 2. Year Extraction
        year = self._extract_year(first_page_text, full_text)

        # 3. Authors Extraction
        authors = self._extract_authors(reader.metadata, first_page_text)

        # 4. Abstract Extraction
        abstract = self._extract_abstract(first_page_text, full_text)

        # 5. References Extraction
        references = self._extract_references(last_pages_text, full_text)

        # 6. Page-level evidence extraction
        page_evidence = self._extract_page_evidence(page_records)

        return {
            "id": f"pdf_{Path(stored_filename or filename).stem[:20]}",
            "title": title,
            "authors": authors,
            "year": year,
            "venue": "Uploaded PDF Manuscript",
            "citation_count": None,
            "abstract": abstract,
            "extracted_text": full_text,
            "text_extraction_scope": (
                f"All {num_pages} pages (selectable text)"
                if pages_with_text == num_pages and num_pages > 0
                else f"Selectable text on {pages_with_text} of {num_pages} pages"
                if pages_with_text
                else f"No selectable text found across {num_pages} pages"
            ),
            "text_extraction_warnings": (
                [
                    "No selectable text was extracted. This PDF may be scanned or image-only; OCR is not configured."
                ]
                if not pages_with_text
                else [
                    f"No selectable text was extracted from {num_pages - pages_with_text} page(s); OCR may be needed for image-only pages."
                ]
                if pages_with_text < num_pages
                else []
            ),
            "url": f"/api/uploads/{quote(stored_filename)}" if stored_filename else "",
            "pdf_url": f"/api/uploads/{quote(stored_filename)}" if stored_filename else "",
            "page_count": num_pages,
            "page_evidence": page_evidence,
            "referenced_works": [],
            "raw_references": references[:15],
            "source": "Uploaded PDF",
            "file_size_kb": round(file_size / 1024, 1)
        }

    def _extract_page_evidence(self, page_records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Scans each page for limitation statements, bottlenecks, and empirical findings with page attribution.
        """
        findings = []
        keywords = [
            "limitation", "bottleneck", "challenge", "vulnerability", "hallucinat", "noise",
            "latency", "failure mode", "future work", "error analysis", "trade-off", "degradation"
        ]
        seen_quotes = set()

        for p in page_records:
            page_num = p["page"]
            text = p["text"]
            sentences = re.split(r'(?<=[.!?])\s+', text)
            for s in sentences:
                s_clean = re.sub(r'\s+', ' ', s).strip()
                if len(s_clean) < 40 or len(s_clean) > 280:
                    continue
                lower_s = s_clean.lower()
                if any(k in lower_s for k in keywords):
                    if s_clean not in seen_quotes:
                        seen_quotes.add(s_clean)
                        sec = "Empirical Evaluation"
                        if "limitation" in lower_s:
                            sec = "Limitations & Constraints"
                        elif "future" in lower_s:
                            sec = "Future Work"
                        elif "latency" in lower_s or "cost" in lower_s:
                            sec = "Computational Efficiency"
                        elif "hallucinat" in lower_s or "noise" in lower_s:
                            sec = "Robustness & Errors"

                        findings.append({
                            "page": page_num,
                            "section": sec,
                            "quote": s_clean
                        })
                        if len(findings) >= 8:
                            return findings
        return findings

    def _extract_title(self, metadata: Any, first_page: str, filename: str) -> str:
        # Check metadata
        if metadata and metadata.title and len(metadata.title.strip()) > 5:
            meta_title = metadata.title.strip()
            if not meta_title.lower().startswith("untitled") and not meta_title.endswith(".pdf"):
                if not any(k in meta_title.lower() for k in ["copyright", "published by", "open access", "journal of", "arxiv", "vol."]):
                    return meta_title

        # Check first page lines
        lines = [line.strip() for line in first_page.split("\n") if len(line.strip()) > 3]
        for line in lines[:15]:
            lower_l = line.lower()
            # Skip publisher notices, headers, copyright, ISSN, DOIs, license, open access clauses
            if any(h in lower_l for h in [
                "arxiv:", "ieee", "springer", "proceedings", "conference", "vol.", "issn",
                "copyright", "©", "published by", "open access", "http", "doi:", "license",
                "authors.", "unrestricted use", "reproduction in any medium", "properly cited",
                "creative commons", "all rights reserved"
            ]):
                continue
            if len(line.split()) >= 3 and len(line) < 160:
                return line

        # Fallback to sanitized filename
        base_name = Path(filename).stem if filename else "Uploaded Academic Paper"
        cleaned_name = re.sub(r'[-_]', ' ', base_name)
        cleaned_name = re.sub(r'\b[a-f0-9]{8}\b', '', cleaned_name).strip()
        return cleaned_name.title()

    def _extract_year(self, first_page: str, full_text: str) -> Optional[int]:
        # Look for 2021-2026 or 2018-2026 in first page
        matches = re.findall(r'\b(20(?:1[89]|2[0-6]))\b', first_page)
        if matches:
            return int(matches[-1])
        matches_all = re.findall(r'\b(20(?:1[89]|2[0-6]))\b', full_text[:3000])
        if matches_all:
            return int(matches_all[0])
        return None

    def _extract_authors(self, metadata: Any, first_page: str) -> List[str]:
        if metadata and metadata.author and len(metadata.author.strip()) > 3:
            raw_authors = re.split(r'[,;and]', metadata.author)
            cleaned = [a.strip() for a in raw_authors if len(a.strip()) > 2]
            if cleaned:
                return cleaned[:5]

        # Scan first page between title and abstract
        lines = [line.strip() for line in first_page.split("\n") if line.strip()]
        for i, line in enumerate(lines[:12]):
            if any(kw in line.lower() for kw in ["university", "department", "institute", "laboratory", "@", "email"]):
                if i > 0:
                    prev_line = lines[i-1]
                    parts = re.split(r'[,;]|\band\b', prev_line)
                    res = [p.strip() for p in parts if 2 < len(p.strip()) < 35 and not any(char.isdigit() for char in p)]
                    if res:
                        return res[:5]

        return ["Manuscript Contributor(s)"]

    def _extract_abstract(self, first_page: str, full_text: str) -> str:
        # Pattern matching 'Abstract' block without middle inline (?i)
        match = re.search(
            r'abstract[\s\:\.\-—\n]+([\s\S]+?)(?=\n(?:1[\.\s]+|i[\.\s]+)?(?:introduction|keywords|index terms)|\n\n\n)',
            first_page,
            flags=re.IGNORECASE
        )
        if match:
            abstract_text = re.sub(r'\s+', ' ', match.group(1)).strip()
            if len(abstract_text) > 40:
                return abstract_text[:1200]

        # Try on full text
        match_full = re.search(
            r'abstract[\s\:\.\-—\n]+([\s\S]+?)(?=\n(?:1[\.\s]+)?introduction)',
            full_text[:4000],
            flags=re.IGNORECASE
        )
        if match_full:
            abstract_text = re.sub(r'\s+', ' ', match_full.group(1)).strip()
            if len(abstract_text) > 40:
                return abstract_text[:1200]

        return ""

    def _extract_references(self, last_pages: str, full_text: str) -> List[str]:
        refs = []
        text_to_search = last_pages if len(last_pages) > 200 else full_text[-5000:]
        ref_match = re.search(
            r'(?:references|bibliography)[\s\:\.\n]+([\s\S]+)',
            text_to_search,
            flags=re.IGNORECASE
        )
        if ref_match:
            raw_refs = ref_match.group(1)
            # Match bracketed refs like [1], [2] or standard numbered
            split_items = re.split(r'\n\s*\[\d+\]|\n\s*\d+\.\s+', raw_refs)
            for item in split_items:
                item_clean = re.sub(r'\s+', ' ', item).strip()
                if len(item_clean) > 20:
                    refs.append(item_clean[:180])
        return refs
