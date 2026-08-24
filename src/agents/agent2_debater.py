from typing import List
from src.models import GreenwashingClaim, DebateTurn, ClaimDebateResult, DocumentChunk
from src.config import MAX_DEBATE_ROUNDS, AGENT1_MODEL_NAME, AGENT2_MODEL_NAME
from src.llm_client import call_llm_json

AGENT2_SYSTEM_PROMPT = """Bạn là Agent 2 (Devil's Advocate - Chuyên gia phản biện độc lập).
Nhiệm vụ của bạn là phản biện lại đánh giá rủi ro Greenwashing của Agent 1 nhằm tránh kết luận vội vã, ảo giác (hallucination) hoặc thổi phồng rủi ro.

Hãy soi xét kỹ:
1. Đánh giá của Agent 1 có quá nghiêm khắc hay thiếu căn cứ không?
2. Có thông tin nào trong đoạn văn gốc minh oan hoặc giải thích cho doanh nghiệp không?
3. Đề xuất giữ nguyên, tăng hoặc giảm mức độ Rủi ro (Risk Level: High, Medium, Low, None) và Độ tin cậy (Confidence Level).

Trả về kết quả chuẩn JSON:
{
  "argument": "Lời phản biện chi tiết của Agent 2",
  "proposed_risk_level": "High" | "Medium" | "Low" | "None",
  "proposed_confidence": 0.80,
  "missing_evidence_requested": "Yêu cầu thêm bằng chứng nếu cần"
}
"""

AGENT1_DEFENSE_PROMPT = """Bạn là Agent 1 (ESG Claim Analyzer), tiếp nhận lời phản biện từ Agent 2 (Devil's Advocate).
Hãy trả lời phản biện của Agent 2, bảo vệ hoặc điều chỉnh đánh giá của bạn dựa trên bằng chứng văn bản.

Trả về kết quả chuẩn JSON:
{
  "argument": "Câu trả lời phản biện và bảo vệ lập luận của Agent 1",
  "proposed_risk_level": "High" | "Medium" | "Low" | "None",
  "proposed_confidence": 0.85,
  "consensus_agreed": true/false
}
"""


def run_debate_loop(claim: GreenwashingClaim, chunk: DocumentChunk) -> ClaimDebateResult:
    """
    Run up to MAX_DEBATE_ROUNDS debate turns between Agent 1 and Agent 2.
    """
    debate_history: List[DebateTurn] = []
    
    current_risk = claim.initial_risk_level
    current_confidence = claim.initial_confidence
    consensus = False

    for round_num in range(1, MAX_DEBATE_ROUNDS + 1):
        # --- Turn A: Agent 2 Critiques Agent 1 ---
        agent2_prompt = f"""
Đoạn văn bản gốc (Trang {chunk.page_number}):
"{chunk.text_content}"

Tuyên bố được Agent 1 phát hiện:
- Phân loại: {claim.indicator_type}
- Claim: "{claim.claim_text}"
- Mức độ rủi ro sơ bộ Agent 1 đưa ra: {current_risk} (Confidence: {current_confidence})
- Lý do của Agent 1: {claim.reasoning}

Lịch sử phản biện trước đó: {[turn.dict() for turn in debate_history]}

Hãy đưa ra phản biện gay gắt và đề xuất Risk Level / Confidence điều chỉnh.
"""
        try:
            res_a2 = call_llm_json(agent2_prompt, AGENT2_SYSTEM_PROMPT, model_name=AGENT2_MODEL_NAME)
            turn2 = DebateTurn(
                round_number=round_num,
                agent_name="Agent 2 (Devil Advocate)",
                argument=res_a2.get("argument", "Cần xem xét kỹ chứng nhận môi trường."),
                proposed_risk_level=res_a2.get("proposed_risk_level", current_risk),
                proposed_confidence=float(res_a2.get("proposed_confidence", current_confidence)),
                missing_evidence_requested=res_a2.get("missing_evidence_requested")
            )
            debate_history.append(turn2)

            # Check consensus (if Agent 2 agrees with current risk level)
            if turn2.proposed_risk_level == current_risk:
                consensus = True
                break

            # --- Turn B: Agent 1 Responds & Re-evaluates ---
            agent1_prompt = f"""
Agent 2 vừa phản biện như sau:
"{turn2.argument}"
Mức rủi ro Agent 2 đề xuất: {turn2.proposed_risk_level}

Văn bản gốc: "{chunk.text_content}"

Hãy phản hồi lại Agent 2 và đưa ra mức Risk Level sau khi xem xét phản biện.
"""
            res_a1 = call_llm_json(agent1_prompt, AGENT1_DEFENSE_PROMPT, model_name=AGENT1_MODEL_NAME)
            turn1 = DebateTurn(
                round_number=round_num,
                agent_name="Agent 1 (Claimant)",
                argument=res_a1.get("argument", "Tiếp thu ý kiến phản biện."),
                proposed_risk_level=res_a1.get("proposed_risk_level", turn2.proposed_risk_level),
                proposed_confidence=float(res_a1.get("proposed_confidence", turn2.proposed_confidence)),
                missing_evidence_requested=None
            )
            debate_history.append(turn1)

            current_risk = turn1.proposed_risk_level
            current_confidence = turn1.proposed_confidence

            if res_a1.get("consensus_agreed") or (turn1.proposed_risk_level == turn2.proposed_risk_level):
                consensus = True
                break

        except Exception as e:
            print(f"⚠️ Error in debate round {round_num}: {e}")
            break

    # Summarize final result and check Human-in-the-Loop flag
    human_review = not consensus
    disagreement_note = None
    if human_review:
        last_turn_risk = debate_history[-1].proposed_risk_level if debate_history else current_risk
        disagreement_note = f"⚠️ BẤT ĐỒNG Ý KIẾN: Agent 1 chốt rủi ro '{current_risk}', trong khi Agent 2 đề xuất '{last_turn_risk}' sau {len(debate_history)} lượt phản biện. Cần Chuyên gia ESG (Human-in-the-loop) can thiệp thẩm định."

    summary = f"Sau {len(debate_history)} lượt phản biện giữa Agent 1 và Agent 2, hai bên {'đã đạt đồng thuận' if consensus else 'CHƯA ĐỒNG THUẬN (Cần con người can thiệp)'}. Mức rủi ro chốt: {current_risk}."

    return ClaimDebateResult(
        claim=claim,
        debate_history=debate_history,
        final_risk_level=current_risk,
        final_confidence=current_confidence,
        consensus_reached=consensus,
        human_review_required=human_review,
        disagreement_note=disagreement_note,
        debate_summary=summary
    )
