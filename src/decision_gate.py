from typing import Dict, Any, Optional, Tuple
from src.models import GreenwashingClaim, NewsIncident, ClaimDebateResult


# Research-backed Validation Threshold Defaults
DEFAULT_RELEVANCE_THRESHOLD = 0.70
DEFAULT_CONFIDENCE_THRESHOLD = 0.75
DEFAULT_PARTIAL_RELEVANCE_THRESHOLD = 0.75
DEFAULT_PARTIAL_CONFIDENCE_THRESHOLD = 0.78


def evaluate_decision_gate(
    ai_risk_str: str,
    final_confidence: float,
    evidence_compatibility: str,
    matched_incident: Optional[NewsIncident],
    relevance_score: float,
    consensus_reached: bool = True,
    relevance_threshold: float = DEFAULT_RELEVANCE_THRESHOLD,
    confidence_threshold: float = DEFAULT_CONFIDENCE_THRESHOLD,
    partial_relevance_threshold: float = DEFAULT_PARTIAL_RELEVANCE_THRESHOLD,
    partial_confidence_threshold: float = DEFAULT_PARTIAL_CONFIDENCE_THRESHOLD
) -> Dict[str, Any]:
    """
    Evaluates Decision Gate and Human Review Gate before confirming a greenwashing risk.
    Guarantees that unevidenced, aspirational, or low-relevance claims are never falsely confirmed.
    """
    risk_upper = str(ai_risk_str).upper()
    is_medium_or_high = ("HIGH" in risk_upper) or ("MED" in risk_upper) or ("MODERATE" in risk_upper)
    comp_upper = str(evidence_compatibility).upper()

    # Rule 1: No incident or NO_EVIDENCE
    if matched_incident is None or comp_upper in ["NO_EVIDENCE", "REFUTED"]:
        return {
            "final_ai_risk_numeric": 0,
            "final_ai_risk_label": "Low" if not is_medium_or_high else "Low",
            "decision_status": "NO_RISK_CONFIRMED" if not is_medium_or_high else "UNVERIFIED_ASPIRATIONAL",
            "is_confirmed_risk": False,
            "human_review_required": False,
            "gate_reason": "Không có chứng cứ ngoại cảnh hoặc bài báo phủ định vi phạm (NO_EVIDENCE / REFUTED) -> Không xác nhận vi phạm."
        }

    # Rule 2: Low Relevance (< 0.55) -> Reject Match
    if relevance_score < 0.55:
        return {
            "final_ai_risk_numeric": 0,
            "final_ai_risk_label": "Low",
            "decision_status": "REJECTED_LOW_RELEVANCE",
            "is_confirmed_risk": False,
            "human_review_required": False,
            "gate_reason": f"Sự kiện có độ liên quan quá thấp ({relevance_score:.2f} < 0.55) -> Bác bỏ sự kiện đối chiếu."
        }

    # Rule 3: Human Review Gate Triggers
    needs_human_review = False
    review_reasons = []

    if not consensus_reached:
        needs_human_review = True
        review_reasons.append("Agent 1 và Agent 2 bất đồng quan điểm sau các vòng phản biện.")

    if final_confidence < confidence_threshold:
        needs_human_review = True
        review_reasons.append(f"Độ tin cậy mô hình thấp ({final_confidence:.2f} < {confidence_threshold}).")

    if 0.55 <= relevance_score < relevance_threshold:
        needs_human_review = True
        review_reasons.append(f"Độ tương thích sự kiện ở mức trung bình ({relevance_score:.2f} < {relevance_threshold}).")

    # Rule 4: Stricter Gate for PARTIALLY_COMPATIBLE
    if comp_upper == "PARTIALLY_COMPATIBLE":
        if relevance_score < partial_relevance_threshold or final_confidence < partial_confidence_threshold:
            needs_human_review = True
            review_reasons.append(
                f"Bằng chứng gián tiếp (PARTIALLY_COMPATIBLE) chưa đủ ngưỡng xác nhận vi phạm chặt chẽ "
                f"(Relevance {relevance_score:.2f}/{partial_relevance_threshold}, Conf {final_confidence:.2f}/{partial_confidence_threshold})."
            )

    # If routed to Human Review Gate
    if needs_human_review:
        return {
            "final_ai_risk_numeric": 0,  # Human review cases are NOT counted as positive
            "final_ai_risk_label": "Low (Under Review)",
            "decision_status": "HUMAN_REVIEW_REQUIRED",
            "is_confirmed_risk": False,
            "human_review_required": True,
            "gate_reason": f"Chuyển hội đồng chuyên gia thẩm định (Human Review): {'; '.join(review_reasons)}"
        }

    # Rule 5: Pass all gates -> CONFIRMED_RISK
    if is_medium_or_high and (
        (comp_upper == "HIGHLY_COMPATIBLE" and relevance_score >= relevance_threshold and final_confidence >= confidence_threshold) or
        (comp_upper == "PARTIALLY_COMPATIBLE" and relevance_score >= partial_relevance_threshold and final_confidence >= partial_confidence_threshold)
    ):
        ai_num = 2 if "HIGH" in risk_upper else 1
        return {
            "final_ai_risk_numeric": ai_num,
            "final_ai_risk_label": "High" if ai_num == 2 else "Medium",
            "decision_status": "CONFIRMED_RISK",
            "is_confirmed_risk": True,
            "human_review_required": False,
            "gate_reason": f"Thỏa mãn toàn bộ điều kiện Decision Gate: Risk={risk_upper}, Rel={relevance_score:.2f}, Comp={comp_upper}, Conf={final_confidence:.2f}."
        }

    # Default fallback
    return {
        "final_ai_risk_numeric": 0,
        "final_ai_risk_label": "Low",
        "decision_status": "NO_RISK_CONFIRMED",
        "is_confirmed_risk": False,
        "human_review_required": False,
        "gate_reason": "Không đủ điều kiện xác nhận vi phạm môi trường."
    }
