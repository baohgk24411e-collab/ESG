import json
import os
from typing import List, Dict, Any
from src.models import IncidentMatchResult, ClaimDebateResult, SystemEvaluationMetrics
from src.metrics import calculate_evaluation_metrics, compute_cohens_kappa


def run_ablation_study(json_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Computes Ablation Study metrics across 3 configurations:
    1. Baseline 1: Single Agent (Agent 1 only)
    2. Baseline 2: 2-Agent System (Agent 1 + Agent 2 Debate)
    3. Proposed Pipeline: Full 3-Agent System + Incident Filtering
    """
    claims = json_data.get("claims_detected", [])
    matches = json_data.get("incident_matches", [])

    if not claims or not matches:
        return {}

    # --- BASELINE 1: Single Agent (Agent 1 initial risk) ---
    b1_matches = []
    for m in matches:
        claim_obj = next((c for c in claims if c["claim"]["claim_id"] == m["claim_id"]), None)
        initial_risk = claim_obj["claim"]["initial_risk_level"] if claim_obj else "Medium"
        initial_numeric = 3 if "HIGH" in initial_risk.upper() else (2 if "MED" in initial_risk.upper() else (1 if "LOW" in initial_risk.upper() else 0))
        gt_numeric = m["ground_truth_numeric"]

        if initial_numeric == gt_numeric:
            status = "CONFIRMED_RISK" if initial_numeric >= 1 else "NO_RISK_CONFIRMED"
        elif initial_numeric > gt_numeric:
            status = "UNVERIFIED_RISK"  # FP
        else:
            status = "MISSED_RISK"      # FN

        b1_matches.append(IncidentMatchResult(
            claim_id=m["claim_id"],
            claim_text=m["claim_text"],
            ai_risk_numeric=initial_numeric,
            ground_truth_numeric=gt_numeric,
            match_status=status,
            matching_reasoning="Baseline 1: Agent 1 initial assessment only."
        ))

    b1_metrics = calculate_evaluation_metrics(b1_matches)

    # --- BASELINE 2: 2-Agent System (Agent 1 + Agent 2 debate consensus) ---
    b2_matches = []
    for m in matches:
        claim_obj = next((c for c in claims if c["claim"]["claim_id"] == m["claim_id"]), None)
        final_risk = claim_obj["final_risk_level"] if claim_obj else "Low"
        final_numeric = 3 if "HIGH" in final_risk.upper() else (2 if "MED" in final_risk.upper() else (1 if "LOW" in final_risk.upper() else 0))
        gt_numeric = m["ground_truth_numeric"]

        if final_numeric == gt_numeric:
            status = "CONFIRMED_RISK" if final_numeric >= 1 else "NO_RISK_CONFIRMED"
        elif final_numeric > gt_numeric:
            status = "UNVERIFIED_RISK"
        else:
            status = "MISSED_RISK"

        b2_matches.append(IncidentMatchResult(
            claim_id=m["claim_id"],
            claim_text=m["claim_text"],
            ai_risk_numeric=final_numeric,
            ground_truth_numeric=gt_numeric,
            match_status=status,
            matching_reasoning="Baseline 2: Agent 1 + Agent 2 debate consensus."
        ))

    b2_metrics = calculate_evaluation_metrics(b2_matches)

    # --- PROPOSED PIPELINE: Full 3-Agent System + Incident Filtering ---
    prop_matches = [IncidentMatchResult(**m) for m in matches]
    debate_objs = [ClaimDebateResult(**d) for d in claims]
    prop_metrics = calculate_evaluation_metrics(prop_matches, debate_objs)

    ablation_result = {
        "baseline_1_single_agent": {
            "name": "Baseline 1 (Single Agent - Agent 1 only)",
            "precision": b1_metrics.precision,
            "recall": b1_metrics.recall,
            "f1_score": b1_metrics.f1_score,
            "accuracy": b1_metrics.accuracy,
            "tp": b1_metrics.true_positives,
            "fp": b1_metrics.false_positives,
            "tn": b1_metrics.true_negatives,
            "fn": b1_metrics.false_negatives
        },
        "baseline_2_two_agents": {
            "name": "Baseline 2 (2 Agents - Agent 1 + Agent 2 Debate)",
            "precision": b2_metrics.precision,
            "recall": b2_metrics.recall,
            "f1_score": b2_metrics.f1_score,
            "accuracy": b2_metrics.accuracy,
            "tp": b2_metrics.true_positives,
            "fp": b2_metrics.false_positives,
            "tn": b2_metrics.true_negatives,
            "fn": b2_metrics.false_negatives
        },
        "proposed_pipeline": {
            "name": "Proposed Pipeline (Full 3 Agents + Incident Filter)",
            "precision": prop_metrics.precision,
            "recall": prop_metrics.recall,
            "f1_score": prop_metrics.f1_score,
            "accuracy": prop_metrics.accuracy,
            "tp": prop_metrics.true_positives,
            "fp": prop_metrics.false_positives,
            "tn": prop_metrics.true_negatives,
            "fn": prop_metrics.false_negatives,
            "cohens_kappa_r1": prop_metrics.cohens_kappa_round1,
            "cohens_kappa_final": prop_metrics.cohens_kappa_final,
            "kappa_growth": prop_metrics.kappa_growth
        }
    }

    return ablation_result


if __name__ == "__main__":
    json_path = "output_results.json"
    if os.path.exists(json_path):
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        res = run_ablation_study(data)
        print("=== ABLATION STUDY RESULTS ===")
        print(json.dumps(res, ensure_ascii=False, indent=2))
