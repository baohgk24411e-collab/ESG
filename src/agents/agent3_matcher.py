from typing import List, Optional
from src.models import ClaimDebateResult, NewsIncident, IncidentMatchResult
from src.config import AGENT3_MODEL_NAME
from src.llm_client import call_llm_json

AGENT3_SYSTEM_PROMPT = """Bạn là Agent 3 (Incident Matcher & Validation Agent).
Nhiệm vụ của bạn là đối chiếu phán đoán Rủi ro từ Agent 1&2 của MỘT TUYÊN BỐ CỤ THỂ với DỮ LIỆU SỰ KIỆN THỰC TẾ (Báo chí, xử phạt) liên quan trực tiếp đến chủ đề tuyên bố đó.

QUY TẮC NGUYÊN TẮC QUAN TRỌNG VỀ ĐÁNH GIÁ (TRÁNH GẮN MÁC TUYỆT ĐỐI):
1. KHÔNG GẮN MÁC SAI TUYỆT ĐỐI NẾU CHƯA CÓ BẰNG CHỨNG PHỦ ĐỊNH: Việc báo chí chưa đăng tin xử phạt hoặc một đợt kiểm tra không phát hiện sai phạm KHÔNG ĐỒNG NGHĨA là doanh nghiệp hoàn toàn không có rủi ro môi trường.
2. CHỈ KẾT LUẬN AGENT 1 SAI (REFUTED / UNVERIFIED_RISK) KHI: Có văn bản hoặc tin tức chính thức xác nhận thông tin nguy cơ/cảnh báo rủi ro đó là HOÀN TOÀN VÔ CĂN CỨ hoặc BỊ VU KHỐNG.
3. Thang đánh giá "Mức độ tương thích của bằng chứng" (Evidence Compatibility):
   - HIGHLY_COMPATIBLE: Bằng chứng thực tế/báo chí xác nhận trực tiếp vi phạm/rủi ro do Agent 1 cảnh báo.
   - PARTIALLY_COMPATIBLE: Bằng chứng phản ánh đợt kiểm tra/hoạt động liên quan nhưng chưa đủ kết luận phạt nặng (Cảnh báo rủi ro tiềm ẩn của Agent 1 là có cơ sở).
   - REFUTED: Có văn bản/tin tức chính thức xác nhận thông tin cảnh báo rủi ro của Agent 1 là HOÀN TOÀN VÔ CĂN CỨ hoặc SAI SỰ THẬT.
   - NO_EVIDENCE: Không có thông tin/bài báo tiêu cực nào liên quan đến tuyên bố này.

QUY TẮC XUẤT CHUỖI SUY LUẬN (REASONING CHAIN):
Trong JSON trả về, bạn BẮT BUỘC phải xuất ra trường "reasoning_chain" (Chuỗi suy luận theo từng bước) TRƯỚC KHI đưa ra các nhãn đánh giá cuối cùng.

QUY TẮC RÀNG BUỘC TRÍCH DẪN (CITATION GROUNDING):
1. Bạn CHỈ ĐƯỢC PHÉP chọn trích dẫn bài báo nằm trong danh sách METADATA được cung cấp ở dưới.
2. Bắt buộc phải trả về trường "cited_url" trùng khớp CHÍNH XÁC 100% nguyên văn chuỗi URL có trong danh sách metadata. TUYỆT ĐỐI KHÔNG tự bịa URL, không thay đổi URL, và không rút gọn URL về trang chủ.
3. Nếu không có bài báo nào liên quan trực tiếp đến chủ đề tuyên bố, đặt "cited_url": null.

Quy tắc phân loại Cặp đôi (Pairwise Matching):
- Chuyển mức AI phán đoán: HIGH=2, MEDIUM/MODERATE=1, LOW/NONE=0.
- So sánh AI Risk Score ({ai_numeric}) và Ground Truth Risk Score ({gt_numeric}):
  + Nếu AI == Ground Truth và điểm >= 1 -> CONFIRMED_RISK (TP - AI phát hiện đúng rủi ro thực tế).
  + Nếu AI == Ground Truth và điểm == 0 -> NO_RISK_CONFIRMED (TN - AI xác nhận an toàn đúng thực tế).
  + Nếu AI > Ground Truth -> UNVERIFIED_RISK (FP - AI dự báo rủi ro quá mức / Over-prediction).
  + Nếu AI < Ground Truth -> MISSED_RISK (FN - AI bỏ sót rủi ro thực tế / Under-prediction).

Trả về định dạng JSON chuẩn:
{
  "reasoning_chain": "Bước 1: Phân tích tuyên bố... -> Bước 2: Xem xét bằng chứng metadata... -> Bước 3: Đánh giá xem thông tin rủi ro có bị chứng minh là hoàn toàn vô căn cứ hay không... -> Bước 4: Chốt mức độ tương thích.",
  "evidence_compatibility": "HIGHLY_COMPATIBLE" | "PARTIALLY_COMPATIBLE" | "REFUTED" | "NO_EVIDENCE",
  "ground_truth_level": "HIGH_RISK" | "MODERATE_RISK" | "LOW_RISK",
  "ground_truth_numeric": 2 | 1 | 0,
  "cited_url": "URL_chinh_xac_tuyet_doi_tu_metadata" | null,
  "matching_reasoning": "Giải thích tóm tắt lý do đối chiếu"
}
"""


def map_risk_str_to_numeric(risk_str: Optional[str]) -> int:
    """Map risk level string to numeric ordinal value (0, 1, 2)."""
    if not risk_str or not isinstance(risk_str, str):
        return 0
    r = risk_str.upper()
    if "HIGH" in r:
        return 2
    elif "MED" in r or "MODERATE" in r:
        return 1
    return 0


def match_claim_with_incidents(debate_result: ClaimDebateResult, incidents: List[NewsIncident]) -> IncidentMatchResult:
    """
    Agent 3 matches AI prediction against specific topic Ground Truth risk levels with non-binary evidence reasoning.
    """
    claim = debate_result.claim
    ai_risk_str = debate_result.final_risk_level
    ai_numeric = map_risk_str_to_numeric(ai_risk_str)

    # Structure metadata explicitly for Agent 3 with safe context truncation
    top_incidents = incidents[:3]  # Keep top 3 most relevant incidents
    incidents_text = "\n".join([
        f"--- [NGUỒN METADATA #{i+1}] ---\n"
        f"Title: {inc.title[:120]}\n"
        f"Source: {inc.source[:60]}\n"
        f"Publish Date: {inc.published_date}\n"
        f"URL (Exact): {inc.url}\n"
        f"Snippet Content: {inc.snippet[:180]}...\n"
        for i, inc in enumerate(top_incidents)
    ])

    prompt = f"""
CHỦ ĐỀ TUYÊN BỐ ESG: [{claim.indicator_type}]
TRÍCH DẪN BÁO CÁO: "{claim.claim_text[:200]}"
- AI Risk Level (Agent 1+2): {ai_risk_str} (Điểm số AI: {ai_numeric})

DANH SÁCH METADATA BÀI BÁO THỰC TẾ CÀO ĐƯỢC (Chỉ chọn URL trong danh sách này):
{incidents_text if incidents_text else "Không tìm thấy bài báo vi phạm nào."}

Hãy thực hiện chuỗi suy luận từng bước (reasoning_chain) để xác định Mức độ tương thích của bằng chứng (evidence_compatibility) và Ground Truth Risk Level cho tuyên bố này.
"""
    try:
        res = call_llm_json(prompt, AGENT3_SYSTEM_PROMPT, model_name=AGENT3_MODEL_NAME)
        gt_label = res.get("ground_truth_level") or "LOW_RISK"
        if not isinstance(gt_label, str):
            gt_label = "LOW_RISK"
        gt_numeric = int(res.get("ground_truth_numeric", map_risk_str_to_numeric(gt_label)))
        cited_url = res.get("cited_url")
        compatibility = res.get("evidence_compatibility", "NO_EVIDENCE")
        reasoning_chain = res.get("reasoning_chain", res.get("matching_reasoning", ""))

        # Enforce exact pairwise comparison logic
        if ai_numeric == gt_numeric:
            status = "CONFIRMED_RISK" if ai_numeric >= 1 else "NO_RISK_CONFIRMED"
        elif ai_numeric > gt_numeric:
            status = "UNVERIFIED_RISK"  # FP
        else:
            status = "MISSED_RISK"      # FN

        reasoning = res.get("matching_reasoning", f"So sánh cặp đôi AI ({ai_numeric}) vs Ground Truth ({gt_numeric}).")

        # Post-validation: Strict URL citation grounding
        matched_inc = None
        if cited_url and isinstance(cited_url, str):
            for inc in incidents:
                if inc.url.strip() == cited_url.strip():
                    matched_inc = inc
                    break

        # Fallback if LLM identified GT risk >= 1 but didn't return an exact URL string match
        if not matched_inc and incidents and gt_numeric >= 1:
            matched_inc = incidents[0]

        return IncidentMatchResult(
            claim_id=claim.claim_id,
            claim_text=claim.claim_text,
            matched_incident=matched_inc,
            ai_risk_numeric=ai_numeric,
            ground_truth_numeric=gt_numeric,
            ground_truth_label=gt_label,
            evidence_compatibility=compatibility,
            match_status=status,
            reasoning_chain=reasoning_chain,
            matching_reasoning=reasoning
        )
    except Exception as e:
        print(f"⚠️ Agent 3 Error matching claim {claim.claim_id}: {e}")
        gt_numeric = 0
        status = "NO_RISK_CONFIRMED" if ai_numeric == 0 else "UNVERIFIED_RISK"
        return IncidentMatchResult(
            claim_id=claim.claim_id,
            claim_text=claim.claim_text,
            matched_incident=incidents[0] if incidents else None,
            ai_risk_numeric=ai_numeric,
            ground_truth_numeric=gt_numeric,
            ground_truth_label="LOW_RISK",
            evidence_compatibility="NO_EVIDENCE",
            match_status=status,
            reasoning_chain=f"Chuỗi suy luận mặc định do lỗi LLM: {e}",
            matching_reasoning=f"Đối chiếu mặc định: {e}"
        )
