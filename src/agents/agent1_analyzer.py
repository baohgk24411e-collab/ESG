import uuid
from typing import List
from src.models import DocumentChunk, GreenwashingClaim
from src.config import INDICATORS, AGENT1_MODEL_NAME
from src.llm_client import call_llm_json

AGENT1_SYSTEM_PROMPT = """Bạn là Agent 1 (ESG Claim Analyzer), chuyên gia phân tích báo cáo phát triển bền vững / ESG của các doanh nghiệp FMCG tại Việt Nam.

Nhiệm vụ của bạn là kiểm tra đoạn văn bản và phát hiện các dấu hiệu rủi ro Greenwashing thực sự theo 4 nhóm Indicator chính:
1. Selective Disclosure (Giấu thông tin xấu): Nhấn mạnh điểm xanh nhỏ nhưng che giấu tác hại/vi phạm môi trường tiêu cực.
2. Hollow Promise (Cam kết rỗng): Cam kết lớn (Net Zero, 100% tái chế...) nhưng không có tiến triển, không lộ trình, không mốc thời gian.
3. Misconduct (Sai phạm số liệu): Số liệu bất thường, mâu thuẫn hoặc thổi phồng số liệu môi trường.
4. Misleading Presentation (Ngôn ngữ mập mờ): Dùng nhãn 'xanh 100%', 'thân thiện môi trường', 'thuần tự nhiên' mà không có chứng nhận hợp lệ.

LƯU Ý PHÂN MỨC RỦI RO (Risk Level Calibration):
- High: Có dấu hiệu mâu thuẫn số liệu nghiêm trọng hoặc cam kết rất lớn mà hoàn toàn không có lộ trình/mốc thời gian.
- Medium: Có cam kết môi trường cụ thể nhưng thiếu số liệu kiểm chứng hoặc thông tin còn mập mờ.
- Low / None: Các câu giới thiệu lịch sử công ty, thông điệp truyền thông chung, sứ mệnh doanh nghiệp hoặc thành tựu đã được chứng nhận rõ ràng. KHÔNG gán rủi ro High/Medium cho các câu thông điệp chung.

Trả về kết quả dưới dạng định dạng JSON chuẩn theo định dạng sau:
{
  "has_claim": true/false,
  "claims": [
    {
      "indicator_type": "Selective Disclosure" | "Hollow Promise" | "Misconduct" | "Misleading Presentation",
      "claim_text": "Tuyên bố cụ thể trong bài báo cáo",
      "evidence_quote": "Câu trích dẫn chính xác làm bằng chứng từ văn bản",
      "initial_risk_level": "High" | "Medium" | "Low" | "None",
      "initial_confidence": 0.85,
      "reasoning": "Lý do phân tích và đánh giá tại sao đây là rủi ro greenwashing"
    }
  ]
}
"""


def analyze_chunk_for_claims(chunk: DocumentChunk) -> List[GreenwashingClaim]:
    """Analyze a single text chunk using Agent 1."""
    prompt = f"""
Hãy phân tích đoạn văn bản sau từ Báo cáo ESG của công ty {chunk.company_name} (Trang {chunk.page_number}):

--- NỘI DUNG ĐOẠN VĂN ---
{chunk.text_content}
--- KẾT THÚC ---

Phát hiện tất cả các tuyên bố có dấu hiệu Greenwashing hoặc cam kết môi trường cần được kiểm chứng. Trả về đúng JSON theo yêu cầu.
"""
    try:
        res = call_llm_json(prompt, AGENT1_SYSTEM_PROMPT, model_name=AGENT1_MODEL_NAME)
        if not res.get("has_claim") or not res.get("claims"):
            return []

        claims = []
        for item in res.get("claims", []):
            claim_id = f"claim_{uuid.uuid4().hex[:8]}"
            claim = GreenwashingClaim(
                claim_id=claim_id,
                indicator_type=item.get("indicator_type", "Hollow Promise"),
                claim_text=item.get("claim_text", chunk.text_content[:100]),
                page_number=chunk.page_number,
                evidence_quote=item.get("evidence_quote", chunk.text_content[:100]),
                initial_risk_level=item.get("initial_risk_level", "Medium"),
                initial_confidence=float(item.get("initial_confidence", 0.7)),
                reasoning=item.get("reasoning", "Phát hiện qua phân tích ngôn ngữ ESG.")
            )
            claims.append(claim)
        return claims
    except Exception as e:
        print(f"⚠️ Agent 1 Error analyzing chunk on page {chunk.page_number}: {e}")
        return []
