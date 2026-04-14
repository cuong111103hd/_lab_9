# Báo Cáo Cá Nhân — Lab Day 09: Multi-Agent Orchestration

**Họ và tên:** Nguyễn Đức Cường   
**Vai trò trong nhóm:** Worker Owner (Phụ trách retrieval.py, policy_tool.py, synthesis.py, contracts)  
**Ngày nộp:** 2026-04-14  
**Độ dài yêu cầu:** 500–800 từ

---

## 1. Tôi phụ trách phần nào? (100–150 từ)

Trong dự án này, tôi chịu trách nhiệm chính về việc xây dựng các "Workers" - trái tim thực thi của hệ thống RAG đa tác nhân. Cụ thể, tôi đã thiết kế và triển khai ba module quan trọng nhất:
- **`workers/retrieval.py`:** Chịu trách nhiệm tìm kiếm các đoạn văn bản (chunks) từ cơ sở dữ liệu vector ChromaDB sử dụng mô hình embedding Jina AI.
- **`workers/policy_tool.py`:** Là worker phức tạp nhất, chịu trách nhiệm phân tích các quy tắc chính sách, nhận diện các ngoại lệ (Flash Sale, Digital Products) và tích hợp các công cụ MCP để lấy dữ liệu thời gian thực.
- **`workers/synthesis.py`:** Tổng hợp câu trả lời cuối cùng dựa trên bằng chứng thu thập được, đảm bảo tính trung thực (groundedness) và trích dẫn nguồn đầy đủ.
- **`contracts/worker_contracts.yaml`:** Tôi đã xây dựng và duy trì bản "hợp đồng" dữ liệu này để đảm bảo sự phối hợp trơn tru giữa Supervisor và các Workers.

---

## 2. Tôi đã ra một quyết định kỹ thuật gì? (150–200 từ)

**Quyết định:** Sử dụng mô hình **Hybrid Policy Analysis** (Kết hợp Rule-based và LLM-based) trong `policy_tool.py`.

**Lý do:**
Ban đầu, tôi dự định chỉ dùng LLM để kiểm tra chính sách. Tuy nhiên, qua thử nghiệm, tôi nhận thấy LLM đôi khi bỏ lỡ các chi tiết nhỏ nhưng quan trọng như từ khóa "Flash Sale" hoặc "kỹ thuật số" dẫn đến việc cho phép hoàn tiền sai quy định. Tôi quyết định triển khai một lớp **Rule-based** bằng regex/keyword matching để xử lý các "ngoại lệ cứng" trước. Sau đó, LLM mới được gọi để phân tích ngữ cảnh phức tạp hơn (ví dụ: lý do sản phẩm lỗi).

**Trade-off đã chấp nhận:**
Việc này làm code của `policy_tool.py` dài hơn và cần bảo trì danh sách từ khóa thủ công, nhưng bù lại nó mang lại độ chính xác gần như 100% cho các trường hợp ngoại lệ phổ biến, giúp giảm thiểu rủi ro tài chính cho doanh nghiệp.

**Bằng chứng từ code:**
```python
# Rule-based check (Ưu tiên cao nhất)
if "flash sale" in task_lower or "flash sale" in context_text:
    exceptions_found.append({
        "type": "flash_sale_exception",
        "rule": "Đơn hàng Flash Sale không được hoàn tiền (Điều 3, chính sách v4)."
    })
```

---

## 3. Tôi đã sửa một lỗi gì? (150–200 từ)

**Lỗi:** **ChromaDB Path Mismatch (Lỗi sai đường dẫn cơ sở dữ liệu)**

**Symptom:**
Khi chạy `graph.py` từ thư mục gốc, hệ thống hoạt động tốt. Tuy nhiên, khi tôi chạy test độc lập cho retrieval worker (`python retrieval.py`) bên trong thư mục `workers/`, worker luôn trả về `0 chunks` mặc dù đã đánh index thành công.

**Root cause:**
Trong code ban đầu, tôi dùng đường dẫn tương đối `path="./chroma_db"`. Khi chạy từ thư mục `workers/`, script sẽ tìm DB tại `workers/chroma_db` - một thư mục không hề tồn tại dữ liệu. Đây là lỗi phổ biến liên quan đến môi trường thực thi (Execution Context).

**Cách sửa:**
Tôi đã sử dụng thư viện `pathlib` để xác định đường dẫn tuyệt đối dựa trên vị trí của file script:
```python
# Sửa từ đường dẫn tương đối sang tuyệt đối căn cứ vào vị trí file
DB_PATH = Path(__file__).parent.parent / "chroma_db"
```

**Bằng chứng trước/sau:**
- Trước khi sửa: `Query: 'hoàn tiền' -> Retrieved: 0 chunks (Confidence 0.1)`
- Sau khi sửa: `Query: 'hoàn tiền' -> Retrieved: 3 chunks from policy_refund_v4.txt (Confidence 0.9)`

---

## 4. Tôi tự đánh giá đóng góp của mình (100–150 từ)

**Tôi làm tốt nhất ở điểm nào?**
Tôi đã thiết kế được một hệ thống Worker rất "chặt chẽ" về mặt dữ liệu. Nhờ vào việc định nghĩa Contract kĩ lưỡng, các worker của tôi hiếm khi gặp lỗi mismatch type khi tích hợp vào Graph chung.

**Tôi làm chưa tốt hoặc còn yếu ở điểm nào?**
Khả năng xử lý **Temporal Scoping** (so sánh ngày tháng) vẫn còn thủ công qua từ khóa thay vì dùng logic date-time parser chuyên nghiệp.

**Nhóm phụ thuộc vào tôi ở đâu?**
Toàn bộ logic nghiệp vụ (IT Helpdesk, HR, Refund) nằm trong các Worker tôi phụ trách. Nếu tôi không hoàn thành đúng hạn, Supervisor sẽ không có ai để điều hướng và hệ thống sẽ chỉ là một cái khung rỗng.

**Phần tôi phụ thuộc vào thành viên khác:**
Tôi phụ thuộc rất lớn vào **Supervisor Owner** để đảm bảo `AgentState` được truyền đi đúng cách. Nếu Supervisor không gán đúng `supervisor_route`, worker của tôi sẽ không bao giờ được đánh thức để thực thi nhiệm vụ.

---

## 5. Nếu có thêm 2 giờ, tôi sẽ làm gì? (50–100 từ)

Tôi sẽ thử triển khai **Reranker** trong `retrieval_worker` sử dụng mô hình của Jina AI. Hiện tại chúng tôi chỉ dùng Dense Retrieval. Việc thêm Reranker cho top-10 kết quả đầu tiên chắc chắn sẽ giúp Synthesis Worker có context chất lượng hơn, từ đó tăng độ chính xác cho các câu hỏi multi-hop như câu **q15**.

---
*Lưu file này với tên: `reports/individual/2A202600147-NguyenDucCuong.md`*
