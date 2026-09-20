import os
from pathlib import Path
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup

# Khởi tạo thư mục lưu file
DATA_DIR = Path("downloaded_pdfs")
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Danh sách nguồn trang web cần cào
sources = {
    "page_1": "https://example.com/documents",
    # thêm các trang khác vào đây nếu có
}

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# 1. Duyệt qua từng trang web để lấy HTML
for page_name, target_url in sources.items():
    try:
        response = requests.get(target_url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        # 2. Tìm tất cả các thẻ <a> có đuôi .pdf
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if href.lower().endswith(".pdf"):
                full_url = urljoin(target_url, href)
                
                # Lấy tên file gốc từ URL (ví dụ: tailieu.pdf)
                filename = os.path.basename(urlparse(full_url).path)
                file_path = DATA_DIR / filename
                
                # 3. Tải và lưu file PDF
                try:
                    pdf_response = requests.get(full_url, headers=headers, timeout=30)
                    pdf_response.raise_for_status()
                    file_path.write_bytes(pdf_response.content)
                    print(f"Đã tải thành công: {filename}")
                except Exception as err:
                    print(f"Lỗi khi tải {full_url}: {err}")
                    
    except Exception as err:
        print(f"Lỗi khi truy cập trang {target_url}: {err}")