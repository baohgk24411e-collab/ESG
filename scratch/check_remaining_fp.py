import glob
import json
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

files = sorted(glob.glob("output_results/*_result.json"))
for f in files:
    with open(f, "r", encoding="utf-8") as fp:
        d = json.load(fp)
        for m in d["incident_matches"]:
            if m["match_status"] in ["UNVERIFIED_RISK", "FP"]:
                print(f"Remaining FP [{d['company_name']}] File: {f}")
                print(f"  Claim ID: {m['claim_id']}")
                print(f"  Text: {m['claim_text']}")
                print(f"  AI: {m['ai_risk_numeric']} vs GT: {m['ground_truth_numeric']}")
                print(f"  Comp: {m['evidence_compatibility']}")
                inc = m.get("matched_incident")
                print(f"  Inc: {inc.get('title') if inc else 'None'}")
                print(f"  Reasoning: {m.get('matching_reasoning')}")
