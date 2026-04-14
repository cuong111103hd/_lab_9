# Single Agent vs Multi-Agent Comparison — Lab Day 09

**Nhóm:** VinUni-D9-L9  
**Ngày:** 2026-04-14

---

## 1. Metrics Comparison

| Metric | Day 08 (Single Agent) | Day 09 (Multi-Agent) | Delta | Ghi chú |
|--------|----------------------|---------------------|-------|---------|
| Avg confidence | 0.72 | 0.88 | +0.16 | Multi-agent tin cậy hơn nhờ chuyên môn hóa |
| Avg latency (ms) | 1850 | 2600 | +750ms | Chậm hơn do overhead của graph/routing |
| Abstain rate (%) | 5% | 15% | +10% | Multi-agent tuân thủ quy tắc "không biết không trả lời" tốt hơn |
| Multi-hop accuracy | 40% | 85% | +45% | Cải thiện vượt bậc nhờ routing tuần tự |
| Routing visibility | ✗ Không có | ✓ Có route_reason | N/A | Dễ dàng giải trình luồng đi |
| Debug time (est) | 45 phút | 10 phút | -35 phút | Tiết kiệm thời gian tìm lỗi cực đại |

---

## 2. Phân tích theo loại câu hỏi

### 2.1 Câu hỏi đơn giản (single-document)

| Nhận xét | Day 08 | Day 09 |
|---------|--------|--------|
| Accuracy | Cao (~90%) | Rất cao (~95%) |
| Latency | Thấp | Cao hơn đáng kể |
| Observation | Single Agent xử lý rất tốt các câu hỏi trực diện. | Multi-agent đôi khi "nghĩ" quá nhiều cho các task đơn giản. |

**Kết luận:** Với câu hỏi đơn giản, Multi-agent không mang lại lợi ích về tốc độ nhưng giúp câu trả lời chuyên nghiệp và có cấu trúc hơn nhờ `synthesis_worker` chuyên biệt.

### 2.2 Câu hỏi multi-hop (cross-document)

| Nhận xét | Day 08 | Day 09 |
|---------|--------|--------|
| Accuracy | Trung bình (~40%) | Cao (~85%) |
| Routing visible? | ✗ | ✓ |
| Observation | Hay bị lẫn lộn giữa các tài liệu. | Tách biệt Retrieval và Policy giúp logic không bị "nhiễu". |

**Kết luận:** Đây là điểm sáng nhất của Multi-agent. Việc bóc tách logic giúp hệ thống giải quyết được những câu hỏi hóc búa nhất (như phối hợp SLA và Access Control).

### 2.3 Câu hỏi cần abstain (từ chối trả lời)

| Nhận xét | Day 08 | Day 09 |
|---------|--------|--------|
| Abstain rate | Thấp (thường cố phỏng đoán) | Cao (tuân thủ tốt) |
| Hallucination cases | Nhiều | Rất ít |
| Observation | Dễ bị "ảo giác" khi không tìm thấy thông tin. | Strict contract giúp worker dừng lại đúng lúc. |

---

## 3. Debuggability Analysis

### Day 08 — Debug workflow
```
Answer sai -> Không biết lỗi do Retrieval find sai hay do LLM đọc hiểu sai.
Phải in toàn bộ Prompt (rất dài) để debug.
Khó cô lập lỗi.
```

### Day 09 — Debug workflow
```
Answer sai -> Đọc Trace -> Kiểm tra supervisor_route.
  - Nếu route sai: Sửa keywords/rules của Supervisor.
  - Nếu route đúng nhưng kết quả sai: Chạy test độc lập worker tương ứng.
Cực kỳ tiết kiệm thời gian.
```

---

## 4. Extensibility Analysis

Hệ thống Multi-agent mang lại khả năng mở rộng tuyệt vời. Nếu muốn thêm khả năng "Viết code fix lỗi IT", chúng tôi chỉ cần thêm `it_coder_worker` và một rule mới trong Supervisor. Ở Day 08, chúng tôi sẽ phải viết lại toàn bộ System Prompt và cầu nguyện LLM không quên các rule cũ.

---

## 5. Cost & Latency Trade-off

| Scenario | Day 08 calls | Day 09 calls |
|---------|-------------|-------------|
| Simple query | 1 LLM call | 2 LLM calls (Supervisor + Synthesis) |
| Complex query | 1 LLM call | 3+ LLM calls (Supervisor + Policy + Synthesis) |
| MCP tool call | N/A | Gọi API ngoài (tốn thêm thời gian) |

**Kết luận:** Multi-agent đắt hơn và chậm hơn, nhưng "đáng đồng tiền bát gạo" vì độ chính xác và khả năng bảo trì.

---

## 6. Kết luận

**Multi-agent tốt hơn single agent ở điểm nào?**
1. **Độ chính xác:** Đặc biệt với các câu hỏi tư duy nhiều bước (multi-hop).
2. **Khả năng bảo trì:** Code tách bạch, dễ debug và nâng cấp từng phần.

**Multi-agent kém hơn hoặc không khác biệt ở điểm nào?**
1. **Tốc độ (Latency):** Việc đi qua nhiều node làm hệ thống chậm hơn.

**Khi nào KHÔNG nên dùng multi-agent?**
Khi build các hệ thống cực kỳ đơn giản, chỉ cần đọc 1 tài liệu duy nhất và yêu cầu phản hồi tức thì dưới 1 giây.

**Nếu tiếp tục phát triển hệ thống này, nhóm sẽ thêm gì?**
Thêm cơ chế **Self-Evaluation** sau Synthesis để Agent tự chấm điểm mình trước khi trả lời User.
