"""
Task 6 — Lexical search bằng BM25.

Dùng cùng corpus chunks với Task 5. BM25 phù hợp với từ khóa chính xác, mã tài
liệu và tên riêng. Output phải theo SearchResult và sort score giảm dần.
"""

import math
from typing import Any
import numpy as np
from rank_bm25 import BM25Okapi

from src.contracts import validate_search_results

CORPUS: list[dict] = []
_CACHED_BM25: Any = None
_CACHED_CORPUS_ID: tuple[int, int] | None = None


class RobustBM25Okapi(BM25Okapi):
    """BM25Okapi có điều chỉnh IDF theo chuẩn Lucene khi IDF <= 0, tránh trường hợp tập mẫu nhỏ."""

    def _calc_idf(self, nd):
        super()._calc_idf(nd)
        for word, freq in nd.items():
            if self.idf.get(word, 0.0) <= 0:
                self.idf[word] = math.log(1 + (self.corpus_size - freq + 0.5) / (freq + 0.5))


def get_corpus() -> list[dict]:
    """Lazy load corpus chunks từ standardized documents nếu CORPUS chưa có."""
    global CORPUS
    if not CORPUS:
        from src.task4_chunking_indexing import chunk_documents, load_documents

        docs = load_documents()
        CORPUS = chunk_documents(docs)
    return CORPUS


def build_bm25_index(corpus: list[dict]) -> BM25Okapi:
    """Tạo BM25 index từ cùng corpus chunks của Task 4."""
    tokenized = [item["content"].lower().split() for item in corpus]
    return RobustBM25Okapi(tokenized)


def _get_bm25_instance(corpus: list[dict]) -> BM25Okapi:
    """Lấy hoặc tạo BM25 index có caching theo corpus."""
    global _CACHED_BM25, _CACHED_CORPUS_ID
    current_id = (id(corpus), len(corpus))
    if _CACHED_BM25 is None or _CACHED_CORPUS_ID != current_id:
        _CACHED_BM25 = build_bm25_index(corpus)
        _CACHED_CORPUS_ID = current_id
    return _CACHED_BM25


def lexical_search(query: str, top_k: int = 10) -> list[dict]:
    """Trả về BM25 SearchResult theo score giảm dần."""
    if top_k <= 0 or not query.strip():
        return []

    corpus = CORPUS if CORPUS else get_corpus()
    if not corpus:
        return []

    query_tokens = query.lower().split()
    if not query_tokens:
        return []

    bm25 = _get_bm25_instance(corpus)
    scores = bm25.get_scores(query_tokens)

    # Sort indices theo điểm giảm dần
    ranked_indices = np.argsort(scores)[::-1]

    results = []
    seen_ids = set()
    for index in ranked_indices:
        score = float(scores[index])
        if score <= 0:
            continue
        item = corpus[index]
        if item["id"] in seen_ids:
            continue
        seen_ids.add(item["id"])

        clean_meta = dict(item["metadata"])
        if clean_meta.get("url") == "":
            clean_meta["url"] = None

        if "chunk_index" in clean_meta:
            clean_meta["chunk_index"] = int(clean_meta["chunk_index"])

        results.append({
            "id": item["id"],
            "content": item["content"],
            "score": score,
            "metadata": clean_meta,
            "retrieval_method": "bm25",
        })
        if len(results) >= top_k:
            break

    validate_search_results(results, top_k=top_k, expected_method="bm25")
    return results


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    sample_query = "Luật Ngân sách nhà nước"
    print(f"=== BM25 Lexical Search for: '{sample_query}' ===")
    for idx, res in enumerate(lexical_search(sample_query, top_k=3), start=1):
        print(f"[{idx}] Score: {res['score']:.4f} | ID: {res['id']}")
        print(f"    Title: {res['metadata'].get('title')}")
        print(f"    Snippet: {res['content'][:150]}...\n")
