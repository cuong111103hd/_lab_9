# Single Agent vs Multi-Agent Comparison — Lab Day 09

**Nhóm:** Nguyễn Đức Cường - Trần Khánh Bằng - Đỗ Hải Nam 
**Ngày:** 14/04/2026

> **Hướng dẫn:** So sánh Day 08 (single-agent RAG) với Day 09 (supervisor-worker).
> Phải có **số liệu thực tế** từ trace — không ghi ước đoán.
> Chạy cùng test questions cho cả hai nếu có thể.

---

## 1. Metrics Comparison

> Điền vào bảng sau. Lấy số liệu từ:
> - Day 08: chạy `python eval.py` từ Day 08 lab
> - Day 09: chạy `python eval_trace.py` từ lab này

| Metric | Day 08 (Single Agent) | Day 09 (Multi-Agent) | Delta | Ghi chú |
|---|---|---|---|---|
| Avg confidence | ~0.457 | 0.513 | +0.056 | Multi-agent tổng hợp context tốt hơn |
| Avg latency (ms) | ~5000 | 12695 | +7695 | Overhead do routing & tool calls |
| Abstain rate (%) | 15% | 12% | -3% | % câu trả về "không đủ info" |
| Multi-hop accuracy | 60% | 90% | +30% | % câu multi-hop trả lời đúng |
| Routing visibility | ✗ Không có | ✓ Có route_reason | N/A | |
| Debug time (estimate) | 20 phút | 5 phút | -15 phút | Thời gian tìm ra 1 bug |
| Khả năng can thiệp HITL | ✗ Không có | ✓ Có (6% trong trace) | N/A | Mức độ kiểm soát rủi ro bằng human |

> **Lưu ý:** Nếu không có Day 08 kết quả thực tế, ghi "N/A" và giải thích.

---

## 2. Phân tích theo loại câu hỏi

### 2.1 Câu hỏi đơn giản (single-document)

| Nhận xét | Day 08 | Day 09 |
|---|---|---|
| Accuracy | Khá Tốt | Rất Tốt |
| Latency | Nhanh | Trung Bình (do routing) |
| Observation | Truy xuất nhanh vì dùng logic thẳng. | Truy xuất có độ trễ do qua nhiều node Graph nhưng mang lại đáp án tự tin hơn. |

**Kết luận:** Multi-agent có cải thiện không? Tại sao có/không?
Có cải thiện mức độ accuracy và confidence vì Multi-agent có chia node Policy_tool chuyên xử lý các luồng query nội quy. Nhưng đối với câu hỏi đơn giản, nó đem lại overhead thời gian.

### 2.2 Câu hỏi multi-hop (cross-document)

| Nhận xét | Day 08 | Day 09 |
|---|---|---|
| Accuracy | Trung Bình | Cao |
| Routing visible? | ✗ | ✓ |
| Observation | Thường xuyên bỏ sót 1 vế của Multi-hop. | Gọi nhiều tool tuần tự qua LangGraph state, lấy đủ dữ kiện. |

**Kết luận:**
Multi-agent vượt trội vì có thể tách nhỏ tác vụ, cho phép `supervisor` loop qua các worker thích hợp hoặc fetch thêm context trước khi `synthesis`.

### 2.3 Câu hỏi cần abstain

| Nhận xét | Day 08 | Day 09 |
|---|---|---|
| Abstain rate | 15% | 12% |
| Hallucination cases | Nhiều (do LLM tự bịa khi thiếu vector) | Gần như không (do bắt buộc abstain nếu confidence < 0.25) |
| Observation | Dễ lạc đề thay vì abstain | Chặt chẽ nhờ quy tắc abstain rõ ràng tại node Synthesis và logic HITL. |

**Kết luận:**
Kiến trúc Supervisor cho phép kiểm duyệt chặt hơn, dễ dàng raise HITL khi detect những tình huống rủi ro, từ đó giảm hallucination đáng kể.

---

## 3. Debuggability Analysis

> Khi pipeline trả lời sai, mất bao lâu để tìm ra nguyên nhân?

### Day 08 — Debug workflow
```
Khi answer sai → phải đọc toàn bộ RAG pipeline code → tìm lỗi ở indexing/retrieval/generation
Thời gian ước tính: 20 phút
```

### Day 09 — Debug workflow
```
Khi answer sai → đọc trace → xem supervisor_route + route_reason
  → Nếu route sai → sửa supervisor routing logic
  → Nếu retrieval sai → test retrieval_worker độc lập
Thời gian ước tính: 5 phút
```

**Câu cụ thể nhóm đã debug:** _(Mô tả 1 lần debug thực tế trong lab)_
Khi debug cho câu hỏi `[09/15] ERR-403-AUTH`, nhóm đã nhận thấy luồng chạy bị gián đoạn hay không trả về đúng. Nhờ tính năng Log/Trace và file `eval_report.json`,  nhóm thấy `HITL TRIGGERED` hiển thị rõ ràng tại Console theo route `human_review` trước khi gọi `retrieval`, từ đó dễ dàng trace lỗi và verify luồng xử lý tự động của Supervisor đã diễn ra chính xác.

---

## 4. Extensibility Analysis

> Dễ extend thêm capability không?

| Scenario | Day 08 | Day 09 |
|---------|--------|--------|
| Thêm 1 tool/API mới | Phải sửa toàn prompt | Thêm MCP tool + route rule |
| Thêm 1 domain mới | Phải retrain/re-prompt | Thêm 1 worker mới |
| Thay đổi retrieval strategy | Sửa trực tiếp trong pipeline | Sửa retrieval_worker độc lập |
**Nhận xét:**
Vì Supervisor-Worker chia tách rõ constraint và logic (tách rời routing, check policy tools riêng biệt với retrieval), việc bảo trì và mở rộng hệ thống sang scale production lớn là có tính khả thi rất cao so với pipeline monolith ở Day 08.

---

## 5. Cost & Latency Trade-off

> Multi-agent thường tốn nhiều LLM calls hơn. Nhóm đo được gì?

| Scenario | Day 08 calls | Day 09 calls |
| Simple query | 1 LLM call | Khoảng 2 (1 call API nếu worker là LLM, 1 router (nếu dùng router là LLM)) LLM calls |
| Complex query | 1 LLM call | ~3 LLM calls |
| MCP tool call | N/A | Tốn thêm request qua FastAPI/Local MCP Server |

**Nhận xét về cost-benefit:**
Cost đắt hơn 2-3 lần (nếu Router cũng dùng LLM), latency tăng gấp đôi (từ 5000 lên ~12695ms). Tuy nhiên, đổi lại là khả năng Debug và tỷ lệ Chính xác khi giải quyết tác vụ phức tạp/bảo mật tốt hơn nhiều.

---

## 6. Kết luận

> **Multi-agent tốt hơn single agent ở điểm nào?**

1. Khả năng gỡ lỗi, bảo trì qua traces & route. Tùy biến mở rộng bằng cách thêm MCP / worker mới mà không cần đụng vào Core Pipeline.
2. Kiểm soát rủi ro thông qua HITL khi risk level vượt ngưỡng cho phép.

> **Multi-agent kém hơn hoặc không khác biệt ở điểm nào?**

1. Thời gian phản hồi bị chậm đi nhiều (Latency cao hơn) và chi phí API Calls đội lên.

> **Khi nào KHÔNG nên dùng multi-agent?**
Khi mục đích của product chỉ là Search thông tin cơ bản/Q&A thông thường trên tập dataset không có tính bảo mật/tác vụ workflow (Action-based).

> **Nếu tiếp tục phát triển hệ thống này, nhóm sẽ thêm gì?**
Cải thiện Node Router bằng Router LLM nhỏ nhắn giá rẻ hơn (vd. LLaMA 8B / rule-based keyword cache level) để giảm overhead/cost cho các bước định tuyến đơn giản. Thêm hệ thống Cache phân tán.
