import sys
import os

REPO_ROOT = r"d:\ESG_GREENWASHING DETECTION"
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from generate_fast_results import all_15_reports
from src.matching import compute_claim_incident_relevance
from src.models import NewsIncident

tps = []
for rep in all_15_reports:
    comp = rep["company_name"]
    for c in rep["claims"]:
        if c.get("status") == "CONFIRMED_RISK" and c.get("gt", 0) >= 1:
            inc_obj = NewsIncident(
                incident_id="inc_tp",
                company_name=comp,
                title=c.get("news", ""),
                source="News",
                url=c.get("url", ""),
                article_url=c.get("url", ""),
                published_date="2024",
                snippet=c.get("news", "")
            )
            rel_info = compute_claim_incident_relevance(
                claim_text=c["text"],
                indicator_type=c["ind"],
                company_name=comp,
                incident=inc_obj
            )
            tps.append({
                "company": comp,
                "claim": c["text"][:70],
                "news": c.get("news"),
                "comp": c.get("ev_comp"),
                "rel_score": rel_info["relevance_score"],
                "topic_match": rel_info["topic_match"],
                "domains": rel_info.get("matched_domains", [])
            })

print(f"Total TPs: {len(tps)}")
print("Distribution of relevance scores for TPs:")
for t in tps:
    print(f"[{t['company']}] Rel={t['rel_score']} | Comp={t['comp']} | Topic={t['topic_match']} | Claim: {t['claim']} | News: {t['news']}")
