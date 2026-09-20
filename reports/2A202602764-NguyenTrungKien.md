# Individual contribution report

## Thông tin

- Họ và tên: Nguyễn Trung Kiên
- Mã học viên: 2A202602764
- Nhóm: BetBetBet
- Repository/branch: `main`

## Phần việc đã thực hiện

| Module/deliverable | Việc tôi trực tiếp làm | File/commit/PR | Trạng thái |
|---|---|---|---|
| **Task 8: PageIndex Fallback** | Triển khai cơ chế dự phòng không vector PageIndex, bọc khối `try/except` an toàn và xử lý timeout để dịch vụ ngoài không gây crash pipeline | `src/task8_pageindex_vectorless.py` | Done |
| **Task 9: Retrieval Pipeline** | Tích hợp toàn bộ luồng truy xuất: gọi RRF duy nhất 1 lần, so sánh ngưỡng fallback `score_threshold=0.35` với điểm cosine gốc của dense search | `src/task9_retrieval_pipeline.py` | Done |
| **Task 10: Generation có Citation** | Triển khai thuật toán `reorder_for_llm()` (giảm lost-in-the-middle), `format_context()` trích dẫn nguồn `[Document X]`, dispatch OpenAI `gpt-4o-mini`, định nghĩa `SAFE_REFUSAL` | `src/task10_generation.py` | Done |
| **A/B Evaluation & Analysis** | Xây dựng 16 cases trong `golden_dataset.json`, lập trình script `evaluate_ab.py` đo 4 metrics (Faithfulness, Relevance, Recall, Precision), phân tích 3 worst performers và hoàn thiện 100% `RESULT.md` | `group_project/evaluation/` | Done |

## Quyết định kỹ thuật quan trọng

1. **Quyết định:** So sánh ngưỡng fallback trực tiếp với điểm cosine similarity gốc của dense search (`best_dense_score = dense[0]["score"]`) thay vì điểm số sau RRF.  
   **Lý do/evidence:** Điểm RRF được tính bằng tổng nghịch đảo thứ hạng ($\sum \frac{1}{k + rank}$), thường có giá trị rất nhỏ (khoảng $0.015 - 0.035$). Nếu dùng điểm RRF để so với ngưỡng, hệ thống sẽ kích hoạt fallback sai cho mọi truy vấn in-domain. Sử dụng điểm cosine gốc phản ánh trực tiếp mức độ tự tin ngữ nghĩa của mô hình embedding đối với câu hỏi.  
   **Trade-off:** Cần lưu giữ riêng giá trị score gốc từ bước dense retrieval trước khi đưa vào RRF, nhưng đảm bảo pipeline tuân thủ 100% quy tắc rubric của giảng viên.

2. **Quyết định:** Áp dụng kỹ thuật Reordering (đưa các chunk quan trọng nhất về hai đầu ngữ cảnh: vị trí đầu tiên và vị trí cuối cùng) trước khi đưa vào prompt của LLM.  
   **Lý do/evidence:** Hiện tượng "Lost in the middle" khiến các mô hình ngôn ngữ lớn (kể cả GPT-4o-mini) thường ghi nhớ và chú ý tốt nhất vào các đoạn văn ở đầu và cuối context, dễ bỏ qua thông tin nằm ở giữa. Bằng thuật toán đan xen (`front = chunks[::2]`, `back = chunks[1::2]`, `reordered = front + back[::-1]`), các bằng chứng cốt lõi luôn nằm ở vùng chú ý cao nhất của mô hình.  
   **Trade-off:** Mất thêm một bước xử lý mảng $O(N)$ trong bộ nhớ (với $N=5$, thời gian thực thi $< 0.1$ms, hoàn toàn không ảnh hưởng tới latency).

## Kiểm thử và kết quả

- **Test và query đã dùng:**
  - Contract tests: `pytest tests/test_contracts.py -k "test_retrieve or test_reorder or test_generation" -v`
  - Acceptance tests: `pytest tests/test_acceptance.py -v`
  - Script đánh giá tự động: `python group_project/evaluation/evaluate_ab.py`
- **Kết quả trước/sau:**
  - Trước: Module generation và evaluation còn dở dang, thiếu `SAFE_REFUSAL` khiến Streamlit app lỗi import; `golden_dataset.json` và `RESULT.md` trống.
  - Sau: **20/20 bài tests (100%)** đều **PASSED**. Bộ golden dataset đạt 16 cases chuẩn hóa; báo cáo `RESULT.md` được điền đầy đủ không còn chữ TODO nào.
  - Kết quả A/B testing: Config B (Hybrid + RRF) vượt trội với **Context Recall tăng từ 0.9021 lên 0.9283 (+2.62%)**, điểm Faithfulness duy trì mức rất cao **0.9686**.
- **Lỗi đã phát hiện và cách xử lý:**
  - *Lỗi 1:* `ImportError: cannot import name 'SAFE_REFUSAL'` trong `app.py` -> Đã định nghĩa chuẩn xác chuỗi Safe Refusal theo quy định hợp đồng.
  - *Lỗi 2:* Prompt yêu cầu bằng chứng quá ngặt nghèo dẫn tới một số ca bị rơi vào Safe Refusal dù context đã có một phần thông tin -> Đã phân tích chi tiết trong mục Failure Stage và đưa ra khuyến nghị cải tiến cho nhóm.

## Điều còn hạn chế

- **Một hạn chế cụ thể:** Cơ chế Safe Refusal hiện tại mang tính nhị phân (có đủ bằng chứng thì trả lời, thiếu một phần là từ chối hoàn toàn), chưa hỗ trợ phản hồi từng phần kèm ghi chú giới hạn thông tin.
- **Nếu có thêm thời gian:** Tôi sẽ tối ưu prompt để hỗ trợ chế độ **Partial Evidence Answering with Transparency**, cho phép bot tóm tắt những ý đã tìm thấy trong context và nêu rõ phần thông tin còn thiếu thay vì từ chối hoàn toàn.

## Xác nhận đóng góp

Tôi xác nhận nội dung trên phản ánh đúng phần việc của mình và có thể giải thích hoặc chạy lại trong buổi demo.

- Ngày: 20/09/2026
- Tên thành viên: Nguyễn Trung Kiên
