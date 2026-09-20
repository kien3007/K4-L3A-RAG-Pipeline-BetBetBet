"""
Task 2 — Crawl bài viết/thông báo.

Hướng dẫn:
    1. Điền tối thiểu 5 URL công khai vào ARTICLE_URLS.
    2. Crawl từng URL bằng Crawl4AI.
    3. Lưu mỗi bài thành một JSON trong data/landing/news/.
    4. Giữ đủ url, title, date_crawled và content_markdown.

Cài browser trước khi chạy:
    python -m playwright install chromium
    
-> Dùng Firecrawl or bất cứ công cụ nào bạn quen    
"""

import asyncio
import json
from pathlib import Path


from datetime import datetime
import bs4
import markdownify
import requests

DATA_DIR = Path(__file__).parent.parent / "data" / "landing" / "news"

ARTICLE_URLS = [
    "https://thanhnien.vn/tong-bi-thu-chu-tich-nuoc-to-lam-len-duong-cong-tac-tai-my-va-tham-canada-185260920103639813.htm",
    "https://thanhnien.vn/long-kinh-yeu-bac-phai-duoc-the-hien-bang-su-tan-tam-phuc-vu-nhan-dan-185260919212555046.htm",
    "https://thanhnien.vn/co-hoi-thuc-day-quan-he-viet-my-185260919232916729.htm",
    "https://thanhnien.vn/truyen-tai-o-cap-cao-nhat-thong-diep-ve-viet-nam-dang-buoc-vao-ky-nguyen-moi-185260919155048452.htm",
    "https://thanhnien.vn/tong-bi-thu-chu-tich-nuoc-to-lam-trao-nghi-quyet-thanh-lap-thanh-pho-bac-ninh-18526091913161782.htm",
]


PLAYWRIGHT_AVAILABLE = True


async def crawl_article(url: str) -> dict:
    """Crawl một bài viết và trích xuất url, title, date_crawled, content_markdown."""
    global PLAYWRIGHT_AVAILABLE
    date_crawled = datetime.now().isoformat()

    # Thử dùng crawl4ai nếu browser đã cài đặt
    if PLAYWRIGHT_AVAILABLE:
        try:
            from crawl4ai import AsyncWebCrawler
            async with AsyncWebCrawler() as crawler:
                result = await crawler.arun(url=url)
                if result.success and result.markdown:
                    title = result.metadata.get("title", "") if result.metadata else ""
                    return {
                        "url": url,
                        "title": title or "Unknown",
                        "date_crawled": date_crawled,
                        "content_markdown": result.markdown.strip(),
                    }
        except Exception:
            PLAYWRIGHT_AVAILABLE = False

    # Trích xuất trực tiếp bằng requests + BeautifulSoup + markdownify
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()

    soup = bs4.BeautifulSoup(response.text, "html.parser")
    title_elem = soup.find("h1", class_="detail-title") or soup.find("h1")
    title = title_elem.get_text(strip=True) if title_elem else (soup.title.string.strip() if soup.title else "Unknown")

    content_div = (
        soup.find("div", class_="detail-cmain")
        or soup.find("div", class_="detail-content")
        or soup.find("div", class_="content")
        or soup.find("body")
    )
    content_markdown = markdownify.markdownify(str(content_div), heading_style="ATX").strip() if content_div else ""

    return {
        "url": url,
        "title": title,
        "date_crawled": date_crawled,
        "content_markdown": content_markdown,
    }


async def crawl_all() -> None:
    """Crawl và lưu từng bài thành một file JSON."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    for index, url in enumerate(ARTICLE_URLS, 1):
        try:
            article = await crawl_article(url)
            output = DATA_DIR / f"article_{index:02d}.json"
            output.write_text(
                json.dumps(article, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            print(f"Saved: {output}")
        except Exception as error:
            print(f"Failed: {url} — {error}")


if __name__ == "__main__":
    asyncio.run(crawl_all())

