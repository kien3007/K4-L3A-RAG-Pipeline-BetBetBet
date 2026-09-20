"""
Task 7 — Reciprocal Rank Fusion (RRF).

RRF gộp nhiều bảng xếp hạng mà không cộng trực tiếp cosine score với BM25
score. Công thức: RRF(d) = sum(1 / (k + rank)), rank bắt đầu từ 1.

Lưu ý: RRF score chỉ phản ánh thứ hạng, không dùng để quyết định fallback.
"""

from src.contracts import validate_search_results


def rerank_rrf(
    ranked_lists: list[list[dict]],
    top_k: int = 5,
    k: int = 60,
) -> list[dict]:
    """Fuse nhiều ranked lists và trả hybrid SearchResult theo thứ hạng giảm dần."""
    if top_k <= 0 or not ranked_lists:
        return []

    scores: dict[str, float] = {}
    items: dict[str, dict] = {}

    for ranked_list in ranked_lists:
        for rank, item in enumerate(ranked_list, 1):
            item_id = item["id"]
            scores[item_id] = scores.get(item_id, 0.0) + (1.0 / (k + rank))
            if item_id not in items:
                items[item_id] = item

    if not scores:
        return []

    ranked_ids = sorted(scores.keys(), key=lambda i: scores[i], reverse=True)

    results = []
    for item_id in ranked_ids[:top_k]:
        res = dict(items[item_id])
        res["score"] = scores[item_id]
        res["retrieval_method"] = "hybrid"
        results.append(res)

    validate_search_results(results, top_k=top_k, expected_method="hybrid")
    return results


if __name__ == "__main__":
    from src.task5_semantic_search import semantic_search
    from src.task6_lexical_search import lexical_search
    import sys

    sys.stdout.reconfigure(encoding="utf-8")
    query = "Quy định về an toàn giao thông đường bộ"
    dense_results = semantic_search(query, top_k=5)
    sparse_results = lexical_search(query, top_k=5)
    fused = rerank_rrf([dense_results, sparse_results], top_k=5)

    print(f"=== RRF Hybrid Results for '{query}' ===")
    for idx, r in enumerate(fused, 1):
        print(f"[{idx}] Score: {r['score']:.5f} | ID: {r['id']}")
        print(f"    Title: {r['metadata'].get('title')}")
        print(f"    Method: {r['retrieval_method']}\n")
