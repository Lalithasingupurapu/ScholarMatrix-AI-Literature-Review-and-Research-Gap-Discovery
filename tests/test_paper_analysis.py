import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from urllib.parse import parse_qs, urlparse

from backend import app
from backend.services.matrix_generator import LiteratureMatrixGenerator
from backend.services.paper_fetcher import PaperFetcher
from backend.services.pdf_parser import PDFParser
from backend.services.report_generator import ResearchReportGenerator


class FakePage:
    def __init__(self, text):
        self.text = text

    def extract_text(self):
        return self.text


class FakeReader:
    metadata = None

    def __init__(self, pages):
        self.pages = [FakePage(text) for text in pages]


class PaperAnalysisTests(unittest.TestCase):
    def test_extracts_named_dataset_and_wrapped_metrics(self):
        paper = {
            "id": "forecasting",
            "title": "Forecasting with ARIMA-GM",
            "authors": [],
            "abstract": "",
            "extracted_text": (
                "The proposed method uses the\n"
                "ETTh1 dataset for evaluation. We report MAE and\n"
                "RMSE, and the ARIMA-GM model outperforms the LSTM baseline."
            ),
        }

        row = LiteratureMatrixGenerator().generate_matrix([paper])[0]

        self.assertIn("ETTh1", row["datasets"])
        self.assertIn("MAE", row["metrics_and_baselines"])
        self.assertIn("RMSE", row["metrics_and_baselines"])
        self.assertIn("LSTM baseline", row["metrics_and_baselines"])

    def test_does_not_infer_dataset_without_evidence(self):
        paper = {
            "id": "no-dataset",
            "title": "A general forecasting approach",
            "authors": [],
            "abstract": "",
            "extracted_text": "The method is evaluated against two model variants.",
        }

        row = LiteratureMatrixGenerator().generate_matrix([paper])[0]

        self.assertEqual(
            row["datasets"],
            "Not reported in available paper text (dataset names).",
        )

    def test_extracts_unlisted_dataset_but_ignores_references(self):
        paper = {
            "id": "custom-dataset",
            "title": "Forecasting benchmark",
            "authors": [],
            "abstract": "",
            "extracted_text": (
                "The evaluation dataset is called SolarGrid-2040.\n"
                "References\n"
                "The M4 dataset is mentioned only in a cited paper."
            ),
        }

        row = LiteratureMatrixGenerator().generate_matrix([paper])[0]

        self.assertIn("SolarGrid-2040", row["datasets"])
        self.assertNotIn("M4", row["datasets"])

    def test_pdf_parser_keeps_full_text_beyond_old_page_and_character_caps(self):
        page_texts = [f"Page {page_number}. " + ("x" * 1000) for page_number in range(1, 106)]
        page_texts[-1] += " The final benchmark is called SolarGrid-2040."
        content = b"%PDF-1.7"

        with patch(
            "backend.services.pdf_parser.pypdf.PdfReader",
            return_value=FakeReader(page_texts),
        ):
            parsed = PDFParser().parse_pdf_bytes(content, "forecast.pdf")

        self.assertEqual(parsed["page_count"], 105)
        self.assertGreater(len(parsed["extracted_text"]), 100000)
        self.assertIn("SolarGrid-2040", parsed["extracted_text"])
        self.assertEqual(
            parsed["text_extraction_scope"],
            "All 105 pages (selectable text)",
        )

    def test_pdf_parser_reports_image_only_pdfs(self):
        with patch(
            "backend.services.pdf_parser.pypdf.PdfReader",
            return_value=FakeReader(["", "  "]),
        ):
            parsed = PDFParser().parse_pdf_bytes(b"%PDF-1.7", "scanned.pdf")

        self.assertTrue(parsed["text_extraction_warnings"])
        self.assertIn("OCR is not configured", parsed["text_extraction_warnings"][0])

    def test_selected_upload_is_reparsed_from_server_storage(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            upload_directory = Path(temporary_directory)
            stored_pdf = upload_directory / "paper.pdf"
            stored_pdf.write_bytes(b"%PDF-1.7")
            parsed_paper = {"extracted_text": "full PDF content"}

            with patch.object(app, "UPLOAD_DIR", upload_directory):
                with patch.object(
                    app.pdf_parser, "parse_pdf", return_value=parsed_paper
                ) as parse_pdf:
                    result = app._parse_selected_upload(
                        {"pdf_url": "/api/uploads/paper.pdf"}
                    )

        self.assertEqual(result, parsed_paper)
        parse_pdf.assert_called_once_with(str(stored_pdf), stored_pdf.name)
        self.assertEqual(
            app._public_paper(parsed_paper),
            {},
        )

    def test_online_direct_open_access_pdf_adds_full_text(self):
        fetcher = PaperFetcher()
        paper = {
            "source": "OpenAlex",
            "pdf_url": "https://papers.example.org/article.pdf",
            "abstract": "Abstract evidence",
        }
        parsed_pdf = {
            "extracted_text": "Full paper evidence",
            "text_extraction_scope": "All 8 pages (selectable text)",
            "text_extraction_warnings": [],
        }

        with patch.object(
            fetcher, "_download_open_access_pdf", return_value=(parsed_pdf, None)
        ):
            fetcher._attach_open_access_full_text([paper])

        self.assertEqual(paper["extracted_text"], "Full paper evidence")
        self.assertEqual(
            paper["text_extraction_scope"],
            "All 8 pages (selectable text)",
        )

    def test_online_results_fall_back_to_abstract_when_pdf_is_unavailable(self):
        fetcher = PaperFetcher()
        paper = {
            "source": "OpenAlex",
            "pdf_url": "https://papers.example.org/article.pdf",
            "abstract": "Abstract evidence",
        }

        with patch.object(
            fetcher,
            "_download_open_access_pdf",
            return_value=(None, "Network unavailable"),
        ):
            fetcher._attach_open_access_full_text([paper])

        self.assertEqual(
            paper["text_extraction_scope"],
            "Abstract only; open-access PDF unavailable",
        )
        self.assertIn("Network unavailable", paper["text_extraction_warnings"][0])

    def test_online_pdf_downloader_rejects_private_network_targets(self):
        private_address = (
            2,
            1,
            6,
            "",
            ("127.0.0.1", 443),
        )
        with patch(
            "backend.services.paper_fetcher.socket.getaddrinfo",
            return_value=[private_address],
        ):
            is_public = PaperFetcher._is_public_https_url(
                "https://127.0.0.1/paper.pdf"
            )

        self.assertFalse(is_public)

    def test_serpapi_google_scholar_results_are_normalized(self):
        fetcher = PaperFetcher()
        payload = {
            "organic_results": [
                {
                    "title": "Forecasting with ARIMA-GM",
                    "link": "https://example.org/paper",
                    "snippet": "The proposed method improves forecasts.",
                    "publication_info": {
                        "summary": "A Researcher, Journal of Forecasting, 2024",
                        "authors": [{"name": "A Researcher"}],
                    },
                    "resources": [
                        {
                            "file_format": "PDF",
                            "link": "https://example.org/paper.pdf",
                        }
                    ],
                    "inline_links": {"cited_by": {"total": 12}},
                }
            ]
        }

        class FakeResponse:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self):
                return json.dumps(payload).encode("utf-8")

        with patch(
            "backend.services.paper_fetcher.urllib.request.urlopen",
            return_value=FakeResponse(),
        ) as urlopen:
            papers = fetcher._fetch_serpapi(
                "forecasting", 2020, 2025, 25, "test-key-not-a-real-secret"
            )

        self.assertEqual(len(papers), 1)
        self.assertEqual(papers[0]["year"], 2024)
        self.assertEqual(papers[0]["authors"], ["A Researcher"])
        self.assertEqual(papers[0]["citation_count"], 12)
        self.assertEqual(papers[0]["pdf_url"], "https://example.org/paper.pdf")
        query = parse_qs(urlparse(urlopen.call_args.args[0].full_url).query)
        self.assertEqual(query["engine"], ["google_scholar"])
        self.assertEqual(query["num"], ["20"])
        self.assertEqual(query["api_key"], ["test-key-not-a-real-secret"])
        self.assertNotIn("context", urlopen.call_args.kwargs)

    def test_serpapi_key_is_read_from_environment(self):
        with patch.dict(
            "os.environ",
            {"SERPAPI_API_KEY": "  replacement-key  "},
            clear=False,
        ):
            from backend.config import get_serpapi_api_key

            self.assertEqual(get_serpapi_api_key(), "replacement-key")

    def test_serper_google_scholar_results_are_normalized(self):
        fetcher = PaperFetcher()
        payload = {
            "organic": [
                {
                    "title": "[PDF] Forecasting with ARIMA-GM",
                    "link": "https://example.org/paper",
                    "snippet": "The proposed method improves forecasts.",
                    "publicationInfo": "A Researcher, B Scientist - Journal of Forecasting, 2024 - example.org",
                    "year": 2024,
                    "citedBy": 45,
                    "pdfUrl": "https://example.org/paper.pdf",
                    "clusterId": "1234567890",
                }
            ]
        }

        class FakeResponse:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self):
                return json.dumps(payload).encode("utf-8")

        class FakeOpener:
            def open(self, request, timeout=15):
                return FakeResponse()

        with patch("urllib.request.build_opener", return_value=FakeOpener()):
            papers = fetcher._fetch_serper(
                "forecasting", 2020, 2025, 10, "test-serper-key"
            )

        self.assertEqual(len(papers), 1)
        self.assertEqual(papers[0]["title"], "Forecasting with ARIMA-GM")
        self.assertEqual(papers[0]["year"], 2024)
        self.assertEqual(papers[0]["authors"], ["A Researcher", "B Scientist"])
        self.assertEqual(papers[0]["citation_count"], 45)
        self.assertEqual(papers[0]["pdf_url"], "https://example.org/paper.pdf")
        self.assertTrue(papers[0]["has_direct_pdf"])
        self.assertEqual(papers[0]["source"], "Serper Google Scholar")

    def test_serper_key_is_read_from_environment(self):
        with patch.dict(
            "os.environ",
            {"SERPER_API_KEY": "  test-serper-env-key  "},
            clear=False,
        ):
            from backend.config import get_serper_api_key

            self.assertEqual(get_serper_api_key(), "test-serper-env-key")

    def test_deduplication_removes_duplicate_and_variant_titles(self):
        fetcher = PaperFetcher()
        papers = [
            {
                "title": "[PDF] Retrieval-Augmented Generation for NLP Tasks",
                "cluster_id": "1001",
                "url": "https://example.org/rag1",
            },
            {
                "title": "Retrieval-Augmented Generation for NLP Tasks: A Study",
                "cluster_id": "1001",
                "url": "https://example.org/rag1-mirror",
            },
            {
                "title": "Graph Retrieval-Augmented Generation",
                "cluster_id": "1002",
                "url": "https://example.org/graph-rag",
            },
        ]
        deduped = fetcher._deduplicate_papers(papers)
        self.assertEqual(len(deduped), 2)
        self.assertEqual(deduped[0]["title"], "Retrieval-Augmented Generation for NLP Tasks")
        self.assertEqual(deduped[1]["title"], "Graph Retrieval-Augmented Generation")


    def test_report_generator_synthesizes_unique_analytical_sections(self):
        papers = [
            {
                "id": "p1",
                "title": "Forecasting with Deep Learning",
                "authors": ["A Researcher", "B Scientist"],
                "year": 2024,
                "venue": "Journal of AI",
                "citation_count": 50,
                "url": "https://example.org/p1",
                "abstract": "We evaluate forecasting with neural models."
            }
        ]
        matrix = [
            {
                "paper_id": "p1",
                "title": "Forecasting with Deep Learning",
                "authors": "A Researcher, B Scientist",
                "year": 2024,
                "research_focus": "Investigating deep learning for forecasting",
                "methodology": "Neural forecasting architecture",
                "datasets": "ETTh1",
                "metrics_and_baselines": "MAE, RMSE",
                "results": "Achieved lower error rates than baseline",
                "limitations": "Evaluated only on single benchmark dataset",
                "future_scope": "Testing on multi-variate streaming data"
            }
        ]
        gaps = [
            {
                "paper_id": "p1",
                "research_gap": "The paper explicitly discusses a limitation: Evaluated only on single benchmark dataset"
            }
        ]
        report = ResearchReportGenerator().generate_report(
            topic="Deep Learning Forecasting",
            research_question="Does deep learning improve time-series forecasts?",
            papers=papers,
            matrix=matrix,
            gaps=gaps,
            start_year=2023,
            end_year=2024,
            source_mode="online"
        )
        md = report["markdown"]
        self.assertIn("## 1. Executive Synthesis & State of the Art", md)
        self.assertIn("## 2. Methodological Taxonomy & Thematic Paradigms", md)
        self.assertIn("## 3. Empirical Evaluation & Benchmark Landscape", md)
        self.assertIn("## 4. Cross-Study Synthesis of Structural Limitations", md)
        self.assertIn("## 5. Synthesis on the Core Research Question", md)
        self.assertIn("## 6. Strategic Research Agenda & Future Roadmap", md)
        self.assertIn("## 7. Systematic Corpus Bibliography", md)


if __name__ == "__main__":
    unittest.main()
