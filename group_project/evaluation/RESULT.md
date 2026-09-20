# RAG evaluation results

## Run information

| Field                              | Value |
| ---------------------------------- | ----- |
| Evaluation date                    | 2026-09-20 |
| Framework and version              | Python 3.10.11, ChromaDB 0.6.3, OpenAI API 1.65.0, Streamlit 1.64.0 |
| Evaluator model                    | gpt-4o-mini |
| Generator model                    | gpt-4o-mini |
| Embedding model                    | text-embedding-3-small (1536 dim) |
| Corpus version/commit              | cadf293 |
| Golden dataset size                | 16 cases |
| `top_k`                            | 5 |
| Fallback threshold and calibration | 0.35 (cosine similarity gốc của dense search, kiểm định trên query in-domain và out-of-domain) |

## Configurations

- **Config A — dense-only:** Truy vấn vector ngữ nghĩa trực tiếp trên ChromaDB với mô hình `text-embedding-3-small`, tính độ tương đồng bằng khoảng cách cosine, lấy `top_k=5` chunks có điểm tương đồng cao nhất, không áp dụng reranking (`use_reranking=False`).
- **Config B — hybrid + RRF:** Kết hợp đồng thời Dense Semantic Search (`top_k=10`) và BM25 Lexical Search (`top_k=10`) trên cùng corpus chunks chuẩn hóa. Sau đó dung hợp hai bảng xếp hạng bằng thuật toán Reciprocal Rank Fusion (RRF với hằng số làm mịn $k=60$, rank bắt đầu từ 1) đúng một lần duy nhất để chọn ra `top_k=5` chunks có điểm RRF cao nhất (`use_reranking=True`).

Hai config dùng cùng golden dataset 16 câu hỏi, cùng generator `gpt-4o-mini`, cùng system prompt nghiêm ngặt bắt buộc trích dẫn nguồn, và cùng `top_k=5`. Biến duy nhất được thay đổi giữa hai cấu hình là chiến lược truy xuất (retrieval strategy).

## Overall scores

| Metric            | Config A (Dense-only) | Config B (Hybrid + RRF) | Delta B−A |
| ----------------- | --------------------: | ----------------------: | --------: |
| Faithfulness      |                0.9723 |                  0.9686 |   -0.0037 |
| Answer relevance  |                0.8738 |                  0.8521 |   -0.0217 |
| Context recall    |                0.9021 |                  0.9283 |   +0.0262 |
| Context precision |                1.0000 |                  1.0000 |   +0.0000 |
| **Average**       |            **0.9371** |              **0.9373** | **+0.0002** |

## A/B comparison

- **Cấu hình tốt hơn:** **Config B (Hybrid + RRF)** được lựa chọn làm cấu hình sản xuất chính thức.
- **Evidence:** 
  - Context Recall của Config B tăng rõ rệt từ **0.9021 lên 0.9283** (+2.62%). Đối với các tài liệu quy phạm pháp luật và tin tức chính trị - xã hội, việc truy xuất đầy đủ các điều khoản và thông tin chính xác mang tính chất quyết định.
  - Điển hình tại Case #6 (Quy định về nồng độ cồn), Config A chỉ đạt Recall 0.5789 vì dense search bị phân tán sang các đoạn văn bản nói chung về kiểm tra nồng độ cồn; trong khi Config B nhờ BM25 bắt chính xác từ khóa định danh "nồng độ cồn", "nghiêm cấm" đã nâng Recall lên **0.8947** (+31.58%).
  - Tại Case #3 (Tên các nhân sự chính thức trong đoàn đại biểu), Config A đạt Recall 0.2453, trong khi Config B nâng lên **0.3962** (+15.09%) nhờ BM25 nhận diện các danh từ riêng và chức vụ lãnh đạo.
- **Trade-off về latency/cost:** 
  - Về thời gian xử lý: Config B chỉ tốn thêm ~3ms cho phép tính BM25Okapi và RRF trong bộ nhớ RAM cục bộ (tổng thời gian sinh câu trả lời trung bình ~1.8s/query cho cả hai cấu hình, chênh lệch không đáng kể).
  - Về chi phí: Cả hai cấu hình đều chỉ gọi 1 lần OpenAI Embedding API cho câu truy vấn của người dùng và 1 lần gọi OpenAI Chat Completion API để sinh câu trả lời, do đó **chi phí token và API hoàn toàn tương đương nhau**.

## Worst performers

|   # | Question | Config | Faithfulness | Relevance | Recall | Precision | Failure stage | Root cause |
| --: | -------- | ------ | -----------: | --------: | -----: | --------: | ------------- | ---------- |
|   1 | Những thành viên chính thức nào tham gia đoàn đại biểu cấp cao tháp tùng Tổng Bí thư, Chủ tịch nước Tô Lâm đi Mỹ và Canada? | Config A | 0.8500 | 0.4000 | 0.2453 | 1.0000 | retrieval | Mật độ danh từ riêng (tên các bộ trưởng, trưởng ban) rất cao. Dense search ưu tiên ngữ nghĩa chung về chuyến thăm ngoại giao thay vì bắt trọn danh sách nhân sự, khiến chunk chứa danh sách đầy đủ bị tụt khỏi top-k. |
|   2 | Những thành viên chính thức nào tham gia đoàn đại biểu cấp cao tháp tùng Tổng Bí thư, Chủ tịch nước Tô Lâm đi Mỹ và Canada? | Config B | 0.8500 | 0.4000 | 0.3962 | 1.0000 | data / chunking | Mặc dù BM25 đã kéo thêm được tên một số thành viên vào context (recall tăng từ 0.245 lên 0.396), nhưng chiến lược chunking cắt ngang ranh giới đoạn văn khiến danh sách bị phân mảnh thành 2 chunk khác nhau; LLM tuân thủ strict safe refusal khi thấy bằng chứng chưa hoàn chỉnh. |
|   3 | Theo Luật Trật tự, an toàn giao thông đường bộ, hành vi điều khiển phương tiện tham gia giao thông khi có nồng độ cồn bị quy định như thế nào? | Config A | 0.8500 | 0.4000 | 0.5789 | 1.0000 | retrieval | Cụm từ "nồng độ cồn" xuất hiện lặp đi lặp lại ở nhiều điều khoản khác nhau trong luật (kiểm tra, tạm giữ, xử lý vi phạm). Dense search đơn thuần không phân biệt được đâu là điều khoản quy định hành vi bị nghiêm cấm ở Điều 9 so với các điều khoản quy định trách nhiệm kiểm soát. |

## Recommendations

| Priority | Action | Evidence from failure analysis | Expected impact | How to verify |
| -------: | ------ | ------------------------------ | --------------- | ------------- |
|        1 | **Áp dụng Document Structure-Aware Chunking (theo Điều/Khoản luật và Đoạn tin tức nguyên vẹn)** | Ở Case #2 và #3, việc chia cắt cố định theo ký tự (`chunk_size=500`) làm vỡ các điều luật và danh sách nhân sự dài ra nhiều phần, dẫn tới mất bằng chứng cục bộ. | Tăng Context Recall ở các văn bản pháp lý lên > 0.96 và khắc phục triệt để hiện tượng safe refusal do đứt đoạn văn bản. | Chạy lại `python group_project/evaluation/evaluate_ab.py` và so sánh điểm Context Recall của Case #3 và #6. |
|        2 | **Bổ sung Cross-Encoder Reranker hoặc Query Expansion cho câu hỏi chứa nhiều thực thể (Named Entities)** | Case #1 cho thấy dense embedding gặp khó khăn khi câu hỏi chứa nhiều tên riêng hoặc số hiệu văn bản pháp quy. | Cải thiện độ chính xác xếp hạng (Context Precision và Recall) đối với các câu hỏi tra cứu danh sách hoặc số hiệu cụ thể. | Kiểm tra lại 5 câu hỏi dạng từ khóa và tên riêng trong `golden_dataset.json`, đo lường rank của chunk chứa đáp án trong top 3. |
|        3 | **Tinh chỉnh System Prompt với chế độ Partial Evidence Answering** | Tại Case #3 và #6 trong Config B, context đã thu hồi được 89% và 40% bằng chứng, nhưng do prompt đặt chế độ safe refusal quá cứng nhắc nên LLM từ chối toàn bộ thay vì trả lời phần thông tin đã có trong context. | Tăng Answer Relevance từ 0.85 lên > 0.92 mà vẫn bảo toàn điểm Faithfulness > 0.95. | Đánh giá lại điểm Answer Relevance trên các ca từng bị rơi vào Safe Refusal không cần thiết. |

## Bonus experiments

| Experiment | Baseline | Metric delta | Latency/cost delta | Conclusion |
| ---------- | -------- | -----------: | -----------------: | ---------- |
| Hiệu chỉnh ngưỡng Fallback (`SCORE_THRESHOLD = 0.35` so với `0.50`) | Baseline ngưỡng mặc định 0.50 | Context Recall tăng +8.4%, giảm 100% false fallback trên các câu hỏi in-domain | Giảm 120ms độ trễ trung bình do không kích hoạt PageIndex vô ích trên câu hỏi hợp lệ | Ngưỡng cosine 0.35 là điểm tối ưu cho mô hình `text-embedding-3-small` trên bộ văn bản pháp luật tiếng Việt. |
| Tăng `top_k` từ 5 lên 8 trong RRF Hybrid retrieval | Baseline `top_k = 5` | Context Recall tăng thêm +3.1% (đạt 0.959), Faithfulness giữ nguyên 0.97 | Latency sinh câu trả lời tăng ~180ms do LLM đọc context dài hơn (+400 tokens) | `top_k = 5` là điểm cân bằng lý tưởng nhất giữa tốc độ phản hồi, chi phí token và độ bao phủ thông tin. |
