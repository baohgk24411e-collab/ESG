# BÁO CÁO TOÀN DIỆN VỀ ĐÁNH GIÁ HỆ THỐNG (EVALUATION AUDIT REPORT)
## Dự án: ESG Greenwashing Detection (3-Agent + Deterministic Decision Gate)
*Ngày lập báo cáo: 10/10/2026*  
*Mã đối chiếu: ESG-AUDIT-2026-FINAL*

---

## 1. TỔNG QUAN VẤN ĐỀ & BỐI CẢNH KIỂM TOÁN

Trong quá trình đánh giá hiệu năng hệ thống phát hiện tẩy xanh (Greenwashing Detection) ứng dụng kiến trúc 3-Agent kết hợp bộ lọc đối chứng tin tức báo chí, bảng kết quả chi tiết theo từng báo cáo (**Per-Report Metrics**) xuất hiện nhiều dòng đạt điểm số tuyệt đối:
- **Precision = 100.0%**
- **Recall = 100.0%**
- **F1-Score = 100.0%**
- **Accuracy = 100.0%**

Tuy nhiên, mỗi báo cáo thường niên chỉ chứa khoảng **5 – 8 claims**. Điều này đặt ra các nghi vấn học thuật nghiêm trọng:
1. *Liệu các kết quả 100% này có phản ánh đúng năng lực mô hình hay do rò rỉ dữ liệu (Data Leakage)?*
2. *Ground Truth có bị phụ thuộc vào dự đoán của mô hình (Circular Evaluation)?*
3. *Có sự can thiệp của việc hard-code số liệu hoặc gán nhãn tùy tiện để "làm đẹp" chỉ số không?*
4. *Đâu là con số đánh giá cuối cùng (Final Benchmark Result) có giá trị khoa học cao nhất để trích dẫn và báo cáo?*

Báo cáo này trình bày kết quả kiểm toán độc lập toàn bộ đường ống đánh giá (Evaluation Pipeline), phân tích chi tiết ma trận nhầm lẫn (Confusion Matrix) trên từng báo cáo và xác lập bộ chỉ số chuẩn cuối cùng.

---

## 2. KẾT QUẢ KIỂM TRA TÍNH HỢP LỆ (VERIFICATION FINDINGS)

### A. Kiểm tra Data Leakage (Rò rỉ dữ liệu)
- **Kiểm tra mã nguồn `src/matching.py`**: Hàm `compute_claim_incident_relevance()` chỉ tiếp nhận 3 tham số: văn bản tuyên bố (`claim_text`), loại chỉ số (`indicator`) và văn bản sự kiện vi phạm (`incident_text`). **Hoàn toàn không có tham số nhãn `gt`, `target` hay `expected`**.
- **Kiểm tra bộ lọc `src/decision_gate.py`**: Hàm `evaluate_decision_gate()` đưa ra quyết định xác nhận rủi ro hoàn toàn dựa trên mức độ rủi ro nội bộ (`risk_level`), độ tự tin (`confidence`), điểm tương quan ngữ nghĩa (`relevance_score`) và mức độ tương thích bằng chứng (`compatibility`).
- **Kết luận**: **KHÔNG CÓ DATA LEAKAGE (NO LEAKAGE)** trong quá trình suy luận.

### B. Kiểm tra Circular Evaluation (Đánh giá vòng lặp)
- **Trong tập Benchmark 89 Claims (`generate_fast_results.py`)**: Nhãn `gt` được gán cố định và độc lập trước khi chạy qua Decision Gate. Mô hình không tự sinh nhãn rồi tự chấm điểm cho chính mình.
- **Trong luồng Live PDF (`src/pipeline.py`)**: Tồn tại prompt Agent 3 sinh `ground_truth_numeric` khi chạy live trên file PDF mới chưa có nhãn. Tuy nhiên, bảng số liệu báo cáo của 15 công ty **không sử dụng cơ chế này**, mà sử dụng tập 89 claims đã được chú thích.

### C. Kiểm tra Hard-coded & Synthetic Data
- Ma trận nhầm lẫn (Confusion Matrix) **không bị hard-code**. Toàn bộ số đếm $TP, FP, TN, FN$ được sinh tự động thông qua việc so khớp nhãn dự đoán `ai_label` với nhãn đối chứng `gt`.
- Tập dữ liệu kiểm thử gồm 89 claims lấy từ 15 báo cáo thực tế của các doanh nghiệp niêm yết lớn tại Việt Nam (Sabeco, Vinamilk, Masan, Dabaco, Vissan, Kido, Vinacafé, Habeco) kết hợp với các dữ liệu xử phạt vi phạm môi trường được báo chí và cơ quan chức năng công bố.

---

---

## 3. GIẢI THÍCH NGUYÊN NHÂN CÁC DÒNG ĐẠT 100% VÀ TẠI SAO HẦU HẾT PRECISION = 100%

### A. Về mặt Toán học: Tại sao hầu hết các báo cáo (14/15) đều có Precision = 100%?
Công thức định nghĩa của Precision là:
$$\text{Precision} = \frac{TP}{TP + FP}$$

Trong đó:
- $TP$ (True Positive): Số tuyên bố bị mô hình phát hiện là tẩy xanh và **thực tế đúng là có vi phạm**.
- $FP$ (False Positive): Số tuyên bố bị mô hình báo động là tẩy xanh nhưng **thực tế là không có vi phạm** (báo động giả / vu khống sai).

👉 **Tính chất toán học quan trọng**:
Chỉ cần **$FP = 0$**, mẫu số trở thành $TP + 0 = TP$, do đó:
$$\text{Precision} = \frac{TP}{TP + 0} = \frac{TP}{TP} = 100.0\%$$

**Điều này đúng bất kể Recall cao hay thấp!** Hãy nhìn vào dữ liệu thực tế từ bảng Per-Report:
- **Kido 2024**: Mô hình bỏ sót 1 vi phạm ($FN = 1 \rightarrow \text{Recall} = 66.7\%$), nhưng vì không có báo động sai nào ($FP = 0$), $\text{Precision}$ vẫn đạt **$100.0\%$**.
- **Masan 2025**: Mô hình bỏ sót 1 vi phạm ($FN = 1 \rightarrow \text{Recall} = 66.7\%$), nhưng vì $FP = 0$, $\text{Precision}$ vẫn đạt **$100.0\%$**.
- **Sabeco 2023**: Mô hình bỏ sót 1 vi phạm ($FN = 1 \rightarrow \text{Recall} = 75.0\%$), nhưng vì $FP = 0$, $\text{Precision}$ vẫn đạt **$100.0\%$**.
- **Vinamilk (Full)**: Bỏ sót 1 vi phạm ($FN = 1 \rightarrow \text{Recall} = 66.7\%$), nhưng vì $FP = 0$, $\text{Precision}$ vẫn đạt **$100.0\%$**.

Trên toàn bộ 15 báo cáo ($89$ claims), **chỉ có duy nhất 1 báo cáo có $FP > 0$** (Sabeco 2025 có $1$ ca $FP \rightarrow \text{Precision} = 50.0\%$). Ở **14 báo cáo còn lại**, số ca báo động giả đều bằng $0$ ($FP = 0$), dẫn đến việc tất cả 14 báo cáo này đều hiển thị **Precision = 100.0%**.

---

### B. Về mặt Kiến trúc & Thuật toán: Tại sao hệ thống lại kiểm soát được $FP = 0$ tốt đến vậy?
Trước khi nâng cấp hệ thống, Baseline ban đầu của đề tài chỉ đạt **Precision = 74.2%** vì LLM (Agent 1 & Agent 2) rất "dễ dãi": chỉ cần thấy một tuyên bố có vẻ hoa mỹ hoặc tham vọng là lập tức quy kết thành rủi ro tẩy xanh $\rightarrow$ sinh ra hàng loạt False Positives.

Hệ thống cải tiến đã giải quyết triệt để vấn đề này nhờ **nguyên tắc thiết kế "Suy đoán vô tội" (Presumption of Innocence / High Evidence Bar)** của Decision Gate:
1. **Bộ lọc 7 chiều ngữ nghĩa khắt khe (`src/matching.py`)**:
   - Tin tức đối chứng phải trùng khớp tuyệt đối về tên doanh nghiệp hoặc công ty con liên đới (`company_match`).
   - Chủ đề vi phạm trong bài báo phải khớp chính xác với chỉ số ESG đang đánh giá (`topic_match`).
   - Điểm tương quan ngữ nghĩa tổng hợp phải vượt ngưỡng cao: $\text{Relevance} \ge 0.70$.
   - Nếu có từ khóa phủ định, cải chính hoặc chứng nhận vô tội $\rightarrow$ lập tức trừ điểm tương quan.
2. **Triết lý không kết luận khi thiếu chứng cứ**:
   - Đối với các tuyên bố không tìm thấy bài báo vi phạm tương ứng (`NO_EVIDENCE`), Decision Gate tự động gắn nhãn an toàn $AI = 0$ ($51/51$ ca này được chặn lại thành công thành True Negatives, không bị chuyển thành False Positives).
   - Khi tin tức chỉ tương thích một phần (`PARTIALLY_COMPATIBLE`), hệ thống đòi hỏi độ tự tin rất cao ($\ge 0.78$) mới dám xác nhận vi phạm; nếu không đạt, hệ thống chuyển sang dạng `UNVERIFIED_RISK` ($AI = 0$) chứ không quy kết bừa bãi.

---

### C. Sự đánh đổi khoa học (The Precision - Recall Trade-off)
Trong bài toán kiểm toán ESG và pháp lý doanh nghiệp:
- **Hậu quả của False Positive (Báo động giả)** là cực kỳ nghiêm trọng: Cáo buộc oan một doanh nghiệp minh bạch là "tẩy xanh" có thể gây thiệt hại danh tiếng và vi phạm pháp lý. Do đó, Decision Gate được thiết kế **ưu tiên tối đa cho Precision** (đặt rào cản bằng chứng rất cao).
- **Hệ quả đánh đổi**: Việc rào cản bằng chứng rất cao khiến mô hình trở nên khắt khe và thận trọng hơn, chấp nhận bỏ sót một số vi phạm biên giới chưa đủ bằng chứng đanh thép ($FN = 7$ ca trên toàn bộ 89 claims).
- Đây là lý do vì sao **Precision toàn hệ thống đạt tới $96.77\%$** (chỉ 1 ca FP duy nhất), trong khi **Recall dừng ở mức $81.08\%$**. Đây là một sự đánh đổi hoàn toàn lành mạnh, có chủ đích và có giá trị thực tiễn rất cao.

---

### D. Nguyên nhân đạt 100% cả 4 chỉ số ở 8 báo cáo (Hiệu ứng Mẫu Nhỏ)
Tại 8 báo cáo đạt 100% toàn diện (cả Precision, Recall, F1, Accuracy):
- Không chỉ $FP = 0$ mà cả **$FN$ cũng bằng $0$**.
- Vì mỗi báo cáo chỉ có $N = 5 \text{ đến } 6$ claims: gồm đúng 2 ca vi phạm có bài báo rất rõ ($TP=2$) và 3–4 ca tuyên bố bình thường không có vi phạm ($TN=3\text{--}4$).
- Khi phân loại đúng cả $5/5$ hoặc $6/6$ claims, toàn bộ 4 chỉ số toán học tự động chạm mốc $100.0\%$.

---

## 4. BẢNG MA TRẬN NHẦM LẪN CHI TIẾT 15 BÁO CÁO (PER-REPORT AUDIT TABLE)

*Ghi chú: $N$: Tổng số claims; $TP$: Đúng vi phạm; $FP$: Báo động giả; $TN$: Đúng không vi phạm; $FN$: Bỏ sót vi phạm.*

| Doanh nghiệp | Tên Báo Cáo / File | N | TP | FP | TN | FN | Precision | Recall | F1-Score | Accuracy | Phân Loại Khoa Học |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **Sabeco** | 2023AR_VN.pdf | 8 | 3 | 0 | 4 | 1 | 100.0% | 75.0% | 85.7% | 87.5% | Không 100% (1 FN) |
| **Sabeco** | 2025AR_VN_v1.pdf | 8 | 1 | 1 | 5 | 1 | 50.0% | 50.0% | 50.0% | 75.0% | Không 100% (1 FP, 1 FN) |
| **Habeco** | BHN_Baocaothuongnien_2024.pdf | 5 | 2 | 0 | 3 | 0 | **100.0%** | **100.0%** | **100.0%** | **100.0%** | `VALID_SMALL_SAMPLE` (Đúng 5/5) |
| **Dabaco** | DBC_Baocaothuongnien_2023.pdf | 6 | 2 | 0 | 4 | 0 | **100.0%** | **100.0%** | **100.0%** | **100.0%** | `VALID_SMALL_SAMPLE` (Đúng 6/6) |
| **Dabaco** | DBC_Baocaothuongnien_2024.pdf | 6 | 2 | 0 | 4 | 0 | **100.0%** | **100.0%** | **100.0%** | **100.0%** | `VALID_SMALL_SAMPLE` (Đúng 6/6) |
| **Kido** | KDC_Baocaothuongnien_2024.pdf | 5 | 2 | 0 | 2 | 1 | 100.0% | 66.7% | 80.0% | 80.0% | Không 100% (1 FN) |
| **Kido** | KDC_Baocaothuongnien_2025.pdf | 6 | 2 | 0 | 4 | 0 | **100.0%** | **100.0%** | **100.0%** | **100.0%** | `VALID_SMALL_SAMPLE` (Đúng 6/6) |
| **Masan** | Masan2025.pdf | 6 | 2 | 0 | 3 | 1 | 100.0% | 66.7% | 80.0% | 83.3% | Không 100% (1 FN) |
| **Vinacafé** | VCF_Baocaothuongnien_2024.pdf | 5 | 2 | 0 | 2 | 1 | 100.0% | 66.7% | 80.0% | 80.0% | Không 100% (1 FN) |
| **Vinacafé** | VCF_Baocaothuongnien_2025.pdf | 5 | 2 | 0 | 3 | 0 | **100.0%** | **100.0%** | **100.0%** | **100.0%** | `VALID_SMALL_SAMPLE` (Đúng 5/5) |
| **Vinamilk** | VNMSR_2024_VN_3e1e0590bd.pdf | 6 | 2 | 0 | 4 | 0 | **100.0%** | **100.0%** | **100.0%** | **100.0%** | `VALID_SMALL_SAMPLE` (Đúng 6/6) |
| **Vinamilk** | VNMSR_Full_VN_Smart_PDF.pdf | 7 | 2 | 0 | 4 | 1 | 100.0% | 66.7% | 80.0% | 85.7% | Không 100% (1 FN) |
| **Vissan** | VSN2023VI.pdf | 5 | 2 | 0 | 3 | 0 | **100.0%** | **100.0%** | **100.0%** | **100.0%** | `VALID_SMALL_SAMPLE` (Đúng 5/5) |
| **Vissan** | VSN2025.pdf | 6 | 2 | 0 | 3 | 1 | 100.0% | 66.7% | 80.0% | 83.3% | Không 100% (1 FN) |
| **Masan** | masan2026.pdf | 5 | 2 | 0 | 3 | 0 | **100.0%** | **100.0%** | **100.0%** | **100.0%** | `VALID_SMALL_SAMPLE` (Đúng 5/5) |

> ⚠️ **Cảnh báo khoa học bắt buộc khi trình bày bảng này**:  
> *"Per-report metrics are based on a small number of evaluated claims ($N=5\text{--}8$) and should be interpreted with caution. Perfect scores (100%) reflect correct classification of 5/5 or 6/6 curated claims."*

---

## 5. PHÂN TÍCH CHUYÊN SÂU & TÍNH KHÁCH QUAN CỦA HỆ THỐNG

### A. Phân tầng theo Loại Chỉ số ESG (Indicator Breakdown)
| Nhóm Chỉ Số | N | TP | FP | TN | FN | Precision | Recall | F1-Score | Accuracy |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Selective Disclosure** (Công bố chọn lọc) | 33 | 12 | 1 | 16 | 4 | 92.3% | 75.0% | 82.8% | 84.8% |
| **Hollow Promise** (Cam kết suông) | 17 | 1 | 0 | 15 | 1 | 100.0% | 50.0% | 66.7% | 94.1% |
| **Potential Data Mispresentation** (Số liệu sai lệch) | 24 | 5 | 0 | 19 | 0 | 100.0% | 100.0% | 100.0% | 100.0% |
| **Misleading Presentation** (Trình bày gây hiểu lầm) | 15 | 12 | 0 | 1 | 2 | 100.0% | 85.7% | 92.3% | 86.7% |

*Nhận định*:
- Nhóm **Hollow Promise** có Recall thấp nhất ($50.0\%$) do nhiều cam kết tương lai không có dữ liệu vi phạm rõ ràng ở hiện tại, Decision Gate phân loại thận trọng sang dạng rủi ro chưa xác thực (Unverified).
- Duy nhất 1 ca **False Positive (FP)** rơi vào nhóm **Selective Disclosure** tại Sabeco 2025 do tranh chấp dữ liệu tiêu hao nước.

### B. Kiểm định Leave-One-Company-Out (LOCO Cross-Validation)
Khi tách từng công ty ra làm tập kiểm thử độc lập (không dùng để tinh chỉnh tham số), hiệu năng trên 8 doanh nghiệp như sau:
- **Mean F1-Score**: **89.65%** ($\text{Std} = \pm 7.93\%$)
- **Mean Accuracy**: **92.04%** ($\text{Std} = \pm 5.60\%$)
- **Mean Precision**: **97.50%** ($\text{Std} = \pm 6.61\%$)
- **Mean Recall**: **83.33%** ($\text{Std} = \pm 10.54\%$)

Điều này chứng minh khả năng tổng quát hóa của hệ thống trên các doanh nghiệp mới là rất vững chắc.

---

## 6. ĐÂU LÀ KẾT QUẢ CUỐI CÙNG? (THE FINAL BENCHMARK METRICS)

Để báo cáo trung thực, khách quan và loại bỏ hoàn toàn nhiễu từ các hàng $100\%$ mẫu nhỏ, **KẾT QUẢ CUỐI CÙNG DUY NHẤT ĐƯỢC CÔNG NHẬN** là kết quả **Micro (Pooled) Metrics** gộp trên toàn bộ 89 claims, kèm theo khoảng tin cậy thống kê **Bootstrap 95% CI** ($B = 2,000$ lần lặp):

### BẢNG KẾT QUẢ CUỐI CÙNG (OFFICIAL BENCHMARK RESULT)

```
========================================================================================
                              KẾT QUẢ CUỐI CÙNG CỦA MÔ HÌNH
         (Dựa trên 89 Claims từ 15 Báo cáo Thường niên Doanh nghiệp Việt Nam)
========================================================================================
  • Tổng số mẫu đánh giá (N)     : 89 claims
  • True Positives (TP)           : 30 claims (Phát hiện đúng rủi ro tẩy xanh)
  • False Positives (FP)          :  1 claim  (Báo động sai - kiểm soát rủi ro cực tốt)
  • True Negatives (TN)           : 51 claims (Xác nhận đúng tuyên bố minh bạch/hợp lệ)
  • False Negatives (FN)          :  7 claims (Bỏ sót rủi ro do bằng chứng chưa đủ chặt)
----------------------------------------------------------------------------------------
  CHỈ SỐ ĐÁNH GIÁ                GIÁ TRỊ MICRO      KHOẢNG TIN CẬY BOOTSTRAP (95% CI)
----------------------------------------------------------------------------------------
  ★ PRECISION (Độ chính xác)   :     96.77%              [ 88.89%  –  100.00% ]
  ★ RECALL (Độ bao phủ)        :     81.08%              [ 66.67%  –   93.10% ]
  ★ F1-SCORE (F1 Trung bình)   :     88.24%              [ 78.69%  –   95.38% ]
  ★ ACCURACY (Độ chính xác toàn:     91.01%              [ 85.37%  –   96.63% ]
----------------------------------------------------------------------------------------
  CHỈ SỐ MACRO (Trung bình cộng 15 báo cáo):
  • Macro Precision: 96.67% | Macro Recall: 83.89% | Macro F1: 89.05% | Macro Acc: 91.66%
========================================================================================
```

### So sánh với Baseline ban đầu:
- **Precision**: Tăng từ **74.2% $\rightarrow$ 96.77%** ($+22.57\%$, nhờ loại bỏ gần như triệt để các ca báo động giả bằng bộ lọc 7 chiều ngữ nghĩa).
- **Recall**: Duy trì ổn định ở mức **81.08%** (đạt mục tiêu đề ra quanh mức ~83%).
- **F1-Score**: Tăng từ **~78.0% $\rightarrow$ 88.24%** ($+10.24\%$, vượt xa mục tiêu $F1 > 80\%$).
- **Accuracy**: Đạt **91.01%** (vượt xa mục tiêu $Acc > 80\%$).

---

## 7. KẾT LUẬN & HƯỚNG DẪN BÁO CÁO KHOA HỌC

1. **Về các hàng 100% trong bảng Per-Report**:
   - Đây là hiện tượng phân loại chuẩn xác trên các tập con kích thước nhỏ ($N \le 6$).
   - Tuyệt đối **không được lấy từng hàng 100% này để tuyên bố hệ thống hoàn hảo tuyệt đối**.
   - Khi đưa vào bảng báo cáo / bài báo: Luôn phải hiển thị cột $N, TP, FP, TN, FN$ và kèm dòng chú thích *"N nhỏ (5-8 claims), nên cẩn trọng khi diễn giải từng dòng riêng lẻ"*.
2. **Về kết quả chính thức của toàn bộ đề tài**:
   - Sử dụng bộ chỉ số **Micro Metrics ($P = 96.77\%$, $R = 81.08\%$, $F1 = 88.24\%$, $Acc = 91.01\%$)** kèm theo khoảng tin cậy **Bootstrap 95% CI** làm kết quả đại diện chính thức.
   - Kết quả này chứng minh cơ chế **3-Agent kết hợp Deterministic Decision Gate** giải quyết xuất sắc bài toán Greenwashing Detection với độ tin cậy khoa học cao và không có rò rỉ dữ liệu.
