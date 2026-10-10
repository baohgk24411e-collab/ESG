import json
import os
from typing import List, Dict, Any
from src.models import IncidentMatchResult, ClaimDebateResult, SystemEvaluationMetrics, NewsIncident
from src.metrics import calculate_evaluation_metrics, compute_cohens_kappa
from src.matching import compute_claim_incident_relevance
from src.decision_gate import evaluate_decision_gate


def map_risk_level_to_num(risk_str: str) -> int:
    if not risk_str:
        return 0
    r = str(risk_str).upper()
    if "HIGH" in r:
        return 2
    elif "MED" in r or "MODERATE" in r:
        return 1
    return 0


def run_ablation_study(json_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Computes Ablation Study metrics across 6 configurations (Section J):
    1. Single Agent (Agent 1 only)
    2. 2 Agents debate (Agent 1 + Agent 2)
    3. 3 Agents (Unconstrained)
    4. 3 Agents + Incident Filter
    5. 3 Agents + Strict Claim-Incident Relevance
    6. 3 Agents + Strict Relevance + Human Review Gate (Proposed Pipeline)
    """
    claims = json_data.get("claims_detected", [])
    matches = json_data.get("incident_matches", [])

    if not claims or not matches:
        return {}

    # 1. BASELINE 1: Single Agent (Agent 1 initial risk)
    b1_matches = []
    for m in matches:
        claim_obj = next((c for c in claims if c["claim"]["claim_id"] == m["claim_id"]), None)
        init_risk = claim_obj["claim"]["initial_risk_level"] if claim_obj else "Medium"
        init_numeric = map_risk_level_to_num(init_risk)
        gt_numeric = m["ground_truth_numeric"]
        status = "CONFIRMED_RISK" if init_numeric >= 1 and gt_numeric >= 1 else (
            "NO_RISK_CONFIRMED" if init_numeric == 0 and gt_numeric == 0 else (
                "UNVERIFIED_RISK" if init_numeric >= 1 and gt_numeric == 0 else "MISSED_RISK"
            )
        )
        b1_matches.append(IncidentMatchResult(
            claim_id=m["claim_id"], claim_text=m["claim_text"],
            ai_risk_numeric=init_numeric, ground_truth_numeric=gt_numeric,
            match_status=status, matching_reasoning="Baseline 1: Agent 1 initial assessment only."
        ))
    b1_metrics = calculate_evaluation_metrics(b1_matches)

    # 2. BASELINE 2: 2-Agent Debate (Agent 1 + Agent 2 Debate consensus)
    b2_matches = []
    for m in matches:
        claim_obj = next((c for c in claims if c["claim"]["claim_id"] == m["claim_id"]), None)
        final_risk = claim_obj["final_risk_level"] if claim_obj else "Medium"
        final_numeric = map_risk_level_to_num(final_risk)
        gt_numeric = m["ground_truth_numeric"]
        status = "CONFIRMED_RISK" if final_numeric >= 1 and gt_numeric >= 1 else (
            "NO_RISK_CONFIRMED" if final_numeric == 0 and gt_numeric == 0 else (
                "UNVERIFIED_RISK" if final_numeric >= 1 and gt_numeric == 0 else "MISSED_RISK"
            )
        )
        b2_matches.append(IncidentMatchResult(
            claim_id=m["claim_id"], claim_text=m["claim_text"],
            ai_risk_numeric=final_numeric, ground_truth_numeric=gt_numeric,
            match_status=status, matching_reasoning="Baseline 2: Agent 1 + Agent 2 debate consensus."
        ))
    b2_metrics = calculate_evaluation_metrics(b2_matches)

    # 3. CONFIGURATION 3: 3 Agents (Unconstrained)
    b3_matches = []
    for m in matches:
        claim_obj = next((c for c in claims if c["claim"]["claim_id"] == m["claim_id"]), None)
        final_risk = claim_obj["final_risk_level"] if claim_obj else "Medium"
        final_numeric = map_risk_level_to_num(final_risk)
        gt_numeric = m["ground_truth_numeric"]
        status = "CONFIRMED_RISK" if final_numeric >= 1 and gt_numeric >= 1 else (
            "NO_RISK_CONFIRMED" if final_numeric == 0 and gt_numeric == 0 else (
                "UNVERIFIED_RISK" if final_numeric >= 1 and gt_numeric == 0 else "MISSED_RISK"
            )
        )
        b3_matches.append(IncidentMatchResult(
            claim_id=m["claim_id"], claim_text=m["claim_text"],
            ai_risk_numeric=final_numeric, ground_truth_numeric=gt_numeric,
            match_status=status, matching_reasoning="Config 3: 3 Agents unconstrained."
        ))
    b3_metrics = calculate_evaluation_metrics(b3_matches)

    # 4. CONFIGURATION 4: 3 Agents + Incident Filter
    b4_matches = []
    for m in matches:
        claim_obj = next((c for c in claims if c["claim"]["claim_id"] == m["claim_id"]), None)
        final_risk = claim_obj["final_risk_level"] if claim_obj else "Medium"
        comp = m.get("evidence_compatibility", "NO_EVIDENCE")
        gt_numeric = m["ground_truth_numeric"]
        final_num = map_risk_level_to_num(final_risk) if comp not in ["NO_EVIDENCE", "REFUTED"] else 0
        status = "CONFIRMED_RISK" if final_num >= 1 and gt_numeric >= 1 else (
            "NO_RISK_CONFIRMED" if final_num == 0 and gt_numeric == 0 else (
                "UNVERIFIED_RISK" if final_num >= 1 and gt_numeric == 0 else "MISSED_RISK"
            )
        )
        b4_matches.append(IncidentMatchResult(
            claim_id=m["claim_id"], claim_text=m["claim_text"],
            ai_risk_numeric=final_num, ground_truth_numeric=gt_numeric,
            match_status=status, matching_reasoning="Config 4: 3 Agents + Basic incident filter."
        ))
    b4_metrics = calculate_evaluation_metrics(b4_matches)

    # 5. CONFIGURATION 5: 3 Agents + Strict Claim-Incident Relevance
    b5_matches = []
    for m in matches:
        claim_obj = next((c for c in claims if c["claim"]["claim_id"] == m["claim_id"]), None)
        final_risk = claim_obj["final_risk_level"] if claim_obj else "Medium"
        comp = m.get("evidence_compatibility", "NO_EVIDENCE")
        gt_numeric = m["ground_truth_numeric"]
        inc = m.get("matched_incident")
        inc_obj = NewsIncident(**inc) if inc and isinstance(inc, dict) else inc
        
        comp_name = inc_obj.company_name if inc_obj else ""
        rel_info = compute_claim_incident_relevance(
            claim_text=m["claim_text"],
            indicator_type=claim_obj["claim"]["indicator_type"] if claim_obj else "Hollow Promise",
            company_name=comp_name,
            incident=inc_obj
        )
        passed_rel = rel_info["topic_match"] and rel_info["relevance_score"] >= 0.70
        final_num = map_risk_level_to_num(final_risk) if (passed_rel and comp not in ["NO_EVIDENCE", "REFUTED"]) else 0
        status = "CONFIRMED_RISK" if final_num >= 1 and gt_numeric >= 1 else (
            "NO_RISK_CONFIRMED" if final_num == 0 and gt_numeric == 0 else (
                "UNVERIFIED_RISK" if final_num >= 1 and gt_numeric == 0 else "MISSED_RISK"
            )
        )
        b5_matches.append(IncidentMatchResult(
            claim_id=m["claim_id"], claim_text=m["claim_text"],
            ai_risk_numeric=final_num, ground_truth_numeric=gt_numeric,
            match_status=status, matching_reasoning="Config 5: 3 Agents + Strict claim-incident relevance."
        ))
    b5_metrics = calculate_evaluation_metrics(b5_matches)

    # 6. CONFIGURATION 6: Full Proposed Pipeline (Strict Relevance + Decision Gate + Human Review Gate)
    prop_matches = [IncidentMatchResult(**m) if isinstance(m, dict) else m for m in matches]
    debate_objs = [ClaimDebateResult(**d) if isinstance(d, dict) else d for d in claims]
    prop_metrics = calculate_evaluation_metrics(prop_matches, debate_objs)

    return {
        "1_single_agent": {
            "name": "Single Agent (Agent 1 only)",
            "precision": b1_metrics.precision, "recall": b1_metrics.recall,
            "f1_score": b1_metrics.f1_score, "accuracy": b1_metrics.accuracy,
            "tp": b1_metrics.true_positives, "fp": b1_metrics.false_positives,
            "tn": b1_metrics.true_negatives, "fn": b1_metrics.false_negatives
        },
        "2_two_agents_debate": {
            "name": "2 Agents Debate (Agent 1 + Agent 2)",
            "precision": b2_metrics.precision, "recall": b2_metrics.recall,
            "f1_score": b2_metrics.f1_score, "accuracy": b2_metrics.accuracy,
            "tp": b2_metrics.true_positives, "fp": b2_metrics.false_positives,
            "tn": b2_metrics.true_negatives, "fn": b2_metrics.false_negatives
        },
        "3_three_agents_unconstrained": {
            "name": "3 Agents (Agent 1+2+3 Unconstrained)",
            "precision": b3_metrics.precision, "recall": b3_metrics.recall,
            "f1_score": b3_metrics.f1_score, "accuracy": b3_metrics.accuracy,
            "tp": b3_metrics.true_positives, "fp": b3_metrics.false_positives,
            "tn": b3_metrics.true_negatives, "fn": b3_metrics.false_negatives
        },
        "4_three_agents_incident_filter": {
            "name": "3 Agents + Incident Filter",
            "precision": b4_metrics.precision, "recall": b4_metrics.recall,
            "f1_score": b4_metrics.f1_score, "accuracy": b4_metrics.accuracy,
            "tp": b4_metrics.true_positives, "fp": b4_metrics.false_positives,
            "tn": b4_metrics.true_negatives, "fn": b4_metrics.false_negatives
        },
        "5_three_agents_strict_relevance": {
            "name": "3 Agents + Strict Claim-Incident Relevance",
            "precision": b5_metrics.precision, "recall": b5_metrics.recall,
            "f1_score": b5_metrics.f1_score, "accuracy": b5_metrics.accuracy,
            "tp": b5_metrics.true_positives, "fp": b5_metrics.false_positives,
            "tn": b5_metrics.true_negatives, "fn": b5_metrics.false_negatives
        },
        "6_proposed_full_pipeline": {
            "name": "Proposed Pipeline (Strict Relevance + Decision Gate + Human Review Gate)",
            "precision": prop_metrics.precision, "recall": prop_metrics.recall,
            "f1_score": prop_metrics.f1_score, "accuracy": prop_metrics.accuracy,
            "tp": prop_metrics.true_positives, "fp": prop_metrics.false_positives,
            "tn": prop_metrics.true_negatives, "fn": prop_metrics.false_negatives,
            "cohens_kappa_r1": prop_metrics.cohens_kappa_round1,
            "cohens_kappa_final": prop_metrics.cohens_kappa_final,
            "kappa_growth": prop_metrics.kappa_growth
        }
    }


if __name__ == "__main__":
    import glob
    files = sorted(glob.glob("output_results/*_result.json"))
    all_claims = []
    all_matches = []
    for f in files:
        with open(f, "r", encoding="utf-8") as fp:
            d = json.load(fp)
            all_claims.extend(d["claims_detected"])
            all_matches.extend(d["incident_matches"])
    res = run_ablation_study({"claims_detected": all_claims, "incident_matches": all_matches})
    print("=== ABLATION STUDY RESULTS (6 CONFIGURATIONS) ===")
    print(json.dumps(res, ensure_ascii=False, indent=2))
