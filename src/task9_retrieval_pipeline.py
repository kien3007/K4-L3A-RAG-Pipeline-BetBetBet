"""
Task 9 — Retrieval pipeline hoàn chỉnh.

Luồng xử lý:
    1. Chạy semantic_search và lexical_search.
    2. Fuse hai danh sách bằng RRF đúng một lần.
    3. Lấy best cosine score gốc từ dense results.
    4. Nếu score dưới threshold, thử PageIndex fallback.
    5. Nếu fallback lỗi, trả hybrid results thay vì crash.

Không so sánh threshold với RRF score vì hai thang đo khác nhau.
"""

import logging
import os
from dotenv import load_dotenv

from .task5_semantic_search import semantic_search
from .task6_lexical_search import lexical_search
from .task7_reranking import rerank_rrf
from .task8_pageindex_vectorless import pageindex_search

load_dotenv()

SCORE_THRESHOLD = float(os.getenv("SCORE_THRESHOLD", "0.3")) if os.getenv("SCORE_THRESHOLD") else 0.3
DEFAULT_TOP_K = 5

logger = logging.getLogger(__name__)


def retrieve(
    query: str,
    top_k: int = DEFAULT_TOP_K,
    score_threshold: float = SCORE_THRESHOLD,
    use_reranking: bool = True,
) -> list[dict]:
    """Trả về hybrid hoặc pageindex SearchResult theo hợp đồng."""
    if top_k <= 0 or not query.strip():
        return []

    # 1. Thu thập kết quả từ dense semantic search và sparse BM25 lexical search
    dense = semantic_search(query, top_k=top_k * 2)
    sparse = lexical_search(query, top_k=top_k * 2)

    # 2. Fuse bằng RRF đúng một lần duy nhất trong toàn pipeline
    if use_reranking:
        hybrid = rerank_rrf([dense, sparse], top_k=top_k)
    else:
        hybrid = dense[:top_k]

    # 3. Lấy điểm tương đồng gốc cao nhất từ dense retrieval
    best_dense_score = dense[0]["score"] if dense else 0.0

    # 4. Kiểm tra ngưỡng tin cậy để quyết định fallback
    if best_dense_score < score_threshold:
        try:
            fallback = pageindex_search(query, top_k=top_k)
            if fallback:
                return fallback
        except Exception as exc:
            logger.warning(f"Fallback provider error (reverting to hybrid): {exc}")

    # 5. Mặc định trả về kết quả hybrid
    return hybrid[:top_k]


if __name__ == "__main__":
    import sys

    sys.stdout.reconfigure(encoding="utf-8")
    sample_queries = [
        "Quy định về bảo đảm an toàn giao thông đường bộ",
        "Luật Ngân sách nhà nước về các khoản thu chi",
        "Thủ tục đăng ký kinh doanh sao Hỏa ngoài vũ trụ",  # Query out-of-domain để kiểm tra fallback
    ]

    for q in sample_queries:
        print(f"\n{'='*60}\nQuery: '{q}'")
        res = retrieve(q, top_k=3, score_threshold=0.4)
        for idx, item in enumerate(res, 1):
            print(f"[{idx}] Method: {item['retrieval_method']} | Score: {item['score']:.4f} | ID: {item['id']}")
            print(f"    Title: {item['metadata'].get('title')}")
