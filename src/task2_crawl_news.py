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


DATA_DIR = Path(__file__).parent.parent / "data" / "landing" / "news"

ARTICLE_URLS = [
    # TODO: Thêm ít nhất 5 public URL.
    "https://thanhnien.vn/tong-bi-thu-chu-tich-nuoc-to-lam-len-duong-cong-tac-tai-my-va-tham-canada-185260920103639813.htm",
    "https://thanhnien.vn/long-kinh-yeu-bac-phai-duoc-the-hien-bang-su-tan-tam-phuc-vu-nhan-dan-185260919212555046.htm",
    "https://thanhnien.vn/co-hoi-thuc-day-quan-he-viet-my-185260919232916729.htm",
    "https://thanhnien.vn/truyen-tai-o-cap-cao-nhat-thong-diep-ve-viet-nam-dang-buoc-vao-ky-nguyen-moi-185260919155048452.htm",
    "https://thanhnien.vn/tong-bi-thu-chu-tich-nuoc-to-lam-trao-nghi-quyet-thanh-lap-thanh-pho-bac-ninh-18526091913161782.htm"
]


async def crawl_article(url: str) -> dict:
    # TODO: Implement crawling logic.
    #
    from datetime import datetime
    from crawl4ai import AsyncWebCrawler

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url=url)
        return {
            "url": url,
            "title": result.metadata.get("title", "Unknown"),
            "date_crawled": datetime.now().isoformat(),
            "content_markdown": result.markdown,
        }
    raise NotImplementedError("Implement crawl_article")


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
