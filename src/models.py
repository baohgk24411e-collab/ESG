from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class DocumentChunk(BaseModel):
    chunk_id: str
    company_name: str
    source_file: str
    page_number: int
    text_content: str
    relevance_score: float = 0.0


class GreenwashingClaim(BaseModel):
    claim_id: str
    indicator_type: str = Field(..., description="One of: Selective Disclosure, Hollow Promise, Misconduct, Misleading Presentation")
    claim_text: str = Field(..., description="Tuyên bố hoặc đoạn văn bản nghi vấn greenwashing")
    page_number: int = Field(..., description="Trang chứa tuyên bố trong báo cáo")
    evidence_quote: str = Field(..., description="Trích dẫn bằng chứng cụ thể từ đoạn văn")
    initial_risk_level: str = Field(..., description="Mức độ rủi ro sơ bộ: High, Medium, Low, None")
    initial_confidence: float = Field(..., description="Độ tin cậy sơ bộ từ 0.0 đến 1.0")
    reasoning: str = Field(..., description="Lý do phân loại và đánh giá rủi ro")


class DebateTurn(BaseModel):
    round_number: int
    agent_name: str = Field(..., description="Agent 1 (Claimant) or Agent 2 (Devil Advocate)")
    argument: str = Field(..., description="Lập luận hoặc phản biện")
    proposed_risk_level: str = Field(..., description="Mức độ rủi ro đề xuất (High, Medium, Low, None)")
    proposed_confidence: float = Field(..., description="Độ tin cậy đề xuất (0.0 đến 1.0)")
    missing_evidence_requested: Optional[str] = Field(None, description="Bằng chứng bổ sung cần yêu cầu")


class ClaimDebateResult(BaseModel):
    claim: GreenwashingClaim
    debate_history: List[DebateTurn] = []
    final_risk_level: str
    final_confidence: float
    consensus_reached: bool
    human_review_required: bool = Field(False, description="Cờ cảnh báo cần con người (Human-in-the-loop) can thiệp giải quyết bất đồng")
    disagreement_note: Optional[str] = Field(None, description="Ghi chú chi tiết bất đồng ý kiến giữa Agent 1 và Agent 2")
    debate_summary: str


class NewsIncident(BaseModel):
    incident_id: str
    company_name: str
    title: str
    source: str
    url: str
    published_date: str
    snippet: str
    relevance_score: float = 0.0


class IncidentMatchResult(BaseModel):
    claim_id: str
    claim_text: str
    matched_incident: Optional[NewsIncident] = None
    ai_risk_numeric: int = 0
    ground_truth_numeric: int = 0
    ground_truth_label: str = "LOW_RISK"
    evidence_compatibility: str = Field("NO_EVIDENCE", description="HIGHLY_COMPATIBLE, PARTIALLY_COMPATIBLE, REFUTED, NO_EVIDENCE")
    match_status: str = Field(..., description="CONFIRMED_RISK (TP), UNVERIFIED_RISK (FP), NO_RISK_CONFIRMED (TN), MISSED_RISK (FN)")
    reasoning_chain: str = Field("", description="Chuỗi suy luận từng bước của Agent 3 trước khi ra nhãn")
    matching_reasoning: str


class SystemEvaluationMetrics(BaseModel):
    true_positives: int = 0
    false_positives: int = 0
    true_negatives: int = 0
    false_negatives: int = 0
    precision: float = 0.0
    recall: float = 0.0
    f1_score: float = 0.0
    accuracy: float = 0.0
    cohens_kappa_round1: float = Field(0.0, description="Chỉ số đồng thuận Cohen's Kappa Vòng 1")
    cohens_kappa_final: float = Field(0.0, description="Chỉ số đồng thuận Cohen's Kappa Vòng cuối")
    kappa_growth: float = Field(0.0, description="Mức tăng trưởng đồng thuận giữa Agent 1 và Agent 2 qua các vòng")
    indicator_cohens_kappa: Dict[str, Dict[str, Any]] = Field(default_factory=dict, description="Chỉ số Cohen's Kappa phân theo từng Indicator")


class FullPipelineOutput(BaseModel):
    company_name: str
    source_file: str
    total_chunks_processed: int
    relevant_chunks_count: int
    claims_detected: List[ClaimDebateResult]
    scraped_incidents: List[NewsIncident]
    incident_matches: List[IncidentMatchResult]
    metrics: SystemEvaluationMetrics
