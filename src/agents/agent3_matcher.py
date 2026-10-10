from typing import List, Optional
from src.models import ClaimDebateResult, NewsIncident, IncidentMatchResult
from src.config import AGENT3_MODEL_NAME
from src.llm_client import call_llm_json
from src.matching import compute_claim_incident_relevance
from src.decision_gate import evaluate_decision_gate

AGENT3_SYSTEM_PROMPT = """Bạn là Agent 3 (Incident Matcher & Validation Agent).
Nhiệm vụ của bạn là đối chiếu phán đoán Rủi ro từ Agent 1&2 của MỘT TUYÊN BỐ CỤ THỂ với DỮ LIỆU SỰ KIỆN THỰC TẾ (Báo chí, xử phạt) liên quan trực tiếp đến chủ đề tuyên bố đó.

QUY TẮC NGUYÊN TẮC QUAN TRỌNG VỀ ĐÁNH GIÁ (TRÁNH GẮN MÁC TUYỆT ĐỐI):
1. ĐÁNH GIÁ TÍNH LIÊN QUAN TRƯỚC KHI ĐÁNH GIÁ RỦI RO (Relevance First):
   - Bắt buộc kiểm tra: Công ty (company_match), Chủ đề môi trường (topic_match), Thời gian (time_match), Cơ sở/Chi nhánh (entity_match).
   - Nếu bài báo không cùng chủ đề môi trường với tuyên bố (ví dụ: Claim về bao bì nhưng bài báo về nước thải, hoặc Claim về phát thải nhưng bài báo về vi phạm thuế): BẮT BUỘC đặt topic_match=false và claim_incident_relevance < 0.50, cited_url=null.
   - TUYỆT ĐỐI KHÔNG dùng bài báo chỉ vì cùng tên công ty.
2. THANG ĐÁNH GIÁ MỨC ĐỘ TƯƠNG THÍCH BẰNG CHỨNG (Evidence Compatibility):
   - HIGHLY_COMPATIBLE: Bằng chứng thực tế/báo chí xác nhận trực tiếp vi phạm/rủi ro cụ thể cùng chủ đề với tuyên bố.
   - PARTIALLY_COMPATIBLE: Bằng chứng có liên quan về chủ đề nhưng không phản ánh vi phạm trực tiếp của chính tuyên bố này. Không tự động kết luận vi phạm nặng.
   - REFUTED: Có văn bản/tin tức chính thức xác nhận thông tin cảnh báo rủi ro là hoàn toàn sai sự thật.
   - NO_EVIDENCE: Không có thông tin/bài báo tiêu cực nào liên quan trực tiếp đến tuyên bố này.

3. QUY TẮC RÀNG BUỘC TRÍCH DẪN (CITATION GROUNDING):
   - Chỉ chọn URL trong danh sách METADATA được cung cấp bên dưới.
   - Nếu không có bài báo nào liên quan trực tiếp đến chủ đề tuyên bố, đặt cited_url: null.

Trả về định dạng JSON chuẩn:
{
  "reasoning_chain": "Bước 1: Phân tích tuyên bố... -> Bước 2: Kiểm tra topic_match và company_match... -> Bước 3: Tính điểm relevance... -> Bước 4: Chốt mức độ tương thích.",
  "company_match": true | false,
  "topic_match": true | false,
  "time_match": true | false,
  "entity_match": true | false,
  "claim_incident_relevance": 0.0 - 1.0,
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


def normalize_url_for_matching(url: Optional[str]) -> str:
    """Normalizes URL for exact matching (strips whitespace and trailing slashes)."""
    if not url or not isinstance(url, str):
        return ""
    return url.strip().rstrip("/")


def exact_normalized_url_match(url1: Optional[str], url2: Optional[str]) -> bool:
    """Checks whether two URLs match identically after trimming and normalizing trailing slashes."""
    if not url1 or not url2:
        return False
    u1 = normalize_url_for_matching(url1)
    u2 = normalize_url_for_matching(url2)
    if not u1 or not u2:
        return False
    return u1.lower() == u2.lower()


def match_claim_with_incidents(
    debate_result: ClaimDebateResult,
    incidents: List[NewsIncident],
    company_name: str = ""
) -> IncidentMatchResult:
    """
    Agent 3 matches AI prediction against specific topic Ground Truth risk levels,
    enforcing deterministic relevance scoring, decision gate, and human review gate.
    """
    claim = debate_result.claim
    ai_risk_str = debate_result.final_risk_level
    ai_numeric_raw = map_risk_str_to_numeric(ai_risk_str)
    ai_conf = debate_result.final_confidence
    consensus = debate_result.consensus_reached

    # Filter incidents using deterministic multi-dimensional relevance
    filtered_incidents = []
    for inc in incidents:
        rel_info = compute_claim_incident_relevance(
            claim_text=claim.claim_text,
            indicator_type=claim.indicator_type,
            company_name=company_name or inc.company_name,
            incident=inc
        )
        if rel_info["relevance_score"] >= 0.55 and rel_info["topic_match"]:
            filtered_incidents.append((inc, rel_info))

    # Sort candidates by relevance
    filtered_incidents.sort(key=lambda x: x[1]["relevance_score"], reverse=True)

    # Structure metadata explicitly for Agent 3 with candidate incidents
    top_candidates = [item[0] for item in filtered_incidents[:3]]
    incidents_text = "\n".join([
        f"--- [NGUỒN METADATA #{i+1}] ---\n"
        f"Title: {inc.title[:120]}\n"
        f"Source: {inc.source[:60]}\n"
        f"Publish Date: {inc.published_date}\n"
        f"URL (Exact): {inc.article_url or inc.url}\n"
        f"Snippet Content: {inc.snippet[:180]}...\n"
        for i, inc in enumerate(top_candidates)
    ])

    prompt = f"""
CHỦ ĐỀ TUYÊN BỐ ESG: [{claim.indicator_type}]
DOANH NGHIỆP: {company_name}
TRÍCH DẪN BÁO CÁO: "{claim.claim_text[:200]}"
- AI Risk Level (Agent 1+2): {ai_risk_str} (Điểm số AI sơ bộ: {ai_numeric_raw}, Confidence: {ai_conf})

DANH SÁCH METADATA BÀI BÁO THỰC TẾ CÀO ĐƯỢC (Chỉ chọn URL trong danh sách này nếu đúng chủ đề):
{incidents_text if incidents_text else "Không tìm thấy bài báo vi phạm nào cùng chủ đề."}

Hãy thực hiện chuỗi suy luận từng bước (reasoning_chain), kiểm tra topic_match và tính điểm claim_incident_relevance trước khi chốt evidence_compatibility.
"""
    try:
        res = call_llm_json(prompt, AGENT3_SYSTEM_PROMPT, model_name=AGENT3_MODEL_NAME)
        cited_url = res.get("cited_url")
        compatibility = res.get("evidence_compatibility", "NO_EVIDENCE").upper()
        reasoning_chain = res.get("reasoning_chain", res.get("matching_reasoning", ""))
        llm_topic_match = res.get("topic_match", True)
        llm_relevance = float(res.get("claim_incident_relevance", 0.0))

        # Ground Truth Level from LLM/Data
        gt_label = res.get("ground_truth_level") or "LOW_RISK"
        if not isinstance(gt_label, str):
            gt_label = "LOW_RISK"
        gt_numeric = int(res.get("ground_truth_numeric", map_risk_str_to_numeric(gt_label)))

        # Strict URL & Incident Matching
        matched_inc = None
        best_rel_score = 0.0

        if cited_url and isinstance(cited_url, str) and llm_topic_match:
            cited_clean = cited_url.strip()
            for inc in incidents:
                candidates = [inc.article_url, inc.url]
                if any(c and exact_normalized_url_match(c, cited_clean) for c in candidates):
                    # Verify deterministic relevance
                    rel_check = compute_claim_incident_relevance(
                        claim_text=claim.claim_text,
                        indicator_type=claim.indicator_type,
                        company_name=company_name or inc.company_name,
                        incident=inc
                    )
                    if rel_check["topic_match"] and rel_check["relevance_score"] >= 0.55:
                        matched_inc = inc
                        best_rel_score = rel_check["relevance_score"]
                        break

        # Fallback to top deterministic filtered candidate only if relevance >= 0.75 and LLM confirms compatibility
        if not matched_inc and filtered_incidents and compatibility in ["HIGHLY_COMPATIBLE", "PARTIALLY_COMPATIBLE"]:
            top_inc, top_rel = filtered_incidents[0]
            if top_rel["relevance_score"] >= 0.75:
                matched_inc = top_inc
                best_rel_score = top_rel["relevance_score"]

        # Strict Rule: If no match or topic mismatch -> matched_incident = None and compatibility = NO_EVIDENCE
        if not matched_inc or not llm_topic_match or best_rel_score < 0.55:
            matched_inc = None
            if compatibility in ["HIGHLY_COMPATIBLE"]:
                compatibility = "NO_EVIDENCE"

        # Tighten Evidence Compatibility for Ground Truth:
        if compatibility in ["REFUTED", "NO_EVIDENCE"] or matched_inc is None:
            gt_numeric = 0
            gt_label = "LOW_RISK"
            compatibility = "NO_EVIDENCE" if compatibility != "REFUTED" else "REFUTED"
        elif compatibility in ["PARTIALLY_COMPATIBLE"]:
            # PARTIALLY_COMPATIBLE does not automatically elevate GT risk to High
            gt_numeric = 1
            gt_label = "MODERATE_RISK"
        elif compatibility in ["HIGHLY_COMPATIBLE"]:
            gt_numeric = max(1, gt_numeric)
            gt_label = "HIGH_RISK" if gt_numeric >= 2 else "MODERATE_RISK"

        # Apply Decision Gate & Human Review Gate
        gate_res = evaluate_decision_gate(
            ai_risk_str=ai_risk_str,
            final_confidence=ai_conf,
            evidence_compatibility=compatibility,
            matched_incident=matched_inc,
            relevance_score=best_rel_score,
            consensus_reached=consensus
        )

        final_ai_numeric = gate_res["final_ai_risk_numeric"]

        # Final pairwise comparison between gated AI risk and Ground Truth
        if gate_res["decision_status"] == "HUMAN_REVIEW_REQUIRED":
            status = "HUMAN_REVIEW_REQUIRED"
        elif final_ai_numeric == gt_numeric:
            status = "CONFIRMED_RISK" if final_ai_numeric >= 1 else "NO_RISK_CONFIRMED"
        elif final_ai_numeric > gt_numeric:
            status = "UNVERIFIED_RISK"  # FP
        else:
            status = "MISSED_RISK"      # FN

        reasoning = (
            f"Gate: {gate_res['decision_status']} | Relevance={best_rel_score:.2f} | "
            f"Comp={compatibility} | AI={final_ai_numeric} vs GT={gt_numeric}. {gate_res['gate_reason']}"
        )

        return IncidentMatchResult(
            claim_id=claim.claim_id,
            claim_text=claim.claim_text,
            matched_incident=matched_inc,
            ai_risk_numeric=final_ai_numeric,
            ground_truth_numeric=gt_numeric,
            ground_truth_label=gt_label,
            evidence_compatibility=compatibility,
            match_status=status,
            reasoning_chain=reasoning_chain,
            matching_reasoning=reasoning
        )
    except Exception as e:
        print(f"⚠️ Agent 3 Error matching claim {claim.claim_id}: {e}")
        return IncidentMatchResult(
            claim_id=claim.claim_id,
            claim_text=claim.claim_text,
            matched_incident=None,
            ai_risk_numeric=0,
            ground_truth_numeric=0,
            ground_truth_label="LOW_RISK",
            evidence_compatibility="NO_EVIDENCE",
            match_status="NO_RISK_CONFIRMED",
            reasoning_chain=f"Chuỗi suy luận mặc định do lỗi LLM: {e}",
            matching_reasoning=f"Đối chiếu mặc định: {e}"
        )
