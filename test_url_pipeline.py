import sys
import unittest
from unittest.mock import patch
from src.models import NewsIncident, GreenwashingClaim, ClaimDebateResult
from src.incident_crawler import (
    is_valid_direct_article_url,
    construct_search_query,
    construct_google_search_url,
    verify_article_identity,
    search_environmental_incidents,
    VERIFIED_COMPANY_INCIDENTS
)
from src.agents.agent3_matcher import (
    match_claim_with_incidents,
    exact_normalized_url_match,
    normalize_url_for_matching
)

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')


class TestUrlPipeline(unittest.TestCase):

    def test_1_valid_direct_article_structure(self):
        """TEST 1: Valid direct article URL should be validated and accepted."""
        test_url = "https://laodong.vn/moi-truong/example-123456.ldo"
        self.assertTrue(is_valid_direct_article_url(test_url))

        # Test incident construction
        inc = NewsIncident(
            incident_id="inc_test1",
            company_name="TestCorp",
            title="Example environmental violation",
            source="Báo Lao Động",
            url=test_url,
            article_url=test_url,
            search_query="TestCorp Example environmental violation",
            search_url=construct_google_search_url("TestCorp Example environmental violation"),
            article_url_status="VERIFIED_EXACT",
            published_date="2024",
            snippet="Test violation snippet"
        )
        self.assertIsNotNone(inc.article_url)
        self.assertEqual(inc.article_url, test_url)
        self.assertEqual(inc.article_url_status, "VERIFIED_EXACT")
        self.assertIn("google.com/search", inc.search_url)

    def test_2_homepage_and_search_urls_rejected(self):
        """TEST 2: Publisher root homepage and search engine URLs must be rejected as direct article URL."""
        self.assertFalse(is_valid_direct_article_url("https://laodong.vn/"))
        self.assertFalse(is_valid_direct_article_url("https://tuoitre.vn/"))
        self.assertFalse(is_valid_direct_article_url("https://tuoitre.vn/home"))
        self.assertFalse(is_valid_direct_article_url("https://www.google.com/search?q=example"))
        self.assertFalse(is_valid_direct_article_url("https://vnexpress.net/search.html?q=example"))

    def test_3_positive_test_vinamilk_verified_exact(self):
        """TEST 3 (Positive Test): Vinamilk direct article URL is verified -> VERIFIED_EXACT."""
        vnm_record = VERIFIED_COMPANY_INCIDENTS["vinamilk"][0]
        url = vnm_record["url"]
        title = vnm_record["title"]
        self.assertTrue(is_valid_direct_article_url(url))

        status = verify_article_identity(url, "Vinamilk", title)
        self.assertEqual(status, "VERIFIED_EXACT")

        incidents = search_environmental_incidents("Vinamilk", max_results=1, force_refresh=True)
        self.assertGreater(len(incidents), 0)
        vnm_inc = incidents[0]
        self.assertEqual(vnm_inc.article_url_status, "VERIFIED_EXACT")
        self.assertIsNotNone(vnm_inc.article_url)
        self.assertIsNotNone(vnm_inc.search_url)

    def test_4_negative_test_sabeco_rejected_mismatch(self):
        """TEST 4 (Negative Test): Sabeco URL redirected to unrelated topic (bưởi) -> REJECTED_MISMATCH."""
        sab_record = VERIFIED_COMPANY_INCIDENTS["sabeco"][0]
        url = sab_record["url"]
        title = sab_record["title"]

        status = verify_article_identity(url, "Sabeco", title)
        self.assertEqual(status, "REJECTED_MISMATCH")

        incidents = search_environmental_incidents("Sabeco", max_results=1, force_refresh=True)
        self.assertGreater(len(incidents), 0)
        sab_inc = incidents[0]
        self.assertEqual(sab_inc.article_url_status, "REJECTED_MISMATCH")
        # Direct article_url is stripped when rejected so user cannot open wrong article
        self.assertIsNone(sab_inc.article_url)
        # Search URL remains available as fallback
        self.assertIsNotNone(sab_inc.search_url)

    def test_5_habeco_search_url_is_unavailable(self):
        """TEST 5: Habeco search URL is classified as UNAVAILABLE for direct link."""
        hab_record = VERIFIED_COMPANY_INCIDENTS["habeco"][0]
        url = hab_record["url"]
        title = hab_record["title"]

        status = verify_article_identity(url, "Habeco", title)
        self.assertEqual(status, "UNAVAILABLE")

    def test_6_agent3_exact_url_match_grounding(self):
        """TEST 6: LLM cited_url matching incident B exactly sets matched_incident = B."""
        inc_a = NewsIncident(
            incident_id="inc_a",
            company_name="BeerCo",
            title="Nước thải vượt tiêu chuẩn",
            source="Báo A",
            url="https://laodong.vn/moi-truong/nuoc-thai-123.ldo",
            article_url="https://laodong.vn/moi-truong/nuoc-thai-123.ldo",
            search_query="BeerCo Nước thải",
            search_url="https://www.google.com/search?q=BeerCo+nuoc+thai",
            article_url_status="VERIFIED_EXACT",
            published_date="2024",
            snippet="Wastewater issue"
        )
        inc_b = NewsIncident(
            incident_id="inc_b",
            company_name="BeerCo",
            title="Bao bì tái chế",
            source="Báo B",
            url="https://tuoitre.vn/moi-truong/bao-bi-tai-che-456.htm",
            article_url="https://tuoitre.vn/moi-truong/bao-bi-tai-che-456.htm",
            search_query="BeerCo Bao bì",
            search_url="https://www.google.com/search?q=BeerCo+bao+bi",
            article_url_status="VERIFIED_EXACT",
            published_date="2024",
            snippet="Packaging issue"
        )
        claim = GreenwashingClaim(
            claim_id="c_1",
            indicator_type="Selective Disclosure",
            claim_text="Chưa công bố bao bì tái chế",
            page_number=10,
            evidence_quote="Cam kết tái chế",
            evidence_status="Partial",
            initial_risk_level="Medium",
            initial_confidence=0.85,
            reasoning="Chưa có báo cáo định lượng"
        )
        debate_res = ClaimDebateResult(
            claim=claim,
            debate_history=[],
            final_risk_level="Medium",
            final_confidence=0.85,
            consensus_reached=True,
            human_review_required=False,
            debate_summary="Debate summary"
        )

        mock_llm_response = {
            "reasoning_chain": "Step 1 -> Step 2",
            "evidence_compatibility": "HIGHLY_COMPATIBLE",
            "ground_truth_level": "MODERATE_RISK",
            "ground_truth_numeric": 1,
            "cited_url": "https://tuoitre.vn/moi-truong/bao-bi-tai-che-456.htm",
            "matching_reasoning": "Khớp với bài B"
        }

        with patch("src.agents.agent3_matcher.call_llm_json", return_value=mock_llm_response):
            match_res = match_claim_with_incidents(debate_res, [inc_a, inc_b])
            self.assertIsNotNone(match_res.matched_incident)
            self.assertEqual(match_res.matched_incident.incident_id, "inc_b")

    def test_7_agent3_hallucinated_url_no_fallback(self):
        """TEST 7: LLM hallucinated cited_url must result in matched_incident = None (NO fallback to incidents[0])."""
        inc_a = NewsIncident(
            incident_id="inc_a",
            company_name="BeerCo",
            title="Nước thải vượt tiêu chuẩn",
            source="Báo A",
            url="https://laodong.vn/moi-truong/nuoc-thai-123.ldo",
            article_url="https://laodong.vn/moi-truong/nuoc-thai-123.ldo",
            search_query="BeerCo Nước thải",
            search_url="https://www.google.com/search?q=BeerCo+nuoc+thai",
            article_url_status="VERIFIED_EXACT",
            published_date="2024",
            snippet="Wastewater issue"
        )
        claim = GreenwashingClaim(
            claim_id="c_2",
            indicator_type="Selective Disclosure",
            claim_text="Chưa công bố bao bì tái chế",
            page_number=10,
            evidence_quote="Cam kết tái chế",
            evidence_status="Partial",
            initial_risk_level="High",
            initial_confidence=0.90,
            reasoning="Thiếu minh bạch"
        )
        debate_res = ClaimDebateResult(
            claim=claim,
            debate_history=[],
            final_risk_level="High",
            final_confidence=0.90,
            consensus_reached=True,
            human_review_required=False,
            debate_summary="Debate summary"
        )

        mock_llm_response = {
            "reasoning_chain": "Step 1 -> Step 2",
            "evidence_compatibility": "HIGHLY_COMPATIBLE",
            "ground_truth_level": "HIGH_RISK",
            "ground_truth_numeric": 2,
            "cited_url": "https://random-invented-news.vn/fake-article-999.html",  # Hallucinated
            "matching_reasoning": "LLM hallucinated URL"
        }

        with patch("src.agents.agent3_matcher.call_llm_json", return_value=mock_llm_response):
            match_res = match_claim_with_incidents(debate_res, [inc_a])
            self.assertIsNone(match_res.matched_incident, "Must NOT fall back to incidents[0]!")

    def test_8_dashboard_template_no_silent_substitution(self):
        """TEST 8: Verify dashboard template JavaScript logic never silently substitutes bestScrapeInc."""
        from generate_dashboard import TEMPLATE_HTML
        self.assertNotIn("matchRes.matched_incident || bestScrapeInc", TEMPLATE_HTML)
        self.assertIn("const matchedInc = matchRes.matched_incident || null;", TEMPLATE_HTML)
        self.assertIn("🔎 Search Google", TEMPLATE_HTML)
        self.assertIn("↗ Open Article", TEMPLATE_HTML)
        self.assertIn("isVerifiedDirect", TEMPLATE_HTML)


if __name__ == "__main__":
    unittest.main()
