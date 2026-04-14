# Routing Decisions Log — Lab Day 09

**Nhóm:** VinUni-D9-L9  
**Ngày:** 2026-04-14

---

## Routing Decision #1

**Task đầu vào:**
> SLA xử lý ticket P1 là bao lâu?

**Worker được chọn:** `retrieval_worker`  
**Route reason (từ trace):** `task contains P1 SLA keyword`  
**MCP tools được gọi:** `search_kb`  
**Workers called sequence:** `supervisor -> retrieval_worker -> synthesis_worker`

**Kết quả thực tế:**
- final_answer (ngắn): SLA phản hồi ban đầu 15 phút và thời gian xử lý là 4 giờ [sla_p1_2026.txt].
- confidence: 0.95
- Correct routing? Yes

**Nhận xét:** Routing chính xác vì câu hỏi thuần túy tra cứu thông tin (SLA).

---

## Routing Decision #2

**Task đầu vào:**
> Khách hàng Flash Sale yêu cầu hoàn tiền ngày 05/02/2026. Có được không?

**Worker được chọn:** `policy_tool_worker`  
**Route reason (từ trace):** `task contains policy/refund keyword | needs_tool flagged`  
**MCP tools được gọi:** `search_kb`  
**Workers called sequence:** `supervisor -> retrieval_worker -> policy_tool_worker -> synthesis_worker`

**Kết quả thực tế:**
- final_answer (ngắn): Không được hoàn tiền vì đơn hàng Flash Sale nằm trong danh mục ngoại lệ (Điều 3 chính sách v4).
- confidence: 0.98
- Correct routing? Yes

**Nhận xét:** Supervisor nhận diện đúng context cần kiểm tra policy. Luồng đi qua Retrieval trước để lấy context "Điều 3" là rất hợp lý.

---

## Routing Decision #3

**Task đầu vào:**
> Cấp quyền Level 3 cho contractor đang fix P1 khẩn cấp.

**Worker được chọn:** `policy_tool_worker`  
**Route reason (từ trace):** `task contains access/level 3 keyword | risk_high flagged`  
**MCP tools được gọi:** `check_access_permission`, `get_ticket_info`  
**Workers called sequence:** `supervisor -> retrieval_worker -> policy_tool_worker -> synthesis_worker`

**Kết quả thực tế:**
- final_answer (ngắn): Level 3 không có emergency bypass. Cần 3 bên phê duyệt: Line Manager, IT Admin, và IT Security.
- confidence: 0.92
- Correct routing? Yes

**Nhận xét:** Một ca routing khó vì vừa có P1 (IT) vừa có Level 3 (Policy). Supervisor đã chọn Policy là đúng vì quy tắc cấp quyền là rào cản quan trọng nhất cần kiểm tra.

---

## Tổng kết

### Routing Distribution

| Worker | Số câu được route | % tổng |
|--------|------------------|--------|
| retrieval_worker | 9 | 60% |
| policy_tool_worker | 5 | 33% |
| human_review | 1 | 7% |

### Routing Accuracy

- Câu route đúng: 14 / 15
- Câu route sai (đã sửa bằng cách nào?): 1 (đã thêm keyword "access" vào logic supervisor)
- Câu trigger HITL: 1 (câu hỏi về mã lỗi lạ ERR-403)

### Lesson Learned về Routing

1. **Sequential over Parallel:** Việc cho phép `retrieval` chạy trước để cung cấp context cho `policy_worker` giúp tăng độ chính xác lên rất nhiều so với việc để policy worker tự tìm kiếm.
2. **Keyword is often enough:** Với tập data nội bộ nhỏ, keyword matching cho kết quả tin cậy và latency thấp hơn nhiều so với dùng LLM Classifier.

### Route Reason Quality

Các `route_reason` hiện tại đã đủ tốt để debug. Tuy nhiên, trong tương lai chúng tôi sẽ bổ sung thêm "Keyword triggered" cụ thể (ví dụ: `reason: refund keyword found`) để biết chính xác tại sao supervisor lại chọn worker đó.
