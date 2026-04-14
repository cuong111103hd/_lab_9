# Báo Cáo Nhóm — Lab Day 09: Multi-Agent Orchestration

**Tên nhóm:** VinUni-D9-L9  
**Thành viên:**
| Tên | Vai trò | Email |
|-----|---------|-------|
| Supervisor Owner | Supervisor Owner | vinuni.supervisor@example.com |
| Worker Owner | Worker Owner | vinuni.worker@example.com |
| MCP Owner | MCP Owner | vinuni.mcp@example.com |
| Trace & Docs Owner | Trace & Docs Owner | vinuni.docs@example.com |

**Ngày nộp:** 2026-04-14  
**Repo:** VinUni-AICB-P1/D9-Multi-Agent  
**Độ dài khuyến nghị:** 600–1000 từ

---

## 1. Kiến trúc nhóm đã xây dựng (150–200 từ)

Hệ thống của nhóm chúng tôi được xây dựng trên mô hình **Supervisor-Worker** sử dụng framework **LangGraph**. Kiến trúc này cho phép tách biệt rõ ràng các trách nhiệm chuyên môn giữa các tác nhân (Agents). Trung tâm của hệ thống là `supervisor_node`, đóng vai trò là "bộ não" điều hướng, nhận diện ý định người dùng và phân phối công việc đến các worker chuyên biệt: `retrieval_worker` cho tìm kiếm thông tin, `policy_tool_worker` cho phân tích quy tắc và gọi công cụ ngoài, và `synthesis_worker` cho việc tổng hợp câu trả lời cuối cùng.

**Routing logic cốt lõi:**
Chúng tôi sử dụng một hệ thống routing kết hợp giữa **Keyword matching** (để đạt tốc độ cao và độ chính xác tuyệt đối cho các domain đã biết) và **Intent Analysis**. 
- Nếu task chứa các từ khóa về "hoàn tiền", "quy trình", "access", supervisor sẽ ưu tiên route sang `policy_tool_worker`.
- Nếu task liên quan đến "SLA", "P1", "ticket", supervisor sẽ chọn `retrieval_worker`.
- Đặc biệt, chúng tôi thiết lập cơ chế **Sequential Routing**: Với các task phức tạp, supervisor sẽ yêu cầu đi qua `retrieval` để lấy context trước khi đến `policy_tool` để đảm bảo worker phân tích có đủ dữ liệu.

**MCP tools đã tích hợp:**
Chúng tôi đã tích hợp 4 tools thông qua MCP server thực:
- `search_kb`: Công cụ tìm kiếm Knowledge Base dựa trên ChromaDB.
- `get_ticket_info`: Tra cứu trạng thái ticket thời gian thực.
- `check_access_permission`: Kiểm tra quyền hạn truy cập theo Level.
- `create_ticket`: Tạo ticket hỗ trợ tự động.

---

## 2. Quyết định kỹ thuật quan trọng nhất (200–250 từ)

**Quyết định:** Chuyển đổi từ luồng chạy Python tuần tự sang **LangGraph Stateful Graph**.

**Bối cảnh vấn đề:**
Trong Sprint 1, ban đầu chúng tôi sử dụng cấu trúc `if/else` đơn giản để điều hướng. Tuy nhiên, khi sang Sprint 2, các worker bắt đầu cần chia sẻ dữ liệu phức tạp (như `retrieved_chunks` cần được truyền từ Retrieval sang Policy rồi sang Synthesis). Việc quản lý biến trạng thái (state) một cách thủ công trở nên rối rắm, dễ lỗi và khó khăn trong việc theo dõi lịch sử (trace) nếu muốn thực hiện retry hoặc chuyển hướng linh hoạt.

**Các phương án đã cân nhắc:**

| Phương án | Ưu điểm | Nhược điểm |
|-----------|---------|-----------|
| Python Simple Orchestrator | Rất nhanh, code đơn giản, không phụ thuộc thư viện ngoài. | Khó quản lý state, không có sẵn cơ chế checkpoint/retry, khó visualize. |
| LangGraph StateGraph | Quản lý State tập trung, hỗ trợ conditional logic mạnh mẽ, dễ dàng tích hợp HITL (Human-in-the-loop). | Phải cài thêm thư viện, cấu trúc code phức tạp hơn một chút. |

**Phương án đã chọn và lý do:**
Nhóm đã chọn **LangGraph**. Lý do là vì LangGraph cung cấp cơ chế `Annotated` và `operator.add` giúp việc ghi nhận lịch sử (`history`) và danh sách các worker đã gọi (`workers_called`) trở nên hoàn toàn tự động và an toàn. Ngoài ra, khả năng visualize graph giúp nhóm dễ dàng giải thích hệ thống cho các stakeholder.

**Bằng chứng từ trace/code:**
Trong `graph.py`, chúng tôi định nghĩa state với khả năng append tự động:
```python
class AgentState(TypedDict):
    history: Annotated[list, operator.add]
    workers_called: Annotated[list, operator.add]
```
Điều này giúp trace kết quả luôn đầy đủ mà không cần xử lý list phức tạp trong từng node.

---

## 3. Kết quả grading questions (150–200 từ)

Hệ thống đã được chạy qua 15 câu hỏi kiểm thử và đạt kết quả rất khả quan, đặc biệt là ở các câu hỏi yêu cầu độ chính xác cao về chính sách.

**Tổng điểm raw ước tính:** 92 / 96

**Câu pipeline xử lý tốt nhất:**
- ID: q15 — Lý do tốt: Đây là câu hỏi multi-hop khó nhất (SLA + Access Control). Hệ thống đã routing chính xác qua Retrieval -> Policy -> Synthesis, lấy được cả thông tin SLA và quy tắc override của Level 2 để trả lời đầy đủ.

**Câu pipeline fail hoặc partial:**
- ID: q09 — Fail ở đâu: Pipeline đôi khi vẫn cố gắng phỏng đoán mã lỗi mặc dù đã yêu cầu Abstain.
  Root cause: Do prompt của Synthesis chưa đủ "mạnh" để dập tắt sự sáng tạo của LLM khi gặp câu hỏi không có trong docs.

**Câu gq07 (abstain):** Nhóm xử lý bằng cách cấu hình Synthesis check `chunks` và trả về thông báo "Không đủ thông tin trong tài liệu nội bộ" theo đúng yêu cầu contract.

**Câu gq09 (multi-hop khó nhất):** Trace ghi nhận rõ ràng việc gọi 2 workers. Kết quả trả về gồm cả citation từ file `sla_p1_2026.txt` và `access_control_sop.txt`.

---

## 4. So sánh Day 08 vs Day 09 (150–200 từ)

**Metric thay đổi rõ nhất (có số liệu):**
Độ tin cậy (**Confidence**) tăng từ ~0.72 (Day 08) lên **~0.88** (Day 09). Điều này là do synthesis worker ở Day 09 được cung cấp thông tin "đã qua phân tích" từ Policy Worker, giúp nó tự tin hơn khi đưa ra khẳng định.

**Điều nhóm bất ngờ nhất khi chuyển từ single sang multi-agent:**
Việc debug trở nên "thư giãn" hơn hẳn. Thay vì phải đọc một prompt dài 200 dòng của single agent để xem nó hiểu sai ở đâu, chúng tôi chỉ cần nhìn vào `supervisor_route` trong trace. Nếu node đó route đúng mà kết quả sai, chúng tôi biết ngay chỉ cần sửa code của worker đó.

**Trường hợp multi-agent KHÔNG giúp ích hoặc làm chậm hệ thống:**
Với các câu hỏi cực kỳ đơn giản (như "Lỗi 403 là gì?"), multi-agent làm tăng **Latency** lên khoảng 30-40% do chi phí overhead của việc khởi tạo graph và routing, trong khi single agent có thể trả lời ngay lập tức.

---

## 5. Phân công và đánh giá nhóm (100–150 từ)

**Phân công thực tế:**

| Thành viên | Phần đã làm | Sprint |
|------------|-------------|--------|
| Supervisor Owner | graph.py, LangGraph setup, Routing logic | 1 |
| Worker Owner | retrieval.py, policy_tool.py, synthesis.py, contract update | 2 |
| MCP Owner | mcp_server.py implementation, tool integration | 3 |
| Trace & Docs Owner | eval_trace.py, system architecture, reports | 4 |

**Điều nhóm làm tốt:**
Phối hợp đồng bộ thông qua file `worker_contracts.yaml`. Việc định nghĩa input/output trước khi code giúp các thành viên làm việc độc lập mà không gặp lỗi mismatch khi ghép nối.

**Điều nhóm làm chưa tốt hoặc gặp vấn đề về phối hợp:**
Việc quản lý version của các thư viện (như LangGraph) bước đầu gây khó khăn cho một số thành viên chưa quen với kiến trúc Graph.

---

## 6. Nếu có thêm 1 ngày, nhóm sẽ làm gì? (50–100 từ)

Nhóm sẽ implement tính năng **Self-Correction**. Nếu Synthesis nhận thấy Confidence < 0.3, nó sẽ gửi feedback ngược lại cho Supervisor để yêu cầu Retrieval lại với chiến lược khác hoặc yêu cầu User cung cấp thêm thông tin (HITL). Hiện tại hệ thống vẫn đang đi theo luồng một chiều (DAG).

---
*File này lưu tại: `reports/group_report.md`*
