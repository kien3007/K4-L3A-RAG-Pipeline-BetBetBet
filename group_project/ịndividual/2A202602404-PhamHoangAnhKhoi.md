# Individual contribution report

## Thông tin

- Họ và tên: Phạm Hoàng Anh Khôi
- Mã học viên: 2A202602404
- Nhóm: BetBetBet
- Repository/branch: `2-Feat-task4-5-6-7-8-9-10`

## Phần việc đã thực hiện

| Module/deliverable | Việc tôi trực tiếp làm | File/commit/PR | Trạng thái |
|---|---|---|---|
| **Task 4: Chunking, Embedding & Indexing** | Xây dựng pipeline load Markdown chuẩn hóa, phân đoạn bằng `RecursiveCharacterTextSplitter` (size 500, overlap 50), tích hợp OpenAI API `text-embedding-3-small` (1536 dim) theo batch 128, cấu hình ChromaDB cosine space, xử lý làm sạch metadata tương thích Rust backend | `src/task4_chunking_indexing.py` | Done |
| **Task 5: Dense Semantic Search** | Triển khai tìm kiếm vector tương đồng ngữ nghĩa qua ChromaDB, chuyển đổi khoảng cách cosine $d$ sang similarity score $\max(0, 1-d)$, định dạng chuẩn `SearchResult` (`dense`) | `src/task5_semantic_search.py` | Done |
| **Task 6: Lexical Search (BM25)** | Triển khai BM25Okapi trên cùng corpus chunks của Task 4, tùy biến `RobustBM25Okapi` với IDF sàn dương theo chuẩn Lucene (tránh lỗi chia mẫu nhỏ), thiết lập cơ chế caching index trong RAM | `src/task6_lexical_search.py` | Done |
| **Task 7: Reciprocal Rank Fusion (RRF)** | Xây dựng thuật toán RRF $k=60$ dung hợp bảng xếp hạng dense và lexical, khử trùng lặp ID, gán nhãn `hybrid` và sắp xếp giảm dần | `src/task7_reranking.py` | Done |

## Quyết định kỹ thuật quan trọng

1. **Quyết định:** Sử dụng OpenAI `text-embedding-3-small` (1536 chiều) kết hợp xử lý tương thích metadata trong ChromaDB thay vì mô hình local SentenceTransformers.  
   **Lý do/evidence:** Mô hình OpenAI cho chất lượng biểu diễn ngữ nghĩa tiếng Việt vượt trội, thời gian nhúng toàn bộ 1046 chunks chỉ mất ~8 giây. Đồng thời, backend Rust của ChromaDB không chấp nhận giá trị `None` trong metadata, nên tôi đã tiền xử lý chuyển `url: None` thành chuỗi rỗng `""` khi upsert để tránh crash hệ thống.  
   **Trade-off:** Phụ thuộc vào kết nối mạng và OpenAI API key, nhưng bù lại không tiêu tốn RAM/GPU cục bộ và đảm bảo độ chính xác ngữ nghĩa cao.

2. **Quyết định:** Thiết kế lớp `RobustBM25Okapi` kế thừa `BM25Okapi` với cơ chế tính IDF sàn dương (theo công thức Lucene: $\ln(1 + \frac{N - n + 0.5}{n + 0.5})$).  
   **Lý do/evidence:** Công thức chuẩn của thư viện `rank_bm25` tính IDF bị bằng 0 hoặc âm khi từ khóa xuất hiện ở 50% số văn bản (đặc biệt trong các tập test nhỏ như unit test 2 documents). Bằng việc điều chỉnh sàn IDF theo chuẩn Lucene, các từ khóa trong câu hỏi luôn có điểm số phân biệt dương, giúp bài test contract và truy vấn thực tế hoạt động nhất quán 100%.  
   **Trade-off:** Điểm số BM25 có độ lệch nhỏ so với ATIRE BM25 gốc, nhưng vì pipeline sử dụng RRF (dựa trên thứ tự xếp hạng chứ không cộng trực tiếp điểm số) nên hoàn toàn không ảnh hưởng tiêu cực đến kết quả dung hợp cuối cùng.

## Kiểm thử và kết quả

- **Test và query đã dùng:**
  - Chạy toàn bộ test suite: `pytest tests/test_contracts.py -k "test_chunk_documents or test_semantic_search or test_lexical_search or test_rrf" -v`
  - Thử nghiệm truy vấn thực tế: *"Quy định về bảo đảm an toàn giao thông đường bộ"* và *"Luật Ngân sách nhà nước về các khoản thu chi"*.
- **Kết quả trước/sau:**
  - Trước: Module chưa triển khai, test báo `NotImplementedError`, BM25 báo lỗi điểm 0 trên tập test mẫu nhỏ.
  - Sau: Toàn bộ các test hợp đồng của Task 4, 5, 6, 7 đều **PASSED (100%)**. ChromaDB lưu trữ thành công **1046 chunks** với metric `cosine`.
- **Lỗi đã phát hiện và cách xử lý:**
  - *Lỗi 1:* `TypeError: argument 'metadatas': Cannot convert Python object to MetadataValue` từ ChromaDB khi có `url: None` -> Đã chuẩn hóa chuyển đổi thành `""` trước khi đưa vào ChromaDB và khôi phục khi query.
  - *Lỗi 2:* `IndexError` trong `test_lexical_search` do BM25Okapi tính IDF=0 với corpus 2 phần tử -> Đã giải quyết triệt để bằng `RobustBM25Okapi`.

## Điều còn hạn chế

- **Một hạn chế cụ thể:** Chiến lược chunking theo số ký tự cố định (`chunk_size=500`) đôi khi cắt ngang giữa một điều luật hoặc danh sách nhân sự dài, làm giảm tính toàn vẹn của bằng chứng ngữ cảnh.
- **Nếu có thêm thời gian:** Tôi sẽ triển khai cơ chế **Structure-Aware Chunking** (chia theo từng Điều/Khoản luật và theo từng đoạn văn bản nguyên vẹn của bài báo) để giữ trọn vẹn ngữ nghĩa pháp lý.

## Xác nhận đóng góp

Tôi xác nhận nội dung trên phản ánh đúng phần việc của mình và có thể giải thích hoặc chạy lại trong buổi demo.

- Ngày: 20/09/2026
- Tên thành viên: Phạm Hoàng Anh Khôi
