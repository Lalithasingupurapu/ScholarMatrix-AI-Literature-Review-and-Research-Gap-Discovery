import re
from typing import Any, Dict, List


class LiteratureMatrixGenerator:
    DATASET_NAMES = (
        "TruthfulQA",
        "FEVER",
        "HotpotQA",
        "TriviaQA",
        "PopQA",
        "Natural Questions",
        "NaturalQuestions",
        "PubHealth",
        "ARC-Challenge",
        "BioASQ",
        "MedQA",
        "MS MARCO",
        "BiographyQA",
        "CRUD-RAG",
        "MMLU",
        "GSM8K",
        "SQuAD",
        "HaluEval",
        "WikiData",
        "ImageNet",
        "GLUE",
        "MuSiQue",
        "QASPER",
        "NarrativeQA",
        "FEVEROUS",
        "ELI5",
        "ASQA",
        "KILT",
        "Natural Questions (NQ)",
    )
    METRIC_NAMES = (
        "Exact Match",
        "EM",
        "F1",
        "Precision",
        "Recall",
        "Accuracy",
        "ROUGE",
        "BLEU",
        "BERTScore",
        "MRR",
        "NDCG",
        "MAP",
        "Hit Rate",
        "Faithfulness",
        "Answer Relevance",
        "Context Precision",
        "Context Recall",
        "AUROC",
        "AUC",
        "Latency",
        "throughput",
        "perplexity",
        "BLEU-4",
        "ROUGE-L",
    )
    SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+|\n+")

    @classmethod
    def _sentences(cls, text: str) -> List[str]:
        return [
            re.sub(r"\s+", " ", sentence).strip(" \t-•")
            for sentence in cls.SENTENCE_SPLIT.split(text or "")
            if len(re.sub(r"\s+", " ", sentence).strip()) >= 10
        ]

    @staticmethod
    def _unique(values: List[str], limit: int = 6) -> List[str]:
        seen = set()
        unique = []
        for value in values:
            normalized = value.casefold()
            if normalized not in seen:
                seen.add(normalized)
                unique.append(value)
            if len(unique) >= limit:
                break
        return unique

    @staticmethod
    def _without_references(text: str) -> str:
        return re.split(
            r"\b(?:references|bibliography|works cited)\b",
            text or "",
            maxsplit=1,
            flags=re.IGNORECASE,
        )[0]

    @staticmethod
    def _join_or_unreported(values: List[str], field: str) -> str:
        if values:
            return " • ".join(values)
        return f"Not reported in available paper text ({field})."

    def generate_matrix(
        self, papers: List[Dict[str, Any]], research_question: str = ""
    ) -> List[Dict[str, Any]]:
        """Extract per-paper facts only from the metadata, abstract, or parsed PDF text."""
        matrix = []
        for index, paper in enumerate(papers, start=1):
            title = paper.get("title") or "Untitled paper"
            abstract = paper.get("abstract") or ""
            extracted_text = paper.get("extracted_text") or ""
            analysis_text = self._without_references(extracted_text or abstract)
            sentences = self._sentences(analysis_text)
            title_sentences = self._sentences(title)

            authors = paper.get("authors") or []
            first_author = authors[0].split()[-1] if authors else "Unknown author"
            author_label = f"{first_author} et al." if len(authors) > 1 else first_author

            focus = self._first_matching_sentence(
                sentences,
                (
                    "aim",
                    "objective",
                    "we study",
                    "we investigate",
                    "we address",
                    "we propose",
                    "we present",
                    "we introduce",
                    "this paper",
                    "this work",
                ),
            ) or (title_sentences[0] if title_sentences else title)

            methodology = self._first_matching_sentence(
                sentences,
                (
                    "we propose",
                    "we present",
                    "we introduce",
                    "we develop",
                    "we design",
                    "we implement",
                    "we construct",
                    "we evaluate",
                    "we compare",
                    "our method",
                    "our approach",
                    "methodology",
                    "architecture",
                ),
            )

            datasets = self._extract_datasets(analysis_text)
            metrics = self._extract_metrics_and_baselines(sentences)
            results = self._first_matching_sentence(
                sentences,
                (
                    "results show",
                    "our results",
                    "we find",
                    "we found",
                    "outperform",
                    "achieve",
                    "improve",
                    "improves",
                    "demonstrate",
                    "evaluation shows",
                    "experiments show",
                    "performance",
                ),
            )
            limitations = self._first_matching_sentence(
                sentences,
                (
                    "limitation",
                    "limitations",
                    "future work",
                    "future research",
                    "remain unclear",
                    "does not address",
                    "do not address",
                    "not evaluated",
                    "not evaluate",
                    "we leave",
                    "open question",
                    "challenge",
                    "however",
                    "although",
                    "but ",
                ),
            )
            future_scope = self._first_matching_sentence(
                sentences,
                ("future work", "future research", "we plan", "we leave", "further work"),
            )

            source_scope = (
                paper.get("text_extraction_scope") or "Extracted PDF text excerpt available"
                if extracted_text
                else "Abstract only"
                if abstract
                else "Metadata only; no abstract or full text was available"
            )
            matrix.append(
                {
                    "paper_id": paper.get("id", f"paper_{index}"),
                    "title": title,
                    "authors": author_label,
                    "full_authors": authors,
                    "year": paper.get("year"),
                    "venue": paper.get("venue") or "Publication details unavailable",
                    "citations": paper.get("citation_count", 0),
                    "url": paper.get("url", ""),
                    "pdf_url": paper.get("pdf_url", ""),
                    "abstract": abstract or "Abstract not available from the selected source.",
                    "source_scope": source_scope,
                    "research_focus": focus,
                    "methodology": methodology or "Not described in available paper text.",
                    "datasets": self._join_or_unreported(datasets, "dataset names"),
                    "metrics_and_baselines": metrics
                    or "Not reported in available paper text.",
                    "results": results or "No specific result found in available paper text.",
                    "limitations": limitations
                    or "No explicit limitation found in available paper text.",
                    "future_scope": future_scope
                    or "No explicit future-work statement found in available paper text.",
                }
            )
        return matrix

    @staticmethod
    def _first_matching_sentence(
        sentences: List[str], markers: tuple
    ) -> str:
        for sentence in sentences:
            lower_sentence = sentence.lower()
            if any(marker in lower_sentence for marker in markers):
                return sentence[:700]
        return ""

    def _extract_datasets(self, text: str) -> List[str]:
        found = []
        dataset_context_markers = (
            "dataset",
            "benchmark",
            "evaluation",
            "evaluate",
            "evaluated",
            "experiment",
            "test on",
            "tested on",
            "test set",
            "training set",
        )
        for sentence in self._sentences(text):
            lower_sentence = sentence.lower()
            if not any(marker in lower_sentence for marker in dataset_context_markers):
                continue
            for name in self.DATASET_NAMES:
                if re.search(r"\b" + re.escape(name) + r"\b", sentence, re.IGNORECASE):
                    found.append(name)

        # Capture additional named datasets only when the text explicitly identifies
        # them as a dataset/benchmark; avoid inventing names from generic sentences.
        for match in re.finditer(
            r"\b(?:dataset|benchmark|corpus|test set)s?\s+(?:named\s+|called\s+)?"
            r"([A-Z][A-Za-z0-9_-]*(?:\s+[A-Z][A-Za-z0-9_-]*){0,3})",
            text,
        ):
            candidate = match.group(1).strip()
            if candidate.lower() not in {"the", "our", "this", "these"}:
                found.append(candidate)

        return self._unique(found)

    def _extract_metrics_and_baselines(self, sentences: List[str]) -> str:
        metrics = []
        baselines = []
        for sentence in sentences:
            lower_sentence = sentence.lower()
            has_evaluation_context = any(
                marker in lower_sentence
                for marker in (
                    "evaluation",
                    "evaluate",
                    "experiment",
                    "metric",
                    "measure",
                    "score",
                    "baseline",
                    "compared",
                    "outperform",
                    "accuracy",
                    "precision",
                    "recall",
                    "f1",
                )
            )
            if not has_evaluation_context:
                continue
            for metric in self.METRIC_NAMES:
                if re.search(r"\b" + re.escape(metric.lower()) + r"\b", lower_sentence):
                    metrics.append(metric)
            if any(
                marker in lower_sentence
                for marker in (
                    "baseline",
                    "compared with",
                    "compared to",
                    "compared against",
                    "outperform",
                    "against the",
                    "versus",
                    " vs. ",
                )
            ):
                baselines.append(sentence[:500])

        metric_text = ", ".join(self._unique(metrics, limit=8))
        baseline_text = " | ".join(self._unique(baselines, limit=2))
        if not metric_text and not baseline_text:
            return ""
        return (
            f"Metrics explicitly mentioned: {metric_text or 'Not specified'}"
            f" | Baselines/comparisons: {baseline_text or 'Not specified'}"
        )
