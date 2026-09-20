"""
Task 1 — Thu thập tài liệu chính sách/quy định.

Hướng dẫn:
    1. Chọn chủ đề của nhóm.
    2. Tìm tối thiểu 3 tài liệu PDF/DOCX từ nguồn công khai.
    3. Lưu file gốc vào data/landing/legal/.
    4. Đặt tên không dấu và thể hiện đúng nội dung.

Ví dụ tài liệu: học phí, học bổng, ký túc xá, quy trình đăng ký.
Nếu website chặn crawler, hãy chọn nguồn công khai khác; không vượt WAF.
"""

from pathlib import Path


import requests

DATA_DIR = Path(__file__).parent.parent / "data" / "landing" / "legal"

SOURCES = {
    "89-vbhn-vpqh-luat-ngan-sach-nha-nuoc.pdf": "https://datafiles.chinhphu.vn/cpp/files/vbpq/2026/3/89-vbhn-vpqh.pdf",
    "55-vbhn-vpqh-luat-trat-tu-an-toan-giao-thong-duong-bo.pdf": "https://datafiles.chinhphu.vn/cpp/files/vbpq/2026/3/55-vbhn-vpqh.pdf",
    "72-vbhn-vpqh-luat-giao-duc.pdf": "https://datafiles.chinhphu.vn/cpp/files/vbpq/2026/3/72-vbhn-vpqh.pdf",
}


def setup_directory() -> None:
    """Tạo thư mục lưu tài liệu gốc."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Ready: {DATA_DIR}")


def download_documents() -> None:
    """Tải ít nhất 3 PDF/DOCX từ nguồn công khai."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    for filename, url in SOURCES.items():
        destination = DATA_DIR / filename
        print(f"Downloading: {filename} from {url}...")
        response = requests.get(url, headers=headers, timeout=60)
        response.raise_for_status()

        destination.write_bytes(response.content)
        print(f"Saved: {destination} ({len(response.content):,} bytes)")


if __name__ == "__main__":
    setup_directory()
    download_documents()

