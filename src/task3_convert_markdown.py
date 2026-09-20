"""
Task 3 — Chuẩn hóa dữ liệu sang Markdown.

Hướng dẫn:
    1. Dùng MarkItDown để convert PDF/DOCX.
    2. Đọc JSON và giữ metadata ở đầu file Markdown.
    3. Giữ cấu trúc thư mục legal/ và news/.
    4. Không tạo file rỗng hoặc file trùng khi chạy lại.

Cài đặt:
    Dependency MarkItDown đã được khai báo trong pyproject.toml.
    
-> Hoặc dùng công cụ nào bạn quen khác Markitdown
"""

import json
from pathlib import Path

try:
    from src.task1_collect_legal_docs import SOURCES as LEGAL_SOURCES
except ImportError:
    LEGAL_SOURCES = {}


LANDING_DIR = Path(__file__).parent.parent / "data" / "landing"
OUTPUT_DIR = Path(__file__).parent.parent / "data" / "standardized"

LEGAL_TITLES = {
    "89-vbhn-vpqh-luat-ngan-sach-nha-nuoc.pdf": "Luật Ngân sách nhà nước (Văn bản hợp nhất 89/VBHN-VPQH)",
    "55-vbhn-vpqh-luat-trat-tu-an-toan-giao-thong-duong-bo.pdf": "Luật Trật tự, an toàn giao thông đường bộ (Văn bản hợp nhất 55/VBHN-VPQH)",
    "72-vbhn-vpqh-luat-giao-duc.pdf": "Luật Giáo dục (Văn bản hợp nhất 72/VBHN-VPQH)",
}


def extract_text_from_pdf(pdf_path: Path) -> str:
    """Trích xuất nội dung văn bản từ file PDF."""
    try:
        import pypdfium2
        doc = pypdfium2.PdfDocument(pdf_path)
        pages_text = []
        for page in doc:
            text = page.get_textpage().get_text_range().strip()
            if text:
                pages_text.append(text)
        return "\n\n".join(pages_text)
    except Exception:
        from markitdown import MarkItDown
        converter = MarkItDown()
        result = converter.convert(str(pdf_path))
        return result.text_content


def convert_legal_docs() -> None:
    """Convert PDF/DOCX vào standardized/legal kèm title và source."""
    legal_dir = LANDING_DIR / "legal"
    output_dir = OUTPUT_DIR / "legal"
    output_dir.mkdir(parents=True, exist_ok=True)

    for path in sorted(legal_dir.iterdir()):
        if path.suffix.lower() in {".pdf", ".doc", ".docx"}:
            text_content = extract_text_from_pdf(path).strip()
            if not text_content:
                continue

            doc_title = LEGAL_TITLES.get(path.name, path.stem.replace("-", " ").title())
            source_url = LEGAL_SOURCES.get(path.name, path.name)

            header = (
                f"# {doc_title}\n\n"
                f"**Source:** {source_url}\n\n"
                f"---\n\n"
            )

            output_file = output_dir / f"{path.stem}.md"
            output_file.write_text(header + text_content, encoding="utf-8")
            print(f"Saved legal markdown: {output_file} ({len(header + text_content):,} chars)")


def convert_news_articles() -> None:
    """Convert JSON vào standardized/news kèm title và metadata."""
    news_dir = LANDING_DIR / "news"
    output_dir = OUTPUT_DIR / "news"
    output_dir.mkdir(parents=True, exist_ok=True)

    for path in sorted(news_dir.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        title = data.get("title", "Untitled").strip()
        url = data.get("url", "").strip()
        date_crawled = data.get("date_crawled", "").strip()
        content = data.get("content_markdown", "").strip()

        header = (
            f"# {title}\n\n"
            f"**Source:** {url}\n\n"
            f"**Crawled:** {date_crawled}\n\n"
            f"---\n\n"
        )

        output_file = output_dir / f"{path.stem}.md"
        output_file.write_text(header + content, encoding="utf-8")
        print(f"Saved news markdown: {output_file} ({len(header + content):,} chars)")


def convert_all() -> None:
    """Convert toàn bộ dữ liệu landing."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    convert_legal_docs()
    convert_news_articles()
    print(f"Saved Markdown to: {OUTPUT_DIR}")


if __name__ == "__main__":
    convert_all()

