import glob
import json
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

files = sorted(glob.glob("output_results/*_result.json"))
missed_tps = []
for f in files:
    with open(f, "r", encoding="utf-8") as fp:
        d = json.load(fp)
        for m in d["incident_matches"]:
            if m["ground_truth_numeric"] >= 1 and m["match_status"] in ["MISSED_RISK", "FN", "HUMAN_REVIEW_REQUIRED"]:
                missed_tps.append({
                    "company": d["company_name"],
                    "claim_id": m["claim_id"],
                    "claim_text": m["claim_text"],
                    "ai_risk_numeric": m["ai_risk_numeric"],
                    "gt": m["ground_truth_numeric"],
                    "comp": m["evidence_compatibility"],
                    "incident": m.get("matched_incident"),
                    "reasoning": m.get("matching_reasoning"),
                    "status": m["match_status"]
                })

print(f"Total Missed (FN): {len(missed_tps)}")
for i, item in enumerate(missed_tps, 1):
    inc = item["incident"]
    print(f"\nFN #{i} [{item['company']}] Claim: {item['claim_id']}")
    print(f"  Text: {item['claim_text']}")
    print(f"  AI: {item['ai_risk_numeric']} vs GT: {item['gt']} | Comp: {item['comp']}")
    print(f"  Inc Title: {inc.get('title') if inc else 'None'}")
    print(f"  Reasoning: {item['reasoning']}")
