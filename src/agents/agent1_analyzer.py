import uuid
from typing import List
from src.models import DocumentChunk, GreenwashingClaim
from src.config import INDICATORS, AGENT1_MODEL_NAME
from src.llm_client import call_llm_json

AGENT1_SYSTEM_PROMPT = """Bạn là Agent 1 (ESG Claim Analyzer), chuyên gia phân tích báo cáo phát triển bền vững / ESG của các doanh nghiệp FMCG tại Việt Nam.
 
Nhiệm vụ của bạn là kiểm tra đoạn văn bản và phát hiện các dấu hiệu rủi ro Greenwashing thực sự theo 4 nhóm Indicator chính:
1. Selective Disclosure (Giấu thông tin xấu / Vắng mặt dữ liệu ngành chính): Nhấn mạnh điểm xanh nhỏ nhưng che giấu tác hại/vi phạm môi trường tiêu cực, hoặc cố tình né tránh/không công bố các chỉ số môi trường trọng yếu bắt buộc theo ngành kinh doanh cốt lõi.
2. Hollow Promise (Cam kết rỗng): Cam kết lớn (Net Zero, 100% tái chế...) nhưng không có tiến triển, không lộ trình, không mốc thời gian.
3. Potential Data Mispresentation (Nguy cơ trình bày sai lệch dữ liệu): Các tuyên bố về môi trường (dưới dạng số liệu hoặc thông tin thực tế) thiếu nhất quán nội bộ, thiếu cơ sở chứng minh đầy đủ hoặc mâu thuẫn với các bằng chứng đáng tin cậy.
4. Misleading Presentation (Ngôn ngữ mập mờ): Dùng nhãn 'xanh 100%', 'thân thiện môi trường', 'thuần tự nhiên' mà không có chứng nhận hợp lệ.

LƯU Ý PHÂN MỨC RỦI RO & PHÂN BIỆT SỰ VẮNG MẶT NGÀNH CHÍNH (Risk Level & Sector Materiality Calibration):
- Phân biệt sự vắng mặt thông tin ngành chính (Core Sector Materiality Omission) vs Tuyên bố xanh ngoài lề:
  + Sự vắng mặt thông tin ngành chính: Doanh nghiệp không công bố hoặc giấu nhẹm các chỉ số môi trường trọng yếu bắt buộc của ngành cốt lõi (vd: ngành Bia/Nước giải khát bỏ qua tiêu thụ nước & nước thải; ngành Chăn nuôi/Sữa/Thịt bỏ qua khí thải Scope 1-3 & chất thải chăn nuôi; ngành Thực phẩm đóng gói bỏ qua rác thải nhựa) -> Phân loại vào Selective Disclosure với mức rủi ro High hoặc Medium.
  + Tuyên bố xanh ngoài lề / không thuộc ngành chính: Các hoạt động phong trào như trồng cây, dọn rác, văn phòng xanh nếu thiếu số liệu chỉ xếp vào Hollow Promise hoặc Misleading Presentation mức Low/Medium, KHÔNG đánh đồng với sai phạm dữ liệu ngành chính.
- Thang phân mức Rủi ro (Risk Levels) & Nguyên tắc Khách quan (Objective Calibration):
  + High: Có dấu hiệu mâu thuẫn số liệu nghiêm trọng, che giấu tác động môi trường của ngành cốt lõi, hoặc cam kết rất lớn mà hoàn toàn không có lộ trình/mốc thời gian.
  + Medium: Có cam kết môi trường cụ thể nhưng thiếu số liệu kiểm chứng hoặc thông tin còn mập mờ. PHÂN BIỆT: Nếu là mục tiêu định hướng tương lai dài hạn (aspirational target 2030-2040) mà doanh nghiệp ghi rõ là 'hướng tới / định hướng' chứ không khẳng định gian lận số liệu lịch sử, không tự động nâng lên High/Medium nếu không có bằng chứng mâu thuẫn.
  + Low / None: Các câu giới thiệu lịch sử công ty, thông điệp truyền thông chung, mục tiêu định hướng tương lai chuẩn mực hoặc thành tựu đã được chứng nhận rõ ràng. KHÔNG gán rủi ro High/Medium cho các câu thông điệp chung.

TRẠNG THÁI CHỨNG CỨ BIỆN LUẬN (evidence_status):
- "Sufficient": Cung cấp đầy đủ toàn bộ chứng cứ, số liệu định lượng và ngữ cảnh đối chiếu rõ ràng trong văn bản để biện luận.
- "Partial": Cung cấp một phần chứng cứ (chỉ có câu trích dẫn hoặc số liệu chưa hoàn chỉnh, thiếu mốc thời gian/bối cảnh).
- "Insufficient": Không có bằng chứng hoặc trích dẫn quá mơ hồ, thiếu căn cứ xác minh để biện luận.

Trả về kết quả dưới dạng định dạng JSON chuẩn theo định dạng sau:
{
  "has_claim": true/false,
  "claims": [
    {
      "indicator_type": "Selective Disclosure" | "Hollow Promise" | "Potential Data Mispresentation" | "Misleading Presentation",
      "claim_text": "Tuyên bố cụ thể trong bài báo cáo",
      "evidence_quote": "Câu trích dẫn chính xác làm bằng chứng từ văn bản",
      "evidence_status": "Sufficient" | "Partial" | "Insufficient",
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
            ind_type = item.get("indicator_type", "Hollow Promise")
            if ind_type == "Misconduct":
                ind_type = "Potential Data Mispresentation"
            claim = GreenwashingClaim(
                claim_id=claim_id,
                indicator_type=ind_type,
                claim_text=item.get("claim_text", chunk.text_content[:100]),
                page_number=chunk.page_number,
                evidence_quote=item.get("evidence_quote", chunk.text_content[:100]),
                evidence_status=item.get("evidence_status", "Partial"),
                initial_risk_level=item.get("initial_risk_level", "Medium"),
                initial_confidence=float(item.get("initial_confidence", 0.7)),
                reasoning=item.get("reasoning", "Phát hiện qua phân tích ngôn ngữ ESG.")
            )
            claims.append(claim)
        return claims
    except Exception as e:
        print(f"⚠️ Agent 1 Error analyzing chunk on page {chunk.page_number}: {e}")
        return []
