import unittest
import sys
import os

REPO_ROOT = r"d:\ESG_GREENWASHING DETECTION"
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from src.models import GreenwashingClaim, NewsIncident, ClaimDebateResult
from src.matching import compute_claim_incident_relevance
from src.decision_gate import evaluate_decision_gate


class TestImprovedPipeline(unittest.TestCase):
    """
    Mandatory Test Suite (Section M of Specification):
    Tests 1 to 8 covering matching, relevance, decision gating, and human review routing.
    """

    def test_1_wastewater_claim_and_wastewater_incident_strong_match(self):
        """Test 1: Claim về wastewater + Incident về wastewater => strong match (>= 0.75)."""
        claim_text = "Sabeco không công bố đầy đủ lượng nước thải thực tế xả ra môi trường tại các nhà máy."
        incident = NewsIncident(
            incident_id="inc_test_1",
            company_name="Sabeco",
            title="Nghệ An: Nghi vấn nước thải ô nhiễm từ KCN Bắc Vinh (khu vực Sabeco Sông Lam) xả ra môi trường",
            source="Báo Dân Việt",
            url="https://laodong.vn/moi-truong/sabeco-nuoc-thai.ldo",
            published_date="2024",
            snippet="Kiểm tra công tác xử lý nước thải và xả thải công nghiệp của Sabeco Sông Lam."
        )
        res = compute_claim_incident_relevance(
            claim_text=claim_text,
            indicator_type="Selective Disclosure",
            company_name="Sabeco",
            incident=incident
        )
        self.assertTrue(res["topic_match"], "Topic should match on wastewater/water domain")
        self.assertTrue(res["company_match"], "Company should match")
        self.assertGreaterEqual(res["relevance_score"], 0.75, f"Expected strong match >= 0.75, got {res['relevance_score']}")
        self.assertEqual(res["match_category"], "STRONG_MATCH")

    def test_2_packaging_claim_and_wastewater_incident_reject(self):
        """Test 2: Claim về packaging + Incident về wastewater => reject / low relevance (< 0.55)."""
        claim_text = "Sabeco đặt mục tiêu 100% bao bì tái chế và phân hủy sinh học vào năm 2040."
        incident = NewsIncident(
            incident_id="inc_test_2",
            company_name="Sabeco",
            title="Sabeco bị xử phạt do xả nước thải vượt tiêu chuẩn môi trường ra sông Lam",
            source="Báo Tài Nguyên & Môi Trường",
            url="https://baotainguyenmoitruong.vn/xa-thai-sabeco.html",
            published_date="2024",
            snippet="Xử lý nước thải vượt ngưỡng quy chuẩn kỹ thuật quốc gia."
        )
        res = compute_claim_incident_relevance(
            claim_text=claim_text,
            indicator_type="Hollow Promise",
            company_name="Sabeco",
            incident=incident
        )
        self.assertFalse(res["topic_match"], "Packaging claim should not match wastewater incident topic")
        self.assertLess(res["relevance_score"], 0.55, f"Expected rejection < 0.55, got {res['relevance_score']}")
        self.assertIn(res["match_category"], ["TOPIC_MISMATCH", "REJECT_LOW_RELEVANCE"])

    def test_3_carbon_claim_and_tax_violation_incident_reject(self):
        """Test 3: Claim về carbon emissions + Incident về tax violation => reject (< 0.55)."""
        claim_text = "Kido cam kết cắt giảm 25% phát thải khí nhà kính Scope 1 và Scope 2 đến năm 2030."
        incident = NewsIncident(
            incident_id="inc_test_3",
            company_name="Kido",
            title="Tập đoàn KIDO (KDC) bị phạt và truy thu thuế hơn 21 tỷ đồng sau thanh tra",
            source="Báo Thanh Niên",
            url="https://thanhnien.vn/kido-truy-thu-thue.html",
            published_date="2023",
            snippet="Tổng cục Thuế ban hành quyết định xử phạt vi phạm hành chính về thuế đối với Kido."
        )
        res = compute_claim_incident_relevance(
            claim_text=claim_text,
            indicator_type="Potential Data Mispresentation",
            company_name="Kido",
            incident=incident
        )
        self.assertFalse(res["topic_match"], "Carbon claim should not match purely financial/tax incident")
        self.assertLess(res["relevance_score"], 0.55, f"Expected rejection < 0.55, got {res['relevance_score']}")

    def test_4_same_company_different_topic_not_confirmed_risk(self):
        """Test 4: Same company nhưng incident khác topic => không được confirm risk."""
        claim_text = "Masan cam kết 100% bao bì sản phẩm tiêu dùng có thể tái chế vào năm 2035."
        incident = NewsIncident(
            incident_id="inc_test_4",
            company_name="Masan",
            title="Thu hồi đất ngoài quy hoạch của Công ty Núi Pháo (Masan) sau kết luận thanh tra",
            source="Báo Dân Trí",
            url="https://dantri.com.vn/nui-phao-dat-dai.html",
            published_date="2023",
            snippet="Thanh tra Bộ Tài nguyên và Môi trường thu hồi đất ngoài quy hoạch của Núi Pháo."
        )
        rel_info = compute_claim_incident_relevance(
            claim_text=claim_text,
            indicator_type="Hollow Promise",
            company_name="Masan",
            incident=incident
        )
        self.assertFalse(rel_info["topic_match"], "Packaging vs Land/Mining should not match topics")
        
        gate = evaluate_decision_gate(
            ai_risk_str="Medium",
            final_confidence=0.85,
            evidence_compatibility="NO_EVIDENCE",
            matched_incident=None if not rel_info["topic_match"] else incident,
            relevance_score=rel_info["relevance_score"],
            consensus_reached=True
        )
        self.assertFalse(gate["is_confirmed_risk"], "Risk must NOT be confirmed when topics diverge")
        self.assertEqual(gate["final_ai_risk_numeric"], 0)

    def test_5_no_exact_incident_matched_incident_is_none(self):
        """Test 5: No exact incident => matched_incident = None."""
        claim_text = "Vinamilk cam kết 100% bao bì tự hủy sinh học vào năm 2040."
        gate = evaluate_decision_gate(
            ai_risk_str="Medium",
            final_confidence=0.82,
            evidence_compatibility="NO_EVIDENCE",
            matched_incident=None,
            relevance_score=0.0,
            consensus_reached=True
        )
        self.assertFalse(gate["is_confirmed_risk"], "Cannot confirm risk when matched_incident is None")
        self.assertEqual(gate["final_ai_risk_numeric"], 0)

    def test_6_partial_compatibility_low_relevance_not_confirmed_risk(self):
        """Test 6: Partial compatibility + low relevance => không được CONFIRMED_RISK."""
        gate = evaluate_decision_gate(
            ai_risk_str="Medium",
            final_confidence=0.80,
            evidence_compatibility="PARTIALLY_COMPATIBLE",
            matched_incident=NewsIncident(
                incident_id="inc_test_6",
                company_name="TestCorp",
                title="Generic news article",
                source="News",
                url="https://example.com/news",
                published_date="2024",
                snippet="General mention."
            ),
            relevance_score=0.60,  # Below partial threshold 0.80
            consensus_reached=True
        )
        self.assertFalse(gate["is_confirmed_risk"], "Partial compatibility with low relevance must NOT confirm risk")
        self.assertEqual(gate["final_ai_risk_numeric"], 0)

    def test_7_high_compatibility_high_relevance_can_be_confirmed_risk(self):
        """Test 7: High compatibility + high relevance => có thể CONFIRMED_RISK."""
        gate = evaluate_decision_gate(
            ai_risk_str="High",
            final_confidence=0.88,
            evidence_compatibility="HIGHLY_COMPATIBLE",
            matched_incident=NewsIncident(
                incident_id="inc_test_7",
                company_name="Dabaco",
                title="UBND tỉnh Thanh Hóa xử phạt hơn 216 triệu đồng Dabaco do xả nước thải vượt quy chuẩn",
                source="Báo Lao Động",
                url="https://laodong.vn/moi-truong/xu-phat-dabaco.ldo",
                published_date="2024",
                snippet="Xả nước thải vượt quy chuẩn kỹ thuật quốc gia."
            ),
            relevance_score=0.88,
            consensus_reached=True
        )
        self.assertTrue(gate["is_confirmed_risk"], "High compatibility + high relevance should confirm risk")
        self.assertGreaterEqual(gate["final_ai_risk_numeric"], 1)
        self.assertEqual(gate["decision_status"], "CONFIRMED_RISK")

    def test_8_agent_disagreement_weak_evidence_human_review(self):
        """Test 8: Agent disagreement + weak evidence => human review."""
        gate = evaluate_decision_gate(
            ai_risk_str="Medium",
            final_confidence=0.72,  # Low confidence
            evidence_compatibility="PARTIALLY_COMPATIBLE",
            matched_incident=NewsIncident(
                incident_id="inc_test_8",
                company_name="Vinacafé",
                title="Bài báo về chứng nhận nông nghiệp",
                source="News",
                url="https://example.com/vinacafe",
                published_date="2024",
                snippet="Thảo luận về vùng trồng."
            ),
            relevance_score=0.68,
            consensus_reached=False  # Agent disagreement
        )
        self.assertFalse(gate["is_confirmed_risk"], "Disagreement and weak evidence must NOT confirm risk")
        self.assertTrue(gate["human_review_required"], "Case must be routed to human review")
        self.assertEqual(gate["decision_status"], "HUMAN_REVIEW_REQUIRED")


if __name__ == "__main__":
    unittest.main()
