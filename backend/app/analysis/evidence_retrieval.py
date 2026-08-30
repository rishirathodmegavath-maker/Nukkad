"""Small, dependency-free TF-IDF vector index over the evidence corpus."""
from __future__ import annotations

import json
import math
import re
from collections import Counter
from pathlib import Path

from ..schemas import EvidenceItem

CORPUS_PATH = Path(__file__).resolve().parents[2] / "evidence_corpus" / "documents.json"


def _tokens(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


class EvidenceIndex:
    def __init__(self, path: Path = CORPUS_PATH):
        self.documents: list[dict[str, str]] = json.loads(path.read_text(encoding="utf-8"))
        self.doc_counts = [Counter(_tokens(d["text"] + " " + d["source"])) for d in self.documents]
        document_frequency = Counter()
        for counts in self.doc_counts:
            document_frequency.update(counts.keys())
        n = max(1, len(self.documents))
        self.idf = {term: math.log((n + 1) / (freq + 1)) + 1 for term, freq in document_frequency.items()}
        self.vectors = [self._vector(counts) for counts in self.doc_counts]

    def _vector(self, counts: Counter[str]) -> dict[str, float]:
        total = max(1, sum(counts.values()))
        return {term: count / total * self.idf.get(term, 1.0) for term, count in counts.items()}

    @staticmethod
    def _cosine(left: dict[str, float], right: dict[str, float]) -> float:
        dot = sum(value * right.get(term, 0.0) for term, value in left.items())
        left_norm = math.sqrt(sum(value * value for value in left.values()))
        right_norm = math.sqrt(sum(value * value for value in right.values()))
        return dot / (left_norm * right_norm) if left_norm and right_norm else 0.0

    def search(self, query: str, limit: int = 2) -> list[EvidenceItem]:
        query_vector = self._vector(Counter(_tokens(query)))
        ranked = sorted(
            ((self._cosine(query_vector, vector), doc) for vector, doc in zip(self.vectors, self.documents)),
            key=lambda pair: pair[0],
            reverse=True,
        )[:limit]
        return [
            EvidenceItem(
                source=doc["source"], text=doc["text"], relevance="supporting" if score >= 0.1 else "contextual",
                document_id=doc["id"], retrieval_score=round(score, 3), freshness=doc["freshness"], lineage=doc["lineage"],
            )
            for score, doc in ranked if score > 0
        ]


INDEX = EvidenceIndex()
