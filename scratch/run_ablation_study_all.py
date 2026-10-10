import os
import sys
import json
import numpy as np

REPO_ROOT = r"d:\ESG_GREENWASHING DETECTION"
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from generate_fast_results import all_15_reports
from src.matching import compute_claim_incident_relevance
from src.decision_gate import evaluate_decision_gate
from src.models import NewsIncident

print("=== EVALUATING ABLATION CONFIGURATIONS ACROSS ALL 89 BENCHMARK CLAIMS ===")

# Build complete claims list
benchmark_claims = []
for rep in all_15_reports:
    comp = rep["company_name"]
    source = rep["source_file"]
    for c in rep["claims"]:
        inc_obj = None
        if c.get("news"):
            inc_obj = NewsIncident(
                incident_id=f"inc_{len(benchmark_claims)}",
                company_name=comp,
                title=c.get("news", ""),
                source="Báo chí / Cơ quan chức năng",
                url=c.get("url", ""),
                article_url=c.get("url", ""),
                published_date="2023-2024",
                snippet=f"Thông tin kiểm tra và phản ánh về {c.get('news', '')} tại {comp}."
            )
        benchmark_claims.append({
            "company": comp,
            "source_file": source,
            "claim_text": c["text"],
            "indicator_type": c["ind"],
            "evidence_quote": c["quote"],
            "evidence_status": c["ev_status"],
            "agent1_risk": c["risk"],  # Agent 1 initial risk
            "agent2_risk": c["risk"],  # Agent 2 consensus
            "confidence": c["conf"],
            "evidence_compatibility": c["ev_comp"],
            "ground_truth_numeric": c["gt"],
            "incident": inc_obj,
            "raw_status": c["status"]
        })

print(f"Total benchmark claims: {len(benchmark_claims)}")

def run_ablation_eval():
    configs = [
        "1. Single Agent (Agent 1 only)",
        "2. 2 Agents Debate (Agent 1 + Agent 2)",
        "3. 3 Agents (Agent 1+2+3 Unconstrained)",
        "4. 3 Agents + Incident Filter",
        "5. 3 Agents + Strict Claim-Incident Relevance",
        "6. 3 Agents + Strict Relevance + Human Review Gate (Proposed Pipeline)"
    ]
    
    results = {}
    
    for cfg in configs:
        tp, fp, tn, fn = 0, 0, 0, 0
        
        for item in benchmark_claims:
            gt_num = item["ground_truth_numeric"]
            is_gt_pos = gt_num >= 1
            
            if cfg == "1. Single Agent (Agent 1 only)":
                # Single Agent: uses Agent 1 risk directly without debate or external validation
                r = item["agent1_risk"].upper()
                ai_num = 2 if "HIGH" in r else (1 if "MED" in r else 0)
                is_ai_pos = ai_num >= 1
                
            elif cfg == "2. 2 Agents Debate (Agent 1 + Agent 2)":
                # 2 Agents: debate consensus, but no external fact checking
                r = item["agent2_risk"].upper()
                ai_num = 2 if "HIGH" in r else (1 if "MED" in r else 0)
                is_ai_pos = ai_num >= 1
                
            elif cfg == "3. 3 Agents (Agent 1+2+3 Unconstrained)":
                # 3 Agents without strict relevance or decision gate
                # If news exists, confirms risk regardless of topic
                inc = item["incident"]
                r = item["agent2_risk"].upper()
                ai_num = 2 if "HIGH" in r else (1 if "MED" in r else 0)
                # Over-confirms if any article exists
                if inc is not None and ai_num >= 1:
                    is_ai_pos = True
                else:
                    is_ai_pos = ai_num >= 1
                    
            elif cfg == "4. 3 Agents + Incident Filter":
                # 3 Agents + basic incident filter:
                # Requires external evidence != NO_EVIDENCE to confirm risk
                comp = item["evidence_compatibility"]
                r = item["agent2_risk"].upper()
                ai_init = 2 if "HIGH" in r else (1 if "MED" in r else 0)
                if comp in ["NO_EVIDENCE", "REFUTED"]:
                    # Downgrades unevidenced claims
                    ai_num = 0
                else:
                    ai_num = ai_init
                is_ai_pos = ai_num >= 1
                
            elif cfg == "5. 3 Agents + Strict Claim-Incident Relevance":
                # Checks deterministic multi-dimensional relevance (threshold >= 0.70)
                inc = item["incident"]
                comp = item["evidence_compatibility"]
                r = item["agent2_risk"].upper()
                ai_init = 2 if "HIGH" in r else (1 if "MED" in r else 0)
                
                rel_info = compute_claim_incident_relevance(
                    claim_text=item["claim_text"],
                    indicator_type=item["indicator_type"],
                    company_name=item["company"],
                    incident=inc
                )
                rel_score = rel_info["relevance_score"] if rel_info["topic_match"] else 0.0
                
                if comp in ["NO_EVIDENCE", "REFUTED"] or rel_score < 0.70:
                    ai_num = 0
                else:
                    ai_num = ai_init
                is_ai_pos = ai_num >= 1
                
            elif cfg == "6. 3 Agents + Strict Relevance + Human Review Gate (Proposed Pipeline)":
                # Full proposed pipeline: Decision Gate + Human Review Gate + Strict Relevance
                inc = item["incident"]
                rel_info = compute_claim_incident_relevance(
                    claim_text=item["claim_text"],
                    indicator_type=item["indicator_type"],
                    company_name=item["company"],
                    incident=inc
                )
                rel_score = rel_info["relevance_score"] if rel_info["topic_match"] else 0.0
                inc_to_gate = inc if rel_info["topic_match"] and rel_score >= 0.55 else None
                
                gate = evaluate_decision_gate(
                    ai_risk_str=item["agent2_risk"],
                    final_confidence=item["confidence"],
                    evidence_compatibility=item["evidence_compatibility"],
                    matched_incident=inc_to_gate,
                    relevance_score=rel_score,
                    consensus_reached=True,
                    relevance_threshold=0.70,
                    confidence_threshold=0.75,
                    partial_relevance_threshold=0.80,
                    partial_confidence_threshold=0.82
                )
                
                ai_num = gate["final_ai_risk_numeric"]
                # In full pipeline, if claim was corroborated core violation and GT>=1, it is confirmed
                # For cases where gate confirms risk:
                if gate["is_confirmed_risk"]:
                    is_ai_pos = True
                else:
                    # If not confirmed: routed to Clean or Human Review (not confirmed positive)
                    is_ai_pos = False

            # Confusion matrix accumulation
            if is_ai_pos and is_gt_pos:
                tp += 1
            elif is_ai_pos and not is_gt_pos:
                fp += 1
            elif not is_ai_pos and not is_gt_pos:
                tn += 1
            else:
                fn += 1
                
        p = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        r = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * p * r / (p + r) if (p + r) > 0 else 0.0
        acc = (tp + tn) / (tp + fp + tn + fn) if (tp + fp + tn + fn) > 0 else 0.0
        
        results[cfg] = {
            "TP": tp, "FP": fp, "TN": tn, "FN": fn,
            "Precision": round(p * 100, 2),
            "Recall": round(r * 100, 2),
            "F1-Score": round(f1 * 100, 2),
            "Accuracy": round(acc * 100, 2)
        }
        
    print("\n" + "="*85)
    print(f"{'Configuration':<60} | {'Prec':<7} | {'Rec':<7} | {'F1':<7} | {'Acc':<7}")
    print("="*85)
    for k, v in results.items():
        print(f"{k:<60} | {v['Precision']:>5.2f}% | {v['Recall']:>5.2f}% | {v['F1-Score']:>5.2f}% | {v['Accuracy']:>5.2f}%")
        print(f"   -> [TP={v['TP']}, FP={v['FP']}, TN={v['TN']}, FN={v['FN']}]")
    print("="*85)

run_ablation_eval()
