# Individual contribution report

- Họ và tên: Bùi Đăng Khoa
- Mã học viên: 2A202602617
- Nhóm: BetBetBet
- Repository/branch: khoadev

---

## Phần việc đã thực hiện

| Module/deliverable | Việc tôi trực tiếp làm | File/commit/PR | Trạng thái |
|---|---|---|---|
| **Task 1: Thu thập tài liệu pháp luật** | Viết script tải tự động 3 tài liệu PDF quy phạm pháp luật (Luật Ngân sách nhà nước, Luật TTAT Giao thông đường bộ, Luật Giáo dục), kiểm tra HTTP status và lưu vào landing storage. | `src/task1_collect_legal_docs.py`, `data/landing/legal/` | Done |
| **Task 2: Thu thập tin tức thời sự** | Xây dựng pipeline crawl 5 bài viết thời sự chính trị xã hội, bóc tách cấu trúc HTML và trích xuất `url`, `title`, `date_crawled`, `content_markdown`. | `src/task2_crawl_news.py`, `data/landing/news/*.json` | Done |
| **Task 3: Chuẩn hóa Markdown** | Trích xuất văn bản từ PDF qua `pypdfium2`, làm sạch khoảng trắng, chuẩn hóa header Markdown có nhúng sẵn Title và Source URL để bảo toàn trích dẫn nguồn. | `src/task3_convert_markdown.py`, `data/standardized/` | Done |
| **Giao diện người dùng (UI/UX)** | Xây dựng giao diện Chatbot Streamlit hiện đại: bố cục User bên phải - Agent bên trái, streaming chữ, trích dẫn `[1] [2]` bấm mở link gốc `target="_blank"`, trạng thái suy nghĩ tự nhiên với 3 chấm nhịp nhàng, tối ưu hiển thị độ tin cậy. | `app.py`, `.streamlit/config.toml` | Done |

## Quyết định kỹ thuật quan trọng

1. **Quyết định:** Chuẩn hóa Header Markdown (`# Title` và `**Source:** <url>`) trực tiếp từ Task 3 thay vì chỉ lưu văn bản thô.  
   **Lý do/evidence:** Đảm bảo toàn vẹn tính truy xuất nguồn gốc (data provenance) xuyên suốt từ dữ liệu thô đến khâu chunking (Task 4) và generation (Task 10), giúp LLM trích dẫn chính xác URL nguồn cho từng khẳng định.  
   **Trade-off:** Phải xây dựng logic ánh xạ metadata và tiền xử lý tiêu đề có kiểm soát cho từng file PDF thay vì sử dụng parser tự động hoàn toàn.

2. **Quyết định:** Tách biệt bố cục vật lý User (phải) - Agent (trái) và link hóa trích dẫn `[1]`, `[2]` thành link click mở tab mới `target="_blank"`.  
   **Lý do/evidence:** Tạo trải nghiệm hội thoại trực quan tương tự các nền tảng lớn (ChatGPT/Gemini); loại bỏ các thông số kỹ thuật nội bộ (như điểm RRF 0.0161) gây hiểu lầm cho người dùng cuối.  
   **Trade-off:** Phải tùy biến CSS và cấu trúc lưới chuyên biệt thay vì phụ thuộc hoàn toàn vào component mặc định của Streamlit.

## Kiểm thử và kết quả

- Test hoặc query tôi đã dùng:
  - Chạy toàn bộ test hợp đồng: `pytest tests/test_contracts.py` (đạt **15/15 test passed 100%**).
  - Kiểm tra trực tiếp qua Streamlit với 4 chủ đề câu hỏi mẫu: Mục tiêu giáo dục, An toàn giao thông, Dự toán ngân sách, Tin tức đối ngoại.
- Kết quả trước/sau nếu có:
  - Trước: Chưa có dữ liệu chuẩn hóa, giao diện chat dồn vào giữa và hiển thị điểm kỹ thuật `0.0161` gây hiểu lầm.
  - Sau: Dữ liệu được trích xuất sạch sẽ; giao diện phân tách 2 bên trực quan, click `[1]`, `[2]` mở ngay văn bản PDF/bài báo gốc.
- Lỗi đã phát hiện và cách xử lý:
  - Thẻ gợi ý bị ẩn sau câu hỏi đầu tiên -> Sửa lại cấu trúc hiển thị cố định ở đầu trang để người dùng cuộn lên xem lại bất kỳ lúc nào.
  - File watcher của Streamlit in warning do gói `transformers` quét thiếu `torchvision` -> Khắc phục bằng file cấu hình `.streamlit/config.toml` với `fileWatcherType = "poll"`.

## Điều còn hạn chế

- Một hạn chế cụ thể của phần tôi làm: Thư viện `pypdfium2` trích xuất text thuần túy hiệu quả nhưng chưa giữ được cấu trúc bảng biểu phức tạp trong Luật Ngân sách nhà nước.
- Nếu có thêm thời gian, thay đổi đầu tiên tôi sẽ thực hiện: Tích hợp bộ parser nhận diện layout (Layout-aware PDF parsing như PyMuPDF/Docling) để trích xuất nguyên vẹn các bảng biểu ngân sách và bổ sung Dark Mode cho UI.

## Xác nhận đóng góp

Tôi xác nhận nội dung trên phản ánh đúng phần việc của mình và có thể giải thích hoặc chạy lại trong buổi demo.

- Ngày: 20/09/2026
- Tên thành viên: Bùi Đăng Khoa
