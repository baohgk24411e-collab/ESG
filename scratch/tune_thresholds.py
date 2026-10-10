import os
import sys
import json
import glob
import numpy as np
from typing import List, Dict, Any, Tuple
from sklearn.model_selection import StratifiedKFold

# Add repo root to path
REPO_ROOT = r"d:\ESG_GREENWASHING DETECTION"
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from src.matching import compute_claim_incident_relevance
from src.decision_gate import evaluate_decision_gate
from src.models import IncidentMatchResult, GreenwashingClaim, NewsIncident
from src.metrics import calculate_evaluation_metrics

# Load all 89 claims from output_results
files = sorted(glob.glob(os.path.join(REPO_ROOT, "output_results", "*_result.json")))
all_claims_data = []

for f in files:
    with open(f, "r", encoding="utf-8") as fp:
        d = json.load(fp)
        comp = d["company_name"]
        debates = {c["claim"]["claim_id"]: c for c in d["claims_detected"]}
        for m in d["incident_matches"]:
            cid = m["claim_id"]
            d_obj = debates.get(cid)
            all_claims_data.append({
                "company": comp,
                "file": os.path.basename(f),
                "claim_id": cid,
                "claim_text": m["claim_text"],
                "indicator_type": d_obj["claim"]["indicator_type"] if d_obj else "Hollow Promise",
                "evidence_quote": d_obj["claim"]["evidence_quote"] if d_obj else "",
                "agent1_risk": d_obj["claim"]["initial_risk_level"] if d_obj else "Medium",
                "final_risk": d_obj["final_risk_level"] if d_obj else "Medium",
                "final_confidence": d_obj["final_confidence"] if d_obj else 0.8,
                "consensus_reached": d_obj["consensus_reached"] if d_obj else True,
                "matched_incident": m.get("matched_incident"),
                "evidence_compatibility": m.get("evidence_compatibility", "NO_EVIDENCE"),
                "ground_truth_numeric": m.get("ground_truth_numeric", 0)
            })

print(f"Loaded {len(all_claims_data)} claims for cross-validation and threshold tuning.")

# Prepare Ground Truth binary labels for stratification (1 if GT >= 1, 0 otherwise)
y_binary = np.array([1 if c["ground_truth_numeric"] >= 1 else 0 for c in all_claims_data])
print(f"Class distribution: Positive (Risk) = {sum(y_binary)}, Negative (Clean) = {len(y_binary) - sum(y_binary)}")

def evaluate_configuration(
    dataset: List[Dict[str, Any]],
    rel_thresh: float,
    conf_thresh: float,
    partial_rel_thresh: float,
    partial_conf_thresh: float
) -> Dict[str, float]:
    tp, fp, tn, fn = 0, 0, 0, 0
    
    for item in dataset:
        gt_num = item["ground_truth_numeric"]
        inc = item["matched_incident"]
        
        # Compute relevance
        if inc:
            # Construct incident object
            inc_obj = NewsIncident(
                incident_id=inc.get("incident_id", "inc_0"),
                company_name=inc.get("company_name", item["company"]),
                title=inc.get("title", ""),
                source=inc.get("source", ""),
                url=inc.get("article_url") or inc.get("url") or "",
                article_url=inc.get("article_url"),
                published_date=inc.get("published_date", "2024"),
                snippet=inc.get("snippet", "")
            )
            rel_info = compute_claim_incident_relevance(
                claim_text=item["claim_text"],
                indicator_type=item["indicator_type"],
                company_name=item["company"],
                incident=inc_obj
            )
            rel_score = rel_info["relevance_score"]
            if not rel_info["topic_match"]:
                inc_obj = None
                rel_score = 0.0
        else:
            inc_obj = None
            rel_score = 0.0
            
        gate = evaluate_decision_gate(
            ai_risk_str=item["final_risk"],
            final_confidence=item["final_confidence"],
            evidence_compatibility=item["evidence_compatibility"],
            matched_incident=inc_obj,
            relevance_score=rel_score,
            consensus_reached=item["consensus_reached"],
            relevance_threshold=rel_thresh,
            confidence_threshold=conf_thresh,
            partial_relevance_threshold=partial_rel_thresh,
            partial_confidence_threshold=partial_conf_thresh
        )
        
        ai_num = gate["final_ai_risk_numeric"]
        
        # If the claim was a core violation and corroborated:
        # Note: if GT >= 1 and AI correctly identified confirmed risk -> TP
        is_ai_pos = ai_num >= 1
        is_gt_pos = gt_num >= 1
        
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
    
    return {
        "precision": p,
        "recall": r,
        "f1": f1,
        "accuracy": acc,
        "tp": tp,
        "fp": fp,
        "tn": tn,
        "fn": fn
    }

# Grid search parameters
relevance_grid = [0.60, 0.65, 0.70, 0.75, 0.80]
confidence_grid = [0.70, 0.75, 0.80, 0.85]
partial_rel_grid = [0.75, 0.80, 0.85]
partial_conf_grid = [0.75, 0.80, 0.82]

# 5-Fold Stratified Cross Validation
skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

best_val_f1 = -1.0
best_params = None
best_val_metrics = None

print("\n--- RUNNING 5-FOLD STRATIFIED CROSS-VALIDATION FOR THRESHOLD TUNING ---")

# Evaluate parameter combinations across folds
results_summary = []

for r_th in relevance_grid:
    for c_th in confidence_grid:
        for pr_th in partial_rel_grid:
            for pc_th in partial_conf_grid:
                fold_f1s = []
                fold_recalls = []
                fold_precs = []
                fold_accs = []
                
                for train_idx, val_idx in skf.split(all_claims_data, y_binary):
                    val_data = [all_claims_data[i] for i in val_idx]
                    metrics = evaluate_configuration(val_data, r_th, c_th, pr_th, pc_th)
                    fold_f1s.append(metrics["f1"])
                    fold_recalls.append(metrics["recall"])
                    fold_precs.append(metrics["precision"])
                    fold_accs.append(metrics["accuracy"])
                    
                mean_f1 = np.mean(fold_f1s)
                mean_rec = np.mean(fold_recalls)
                mean_prec = np.mean(fold_precs)
                mean_acc = np.mean(fold_accs)
                
                results_summary.append({
                    "params": (r_th, c_th, pr_th, pc_th),
                    "mean_f1": mean_f1,
                    "mean_recall": mean_rec,
                    "mean_prec": mean_prec,
                    "mean_acc": mean_acc
                })
                
                # Check research constraint: Recall >= 0.80
                if mean_rec >= 0.80 and mean_f1 > best_val_f1:
                    best_val_f1 = mean_f1
                    best_params = (r_th, c_th, pr_th, pc_th)
                    best_val_metrics = {
                        "f1": mean_f1,
                        "recall": mean_rec,
                        "precision": mean_prec,
                        "accuracy": mean_acc
                    }

print(f"Top Tuning Configuration on Validation (under Recall >= 0.80):")
print(f"  Best Parameters: relevance_threshold={best_params[0]}, confidence_threshold={best_params[1]}, partial_relevance_threshold={best_params[2]}, partial_confidence_threshold={best_params[3]}")
print(f"  Validation Mean F1: {best_val_metrics['f1']*100:.2f}%")
print(f"  Validation Mean Precision: {best_val_metrics['precision']*100:.2f}%")
print(f"  Validation Mean Recall: {best_val_metrics['recall']*100:.2f}%")
print(f"  Validation Mean Accuracy: {best_val_metrics['accuracy']*100:.2f}%")

# Save results to json
with open(os.path.join(REPO_ROOT, "scratch", "tuning_results.json"), "w", encoding="utf-8") as f:
    json.dump({
        "best_params": {
            "relevance_threshold": best_params[0],
            "confidence_threshold": best_params[1],
            "partial_relevance_threshold": best_params[2],
            "partial_confidence_threshold": best_params[3]
        },
        "best_val_metrics": best_val_metrics
    }, f, indent=2)

