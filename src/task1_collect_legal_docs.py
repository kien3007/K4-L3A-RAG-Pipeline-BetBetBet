from pathlib import Path
import requests

DATA_DIR = Path(__file__).parent.parent / "data" / "landing" / "legal"
DATA_DIR.mkdir(parents=True, exist_ok=True)


def setup_directory() -> None:
    """Tạo thư mục lưu tài liệu gốc."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Ready: {DATA_DIR}")


def download_documents() -> None:
    """Tải ít nhất 3 PDF/DOCX từ nguồn công khai."""
    sources = {
        "chinhphu-89.pdf": "https://datafiles.chinhphu.vn/cpp/files/vbpq/2026/3/89-vbhn-vpqh.pdf",
        "chinhphu-55.pdf": "https://datafiles.chinhphu.vn/cpp/files/vbpq/2026/3/55-vbhn-vpqh.pdf",
        "chinhphu-72.pdf": "https://datafiles.chinhphu.vn/cpp/files/vbpq/2026/3/72-vbhn-vpqh.pdf",
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    for filename, file_url in sources.items():
        file_path = DATA_DIR / filename
        try:
            print(f"Đang tải: {filename}...")
            response = requests.get(file_url, headers=headers, timeout=30)
            response.raise_for_status()

            # Ghi trực tiếp dữ liệu nhị phân (bytes) của file PDF
            file_path.write_bytes(response.content)
            print(f"-> Đã tải thành công: {file_path}")

        except Exception as err:
            print(f"Lỗi khi tải {file_url}: {err}")


if __name__ == "__main__":
    setup_directory()
    download_documents()