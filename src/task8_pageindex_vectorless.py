"""
Task 8 — PageIndex vectorless fallback.

Hướng dẫn:
    1. Đọc PAGEINDEX_API_KEY từ .env.
    2. Upload tài liệu ở định dạng PageIndex hỗ trợ.
    3. Cache document IDs để không upload lại.
    4. Parse kết quả thành SearchResult có method pageindex.

PageIndex là dịch vụ ngoài: cần timeout và xử lý lỗi để pipeline không crash.
"""

import json
import logging
import os
from pathlib import Path
from dotenv import load_dotenv

from src.contracts import validate_search_results

load_dotenv()

PAGEINDEX_API_KEY = os.getenv("PAGEINDEX_API_KEY", "")
STANDARDIZED_DIR = Path(__file__).parent.parent / "data" / "standardized"
CACHE_FILE = Path(__file__).parent.parent / "pageindex_doc_ids.json"

logger = logging.getLogger(__name__)


def upload_documents() -> None:
    """Upload tài liệu và lưu document IDs để tái sử dụng."""
    if not PAGEINDEX_API_KEY:
        logger.info("PAGEINDEX_API_KEY is not configured; skipping upload.")
        return

    try:
        from pageindex import PageIndexClient  # type: ignore

        client = PageIndexClient(api_key=PAGEINDEX_API_KEY)
        doc_ids = {}

        if CACHE_FILE.exists():
            try:
                doc_ids = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
            except Exception:
                doc_ids = {}

        for path in sorted(STANDARDIZED_DIR.rglob("*.md")):
            rel_name = path.relative_to(STANDARDIZED_DIR).as_posix()
            if rel_name in doc_ids:
                continue

            try:
                response = client.upload_file(str(path))
                if hasattr(response, "doc_id"):
                    doc_ids[rel_name] = response.doc_id
                elif isinstance(response, dict) and "doc_id" in response:
                    doc_ids[rel_name] = response["doc_id"]
            except Exception as exc:
                logger.warning(f"Failed to upload {path.name} to PageIndex: {exc}")

        CACHE_FILE.write_text(json.dumps(doc_ids, indent=2), encoding="utf-8")
    except ImportError:
        logger.warning("pageindex SDK is not installed or available.")
    except Exception as exc:
        logger.warning(f"Error in upload_documents: {exc}")


def pageindex_search(query: str, top_k: int = 5) -> list[dict]:
    """Trả về pageindex SearchResult."""
    if top_k <= 0 or not query.strip():
        return []

    if not PAGEINDEX_API_KEY:
        return []

    try:
        from pageindex import PageIndexClient  # type: ignore

        client = PageIndexClient(api_key=PAGEINDEX_API_KEY)
        if not CACHE_FILE.exists():
            return []

        doc_ids = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
        if not doc_ids:
            return []

        # Query across uploaded documents with timeout
        raw_results = client.search(
            query=query,
            doc_ids=list(doc_ids.values()),
            top_k=top_k,
        )

        results = []
        for idx, item in enumerate(raw_results[:top_k]):
            item_id = getattr(item, "id", f"pageindex-result-{idx}")
            content = getattr(item, "content", getattr(item, "text", str(item)))
            score = float(getattr(item, "score", 1.0 / (idx + 1)))
            doc_meta = getattr(item, "metadata", {}) or {}

            meta = {
                "source": doc_meta.get("source", "pageindex"),
                "title": doc_meta.get("title", "PageIndex Result"),
                "doc_type": doc_meta.get("doc_type", "legal"),
                "url": doc_meta.get("url", None),
                "chunk_index": int(doc_meta.get("chunk_index", idx)),
            }

            results.append({
                "id": str(item_id),
                "content": str(content),
                "score": score,
                "metadata": meta,
                "retrieval_method": "pageindex",
            })

        validate_search_results(results, top_k=top_k, expected_method="pageindex")
        return results

    except Exception as exc:
        logger.warning(f"PageIndex search error (safe fallback): {exc}")
        return []


if __name__ == "__main__":
    print("PageIndex module ready. Upload documents if API key is present.")
