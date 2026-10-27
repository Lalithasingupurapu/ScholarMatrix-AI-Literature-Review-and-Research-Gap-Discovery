import csv
import io
import re
from typing import List, Dict, Any


class ExportService:
    @staticmethod
    def export_matrix_csv(matrix: List[Dict[str, Any]]) -> str:
        """
        Exports the literature matrix as a CSV formatted string.
        """
        output = io.StringIO()
        fieldnames = [
            "Paper ID", "Title", "Authors", "Year", "Venue", "Citations",
            "Research Focus", "Methodology", "Datasets", "Metrics & Baselines",
            "Key Results", "Limitations", "Future Scope", "URL"
        ]
        writer = csv.DictWriter(output, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
        writer.writeheader()

        for row in matrix:
            writer.writerow({
                "Paper ID": row.get("paper_id", ""),
                "Title": row.get("title", ""),
                "Authors": row.get("authors", ""),
                "Year": row.get("year", ""),
                "Venue": row.get("venue", ""),
                "Citations": row.get("citations", 0),
                "Research Focus": row.get("research_focus", ""),
                "Methodology": row.get("methodology", ""),
                "Datasets": row.get("datasets", ""),
                "Metrics & Baselines": row.get("metrics_and_baselines", ""),
                "Key Results": row.get("results", ""),
                "Limitations": row.get("limitations", ""),
                "Future Scope": row.get("future_scope", ""),
                "URL": row.get("url", "")
            })

        return output.getvalue()

    @staticmethod
    def export_bibtex(papers: List[Dict[str, Any]]) -> str:
        """
        Exports paper references as BibTeX bibliography string.
        """
        bibtex_entries = []
        for p in papers:
            first_author = p.get("authors", ["Author"])[0].split()[-1].lower() if p.get("authors") else "author"
            first_author_clean = re.sub(r'[^a-z0-9]', '', first_author)
            year = p.get("year", 2024)
            title_word = re.sub(r'[^a-z0-9]', '', p.get("title", "paper").split()[0].lower())
            cite_key = f"{first_author_clean}{year}{title_word}"

            author_field = " and ".join(p.get("authors", ["Anonymous"]))
            title_field = p.get("title", "Untitled")
            year_field = str(year)
            venue_field = p.get("venue", "arXiv Preprint")
            url_field = p.get("url") or p.get("pdf_url") or ""

            entry = f"""@article{{{cite_key},
  author    = {{{author_field}}},
  title     = {{{{{title_field}}}}},
  journal   = {{{venue_field}}},
  year      = {{{year_field}}},
  url       = {{{url_field}}}
}}"""
            bibtex_entries.append(entry)

        return "\n\n".join(bibtex_entries)
