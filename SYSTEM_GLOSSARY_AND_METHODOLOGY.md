# 📖 HƯỚNG DẪN VÀ GIẢI THÍCH THUẬT NGỮ HỆ THỐNG GIÁM SÁT ESG GREENWASHING

Tài liệu này giải thích chi tiết các thuật ngữ, thang đo rủi ro, chỉ số đánh giá và kiến trúc hệ thống 3 Agent dành cho người dùng, chuyên gia thẩm định và hội đồng đánh giá.

---

## 1. TỔNG QUAN HỆ THỐNG 3 AGENT (SYSTEM ARCHITECTURE)

Hệ thống ứng dụng kiến trúc 3 Agent AI độc lập phối hợp nhằm phát hiện và giám sát rủi ro **Greenwashing** (Tẩy xanh) trong Báo cáo Phát triển Bền vững (ESG) của doanh nghiệp:

1. **Agent 1 (ESG Claim Analyzer - Đơn vị phát hiện)**:
   - Quét toàn bộ văn bản báo cáo ESG, phát hiện các tuyên bố cam kết môi trường và phân loại theo 4 nhóm Indicator.
2. **Agent 2 (Devil's Advocate - Đơn vị phản biện độc lập)**:
   - Phản biện lại đánh giá của Agent 1 nhằm loại bỏ hiện tượng ảo giác (hallucination) hoặc cảnh báo rủi ro quá mức. Hai Agent lặp lại cuộc tranh luận cho đến khi đạt đồng thuận.
3. **Agent 3 (Incident Matcher & Search API Validation - Đơn vị xác thực thực tế)**:
   - Sử dụng **Google Custom Search API / Live Web Search API** để cào dữ liệu báo chí và thông báo xử phạt thực tế, đối chiếu phán đoán của AI với thực tế đời thực.

---

## 2. GIẢI THÍCH CHI TIẾT CÁC THUẬT NGỮ CHÍNH (GLOSSARY)

### 📊 1. Total Claims Detected (Tổng số Claims phát hiện)
- **Định nghĩa**: Tổng số tuyên bố, cam kết hoặc thông điệp về môi trường/ESG có dấu hiệu nghi vấn hoặc cần kiểm chứng được Agent 1 phát hiện từ các đoạn văn bản (chunks) trong báo cáo ESG của doanh nghiệp.

### 🚨 2. Risk Levels & Risk Calibration (Các mức độ Rủi ro)
Hệ thống chuẩn hóa đánh giá rủi ro Greenwashing theo 4 mức độ:

- **🔴 High Risk (Rủi ro Cao)**:
  - **Dấu hiệu**: Tuyên bố mâu thuẫn số liệu môi trường nghiêm trọng; đưa ra cam kết Net Zero / 100% tái chế rất lớn nhưng hoàn toàn **KHÔNG có lộ trình, mốc thời gian hay số liệu kiểm chứng**.
- **🟡 Medium Risk (Rủi ro Trung bình)**:
  - **Dấu hiệu**: Cam kết môi trường cụ thể nhưng thiếu số liệu xác minh độc lập, hoặc ngôn ngữ còn mập mờ, thiếu minh bạch.
- **🟢 Low Risk / None (Rủi ro Thấp / Không rủi ro)**:
  - **Dấu hiệu**: Thông điệp truyền thông chung, sứ mệnh doanh nghiệp, thành tựu đã được chứng nhận rõ ràng (ví dụ: ISO 14001, chứng nhận Net Zero từ tổ chức độc lập).

### 🎯 3. 4 ESG Indicators (4 Nhóm Chỉ số Rủi ro Greenwashing)
1. **Selective Disclosure (Giấu thông tin xấu)**: Nhấn mạnh điểm xanh nhỏ nhưng che giấu tác hại/vi phạm môi trường tiêu cực.
2. **Hollow Promise (Cam kết rỗng)**: Đưa ra cam kết lớn (Net Zero, 100% giảm nhựa...) nhưng không có tiến triển, không có cột mốc thời gian rõ ràng.
3. **Misconduct (Sai phạm số liệu)**: Số liệu môi trường bất thường, thổi phồng hoặc mâu thuẫn giữa các trang báo cáo.
4. **Misleading Presentation (Ngôn ngữ mập mờ)**: Dùng nhãn 'xanh 100%', 'thân thiện môi trường', 'thuần tự nhiên' mà không có chứng nhận hợp lệ.

### 🤝 4. Cohen's Kappa Coefficient ($\kappa$ - Chỉ số Đồng thuận Inter-Rater)
- **Công thức toán học**:
  $$\kappa = \frac{p_o - p_e}{1 - p_e}$$
- **Ý nghĩa**: Đo lường mức độ đồng thuận thực tế giữa Agent 1 và Agent 2 sau các lượt phản biện.
- **Thang bảng xếp hạng (Landis & Koch Interpretation Scale)**:
  - $\kappa = 1.00$: **Perfect agreement** (Đồng thuận tuyệt đối)
  - $\kappa = 0.81 - 0.99$: **Near perfect agreement** (Gần như hoàn hảo)
  - $\kappa = 0.61 - 0.80$: **Substantial agreement** (Đồng thuận đáng kể)
  - $\kappa = 0.41 - 0.60$: **Moderate agreement** (Đồng thuận vừa phải)
  - $\kappa = 0.21 - 0.40$: **Fair agreement** (Đồng thuận trung bình)
  - $\kappa = 0.10 - 0.20$: **Slight agreement** (Đồng thuận nhẹ)
  - $\kappa = 0.00$: **No agreement** (Bất đồng quan điểm, cần con người can thiệp)

### 📈 5. Confusion Matrix & System Metrics (Ma trận Nhầm lẫn & Độ chính xác)
Đối chiếu giữa kết quả AI ($AI$) và Dữ liệu thực tế từ Google Search API ($GT$):

- **True Positive (TP - Confirmed Risk)**: AI cảnh báo rủi ro và báo chí/xử phạt thực tế xác nhận đúng vi phạm ($AI \ge 1, GT \ge 1$).
- **False Positive (FP - Unverified Risk / Over-prediction)**: AI cảnh báo rủi ro nhưng thực tế chưa có báo chí kiểm chứng hoặc thông tin bị bác bỏ ($AI \ge 1, GT = 0$).
- **True Negative (TN - Confirmed Clean)**: AI xác nhận an toàn và thực tế không có vi phạm ($AI = 0, GT = 0$).
- **False Negative (FN - Missed Risk / Under-prediction)**: AI bỏ sót rủi ro khi báo chí thực tế có tin xử phạt ($AI = 0, GT \ge 1$).

### 📐 6. Accuracy Metrics (Precision, Recall, F1-Score, Accuracy)
- **Precision (Độ chính xác)**: Tỷ lệ các cảnh báo rủi ro của AI thực sự đúng thực tế $= \frac{TP}{TP + FP}$.
- **Recall (Độ bao phủ)**: Tỷ lệ các rủi ro thực tế mà AI phát hiện được $= \frac{TP}{TP + FN}$.
- **F1-Score**: Điểm trung bình hài hòa giữa Precision và Recall $= 2 \times \frac{Precision \times Recall}{Precision + Recall}$.
- **Accuracy (Độ chính xác toàn cục)**: Tỷ lệ tổng số phân loại đúng $= \frac{TP + TN}{TP + FP + TN + FN}$.
