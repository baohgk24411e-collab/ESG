from typing import List, Dict, Any
from src.models import IncidentMatchResult, SystemEvaluationMetrics, ClaimDebateResult


def compute_cohens_kappa(rater1_levels: List[str], rater2_levels: List[str]) -> float:
    """
    Calculate Cohen's Kappa Coefficient (kappa) between Agent 1 and Agent 2.
    kappa = (p_o - p_e) / (1 - p_e)
    Note: For small samples (n < 3), applies smoothing to avoid inflated kappa=1.0
    """
    if not rater1_levels or len(rater1_levels) != len(rater2_levels):
        return 0.0

    n = len(rater1_levels)
    categories = ["HIGH", "MEDIUM", "MODERATE", "LOW", "NONE"]

    agreements = sum(1 for a, b in zip(rater1_levels, rater2_levels) if a.upper() == b.upper())
    p_o = agreements / n

    p_e = 0.0
    for cat in categories:
        cnt1 = sum(1 for a in rater1_levels if cat in a.upper())
        cnt2 = sum(1 for b in rater2_levels if cat in b.upper())
        p_e += (cnt1 / n) * (cnt2 / n)

    # For small samples (n < 3), perfect agreement (p_o == 1.0) is statistically
    # unreliable — apply Laplace smoothing to avoid inflated kappa=1.0
    if n < 3 and p_o == 1.0:
        # Smooth: treat as if there was 1 slight disagreement out of (n + 2) virtual obs
        p_o = (agreements + 1) / (n + 2)

    if p_e >= 1.0:
        return 1.0

    kappa = (p_o - p_e) / (1.0 - p_e)
    return round(max(0.0, min(1.0, kappa)), 4)


def compute_per_indicator_kappa(debate_results: List[ClaimDebateResult]) -> Dict[str, Dict[str, Any]]:
    """
    Calculate Cohen's Kappa metrics individually for each of the 4 ESG indicators.
    """
    indicators = [
        "Selective Disclosure",
        "Hollow Promise",
        "Potential Data Mispresentation",
        "Misleading Presentation"
    ]
    
    per_indicator_metrics = {}

    if not debate_results:
        # No debate data yet — return zeros (do not use fake hardcoded baseline)
        return {
            "Selective Disclosure": {"kappa_round1": 0.0, "kappa_final": 0.0, "kappa_growth": 0.0, "claim_count": 0},
            "Hollow Promise": {"kappa_round1": 0.0, "kappa_final": 0.0, "kappa_growth": 0.0, "claim_count": 0},
            "Potential Data Mispresentation": {"kappa_round1": 0.0, "kappa_final": 0.0, "kappa_growth": 0.0, "claim_count": 0},
            "Misleading Presentation": {"kappa_round1": 0.0, "kappa_final": 0.0, "kappa_growth": 0.0, "claim_count": 0}
        }

    for ind in indicators:
        # Match claims for this indicator (supporting both Potential Data Mispresentation and legacy Misconduct)
        ind_key = "misconduct" if ind == "Potential Data Mispresentation" else ind.lower()
        matching_claims = [
            d for d in debate_results 
            if ind.lower() in d.claim.indicator_type.lower() or ind_key in d.claim.indicator_type.lower()
        ]
        
        r1_a1, r1_a2 = [], []
        fin_a1, fin_a2 = [], []

        for d in matching_claims:
            hist = d.debate_history
            if len(hist) >= 2:
                # Round 1: Agent 1 initial vs first Agent 2 critique
                a1_init = hist[0].proposed_risk_level
                a2_first = next((t for t in hist if "Agent 2" in t.agent_name), hist[1])
                r1_a1.append(a1_init)
                r1_a2.append(a2_first.proposed_risk_level)

                # Final round: last Agent 1 turn vs last Agent 2 turn
                a1_last = hist[-1].proposed_risk_level
                a2_turns = [t for t in hist if "Agent 2" in t.agent_name]
                a2_last = a2_turns[-1].proposed_risk_level if a2_turns else a2_first.proposed_risk_level
                fin_a1.append(a1_last)
                fin_a2.append(a2_last)
            else:
                r1_a1.append(d.claim.initial_risk_level)
                r1_a2.append(d.final_risk_level)
                fin_a1.append(d.final_risk_level)
                fin_a2.append(d.final_risk_level)

        if r1_a1 and r1_a2:
            k_r1 = compute_cohens_kappa(r1_a1, r1_a2)
            k_fin = compute_cohens_kappa(fin_a1, fin_a2)
            growth = round(max(0.0, k_fin - k_r1), 4)
        else:
            # No data for this indicator in this report
            k_r1, k_fin, growth = 0.0, 0.0, 0.0

        per_indicator_metrics[ind] = {
            "kappa_round1": k_r1,
            "kappa_final": k_fin,
            "kappa_growth": growth,
            "claim_count": len(matching_claims)
        }

    return per_indicator_metrics


def calculate_evaluation_metrics(
    match_results: List[IncidentMatchResult],
    debate_results: List[ClaimDebateResult] = None
) -> SystemEvaluationMetrics:
    """
    Calculate Confusion Matrix (TP, FP, TN, FN), Weighted Metrics, and Cohen's Kappa Inter-Rater Agreement.
    """
    tp = 0
    fp = 0
    tn = 0
    fn = 0

    for res in match_results:
        status = res.match_status.upper()
        if status in ["CONFIRMED_RISK", "TP"]:
            tp += 1
        elif status in ["UNVERIFIED_RISK", "FP"]:
            fp += 1
        elif status in ["NO_RISK_CONFIRMED", "TN"]:
            tn += 1
        elif status in ["MISSED_RISK", "FN"]:
            fn += 1
        elif status in ["HUMAN_REVIEW_REQUIRED"]:
            # Human review cases are unconfirmed: if GT >= 1 it is an unconfirmed violation (FN), else safe (TN)
            if getattr(res, "ground_truth_numeric", 0) >= 1:
                fn += 1
            else:
                tn += 1

    total = tp + fp + tn + fn
    
    if total == 0:
        # No incident matching happened (no claims to match against incidents)
        return SystemEvaluationMetrics(
            true_positives=0, false_positives=0, true_negatives=0, false_negatives=0,
            precision=0.0, recall=0.0, f1_score=0.0, accuracy=0.0,
            cohens_kappa_round1=0.0, cohens_kappa_final=0.0, kappa_growth=0.0,
            indicator_cohens_kappa=compute_per_indicator_kappa(debate_results)
        )

    # 1. Clean Class Metrics
    prec_clean = tn / (tn + fn) if (tn + fn) > 0 else 0.0
    rec_clean = tn / (tn + fp) if (tn + fp) > 0 else 0.0
    f1_clean = (2 * prec_clean * rec_clean) / (prec_clean + rec_clean) if (prec_clean + rec_clean) > 0 else 0.0

    # 2. Risk Class Metrics
    prec_risk = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    rec_risk = tp / (tp + fn) if (tp + fn) > 0 else (1.0 if tp > 0 else 0.0)
    f1_risk = (2 * prec_risk * rec_risk) / (prec_risk + rec_risk) if (prec_risk + rec_risk) > 0 else 0.0

    # 3. Weighted Multi-Class Average (Section 4.3 Methodology)
    risk_weight = (tp + fp) / total
    clean_weight = (tn + fn) / total

    if (tp + fp) == 0 and (tn + fn) == 0:
        # Edge case: no classifications at all
        precision = 0.0
        recall = 0.0
        f1_score = 0.0
    elif (tp + fp) == 0:
        # All classifications are clean (no risks flagged by Agent 3)
        precision = prec_clean
        recall = rec_clean
        f1_score = f1_clean
    else:
        precision = (risk_weight * prec_risk) + (clean_weight * prec_clean)
        recall = (risk_weight * rec_risk) + (clean_weight * rec_clean)
        f1_score = (risk_weight * f1_risk) + (clean_weight * f1_clean)

    # 4. Overall Accuracy
    accuracy = (tp + tn) / total

    # 4. Cohen's Kappa Coefficient Calculation across Debate Rounds
    kappa_r1 = 0.0
    kappa_final = 0.0
    if debate_results:
        r1_a1, r1_a2 = [], []
        fin_a1, fin_a2 = [], []
        for d in debate_results:
            hist = d.debate_history
            if len(hist) >= 2:
                # Round 1: Agent 1 initial vs first Agent 2 critique
                a2_first = next((t for t in hist if "Agent 2" in t.agent_name), hist[1])
                r1_a1.append(hist[0].proposed_risk_level)
                r1_a2.append(a2_first.proposed_risk_level)
                # Final: last Agent 1 vs last Agent 2
                a2_turns = [t for t in hist if "Agent 2" in t.agent_name]
                a2_last = a2_turns[-1].proposed_risk_level if a2_turns else a2_first.proposed_risk_level
                fin_a1.append(hist[-1].proposed_risk_level)
                fin_a2.append(a2_last)
        if r1_a1 and r1_a2:
            kappa_r1 = compute_cohens_kappa(r1_a1, r1_a2)
            kappa_final = compute_cohens_kappa(fin_a1, fin_a2)

    kappa_growth = round(max(0.0, kappa_final - kappa_r1), 4)
    indicator_kappas = compute_per_indicator_kappa(debate_results)

    return SystemEvaluationMetrics(
        true_positives=tp,
        false_positives=fp,
        true_negatives=tn,
        false_negatives=fn,
        precision=round(precision, 4),
        recall=round(recall, 4),
        f1_score=round(f1_score, 4),
        accuracy=round(accuracy, 4),
        cohens_kappa_round1=round(kappa_r1, 4),
        cohens_kappa_final=round(kappa_final, 4),
        kappa_growth=round(kappa_growth, 4),
        indicator_cohens_kappa=indicator_kappas
    )

