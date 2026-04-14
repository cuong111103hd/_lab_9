# Routing Decisions Log — Lab Day 09

**Nhóm:** Nguyễn Đức Cường - Trần Khánh Bằng - Đỗ Hải Nam 
**Ngày:** 14/04/2026

> **Hướng dẫn:** Ghi lại ít nhất **3 quyết định routing** thực tế từ trace của nhóm.
> Không ghi giả định — phải từ trace thật (`artifacts/traces/`).
> 
> Mỗi entry phải có: task đầu vào → worker được chọn → route_reason → kết quả thực tế.

---

## Routing Decision #1

**Task đầu vào:**
> ERR-403-AUTH là lỗi gì và cách xử lý?

**Worker được chọn:** `human_review` -> `retrieval_worker`  
**Route reason (từ trace):** `unknown error code + risk_high → human review`  
**MCP tools được gọi:** N/A  
**Workers called sequence:** `supervisor -> human_review -> retrieval_worker -> synthesis_worker`

**Kết quả thực tế:**
- final_answer (ngắn): Câu trả lời được tổng hợp từ tài liệu (cụ thể tuỳ hệ thống, nhắm vào việc giải thích auth error).
- confidence: 0.37
- Correct routing? Yes

**Nhận xét:** 
Định tuyến rất chính xác vì hệ thống bắt được từ khóa mã lỗi `ERR-` và yêu cầu sự can thiệp của con người thông qua bước `human_review` trước khi tiến hành tra cứu `retrieval_worker`.

---

## Routing Decision #2

**Task đầu vào:**
> Quy trình xử lý sự cố P1 gồm mấy bước và bước đầu tiên là gì?

**Worker được chọn:** `retrieval_worker`  
**Route reason (từ trace):** `task contains SLA/ticket keywords`  
**MCP tools được gọi:** N/A  
**Workers called sequence:** `supervisor -> retrieval_worker -> synthesis_worker`

**Kết quả thực tế:**
- final_answer (ngắn): Câu trả lời dựa trên nội dung sla_p1_2026.txt.
- confidence: 0.49
- Correct routing? Yes

**Nhận xét:**
Vì câu hỏi chứa từ khoá "P1" thuộc nhóm `retrieval_keywords`, supervisor mặc định gửi query thẳng sang `retrieval_worker` để truy vấn vector search. Đây là bước tối ưu vì câu hỏi mang tính chất tra cứu tài liệu thay vì thao tác policy.

---

## Routing Decision #3

**Task đầu vào:**
> Ticket P1 lúc 2am. Cần cấp Level 2 access tạm thời cho contractor.

**Worker được chọn:** `policy_tool_worker`  
**Route reason (từ trace):** `task contains policy/access keyword | risk_high flagged`  
**MCP tools được gọi:** `check_access_permission`  
**Workers called sequence:** `supervisor -> policy_tool_worker -> synthesis_worker`

**Kết quả thực tế:**
- final_answer (ngắn): Trả lời theo context phân quyền và rule của hệ thống cho contractor lúc khẩn cấp.
- confidence: 0.57
- Correct routing? Yes

**Nhận xét:**
Router nhận diện chính xác các keyword `access` (chuyển sang policy_tool) và `2am` (raise risk_high). Kết quả test chạy mượt mà và confidence thuộc nhóm cao (0.57 so sánh với AVG là 0.513).

---

## Routing Decision #4 (tuỳ chọn — bonus)

**Task đầu vào:**
> _________________

**Worker được chọn:** `___________________`  
**Route reason:** `___________________`

**Nhận xét: Đây là trường hợp routing khó nhất trong lab. Tại sao?**

_________________

---

## Tổng kết

### Routing Distribution

| Worker | Số câu được route | % tổng |
|--------|------------------|--------|
| retrieval_worker | 8 | 50% |
| policy_tool_worker | 8 | 50% |
| human_review | 1 | 6% |

### Routing Accuracy

> Trong số 16 câu nhóm đã chạy, bao nhiêu câu supervisor route đúng?

- Câu route đúng: 16 / 16
- Câu route sai (đã sửa bằng cách nào?): 0
- Câu trigger HITL: 1

### Lesson Learned về Routing

> Quyết định kỹ thuật quan trọng nhất nhóm đưa ra về routing logic là gì?  
> (VD: dùng keyword matching vs LLM classifier, threshold confidence cho HITL, v.v.)

1. Sử dụng Keyword Matching linh hoạt, thiết lập biến cờ (flags) như `risk_high` để linh hoạt thay đổi flow tuỳ theo bối cảnh.
2. Cho phép Route Chaining như việc sau khi qua `human_review` thì quay về `retrieval_worker`.

### Route Reason Quality

> Nhìn lại các `route_reason` trong trace — chúng có đủ thông tin để debug không?  
> Nếu chưa, nhóm sẽ cải tiến format route_reason thế nào?

Có chứa đủ lý do tổng quan để log. Để tốt hơn, ta có thể lưu thêm "confidence of route decision" (đặc biệt khi router được thay thế bằng LLM-based classifier) giúp nhận biết nếu Supervisor không chắc chắn khi chốt route.
