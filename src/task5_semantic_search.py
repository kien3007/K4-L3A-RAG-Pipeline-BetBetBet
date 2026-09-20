"""
Task 5 — Semantic search.

Embed query bằng chính hàm của Task 4, query ChromaDB và đổi cosine distance
thành similarity. Output phải theo SearchResult, sort giảm dần và không quá top_k.
"""

from src.contracts import validate_search_results
from .task4_chunking_indexing import embed_texts, get_collection


def semantic_search(query: str, top_k: int = 10) -> list[dict]:
    """Trả về dense SearchResult theo score giảm dần."""
    if top_k <= 0 or not query.strip():
        return []

    collection = get_collection()
    n_results = top_k
    if hasattr(collection, "count"):
        try:
            total_docs = collection.count()
            if total_docs == 0:
                return []
            n_results = min(top_k, total_docs)
        except Exception:
            pass

    query_vectors = embed_texts([query])
    if not query_vectors:
        return []
    query_vector = query_vectors[0]

    response = collection.query(
        query_embeddings=[query_vector],
        n_results=n_results,
        include=["documents", "metadatas", "distances"],
    )

    results = []
    seen_ids = set()

    if response and response.get("ids") and response["ids"][0]:
        ids = response["ids"][0]
        docs = response.get("documents", [[]])[0]
        metadatas = response.get("metadatas", [[]])[0]
        distances = response.get("distances", [[]])[0]

        for item_id, content, meta, distance in zip(ids, docs, metadatas, distances):
            if item_id in seen_ids:
                continue
            seen_ids.add(item_id)

            # Cosine distance to similarity: similarity = max(0.0, 1.0 - distance)
            score = max(0.0, 1.0 - float(distance))

            clean_meta = dict(meta) if meta else {}
            if clean_meta.get("url") == "":
                clean_meta["url"] = None

            if "chunk_index" in clean_meta:
                clean_meta["chunk_index"] = int(clean_meta["chunk_index"])
            else:
                try:
                    clean_meta["chunk_index"] = int(item_id.rsplit("-", 1)[-1])
                except Exception:
                    clean_meta["chunk_index"] = 0

            results.append({
                "id": item_id,
                "content": content,
                "score": score,
                "metadata": clean_meta,
                "retrieval_method": "dense",
            })

    # Sort descending by score
    sorted_results = sorted(results, key=lambda item: item["score"], reverse=True)[:top_k]
    validate_search_results(sorted_results, top_k=top_k, expected_method="dense")
    return sorted_results


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    sample_query = "Quy định về an toàn giao thông đường bộ"
    print(f"=== Semantic Search for: '{sample_query}' ===")
    for idx, res in enumerate(semantic_search(sample_query, top_k=3), start=1):
        print(f"[{idx}] Score: {res['score']:.4f} | ID: {res['id']}")
        print(f"    Title: {res['metadata'].get('title')}")
        print(f"    Snippet: {res['content'][:150]}...\n")
