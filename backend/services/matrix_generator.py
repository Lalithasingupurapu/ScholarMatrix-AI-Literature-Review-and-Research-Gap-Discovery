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
        "M3",
        "M4",
        "M5",
        "ETT",
        "ETTh1",
        "ETTh2",
        "ETTm1",
        "ETTm2",
        "Electricity",
        "Exchange",
        "Traffic",
        "Weather",
        "Solar-Energy",
        "NN5",
        "PEMS03",
        "PEMS04",
        "PEMS07",
        "PEMS08",
        "Tourism",
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
        "MAE",
        "MSE",
        "RMSE",
        "MAPE",
        "sMAPE",
        "MASE",
        "WAPE",
        "R-squared",
        "Theil's U",
    )
    SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+|\n+")
    DATASET_MARKER = re.compile(
        r"\b(?:data\s*sets?|benchmarks?|corpora|corpus|test\s+sets?|training\s+sets?)\b",
        re.IGNORECASE,
    )
    NAMED_DATASET = re.compile(
        r"\b([A-Z0-9][A-Za-z0-9._/-]*(?:\s+[A-Z0-9][A-Za-z0-9._/-]*){0,3})"
        r"\s+(?:data\s*set|benchmark|corpus|test\s+set|training\s+set)\b",
    )
    DATASET_AFTER_MARKER = re.compile(
        r"(?i:\b(?:data\s*sets?|benchmarks?|corpora|corpus|test\s+sets?|training\s+sets?)\b)"
        r"(?:\s*(?::|-)\s*|\s+)"
        r"(?:(?i:(?:is|are|was|were)\s+))?"
        r"(?:(?i:(?:named|called|including|include|such\s+as)\s+))?"
        r"([A-Z0-9][A-Za-z0-9._/-]*(?:\s+[A-Z0-9][A-Za-z0-9._/-]*){0,3})"
    )
    DATASET_CONTEXT = re.compile(
        r"\b(?:evaluation|evaluate|evaluated|experiment|experiments|test(?:ed)? on|"
        r"training set|using|we use|used)\b",
        re.IGNORECASE,
    )
    GENERIC_DATASET_NAMES = {
        "a", "an", "the", "our", "this", "these", "training", "test",
        "evaluation", "benchmark", "corpus", "dataset", "data",
    }

    @classmethod
    def _sentences(cls, text: str) -> List[str]:
        # PDF extraction often inserts line breaks in the middle of sentences or words.
        text = re.sub(r"(?<=\w)-\s*\n\s*(?=\w)", "", text or "")
        text = re.sub(r"\s+", " ", text)
        return [
            re.sub(r"\s+", " ", sentence).strip(" \t-•")
            for sentence in cls.SENTENCE_SPLIT.split(text)
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
        lines = (text or "").splitlines()
        for index, line in enumerate(lines):
            if re.fullmatch(
                r"\s*(?:(?:\d+(?:\.\d+)*|[A-Z])[\s.)-]+)?"
                r"(?:references|bibliography|works cited)\s*",
                line,
                flags=re.IGNORECASE,
            ):
                return "\n".join(lines[:index])
        return text or ""

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

            source_scope = paper.get("text_extraction_scope") or (
                "Extracted paper text available"
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
        sentences = self._sentences(text)
        for sentence in sentences:
            has_dataset_context = bool(
                self.DATASET_MARKER.search(sentence)
                or self.DATASET_CONTEXT.search(sentence)
            )
            if has_dataset_context:
                for name in self.DATASET_NAMES:
                    if re.search(r"\b" + re.escape(name) + r"\b", sentence, re.IGNORECASE):
                        found.append(name)

            if self.DATASET_MARKER.search(sentence):
                matches = (
                    self.NAMED_DATASET.finditer(sentence),
                    self.DATASET_AFTER_MARKER.finditer(sentence),
                )
                for match_group in matches:
                    for match in match_group:
                        candidate = self._clean_dataset_candidate(match.group(1))
                        if candidate:
                            found.append(candidate)

        return self._unique(found)

    @classmethod
    def _clean_dataset_candidate(cls, candidate: str) -> str:
        candidate = candidate.strip(" \t,;:.()[]{}")
        words = candidate.split()
        while words and words[0].casefold() in cls.GENERIC_DATASET_NAMES:
            words.pop(0)
        while words and words[-1].casefold() in cls.GENERIC_DATASET_NAMES:
            words.pop()
        return " ".join(words)

    def _extract_metrics_and_baselines(self, sentences: List[str]) -> str:
        metrics = []
        baselines = []
        for sentence in sentences:
            baseline_sentence = re.sub(
                r"^.*?\bBaselines/comparisons:\s*",
                "",
                sentence,
                flags=re.IGNORECASE,
            )
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
            has_explicit_metric = any(
                re.search(r"\b" + re.escape(metric.lower()) + r"\b", lower_sentence)
                for metric in self.METRIC_NAMES
            )
            if not has_evaluation_context and not has_explicit_metric:
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
                baselines.append(baseline_sentence[:500])

        metric_text = ", ".join(self._unique(metrics, limit=8))
        baseline_text = " | ".join(self._unique(baselines, limit=2))
        if not metric_text and not baseline_text:
            return ""
        return (
            f"Metrics explicitly mentioned: {metric_text or 'Not specified'}"
            f" | Baselines/comparisons: {baseline_text or 'Not specified'}"
        )
