import os
import sys
import json
import glob
import numpy as np
from collections import Counter
from typing import List, Dict, Any

REPO_ROOT = r"d:\ESG_GREENWASHING DETECTION"
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# 1. Load output_results files
files = sorted(glob.glob(os.path.join(REPO_ROOT, "output_results", "*_result.json")))
reports_data = []

for f in files:
    with open(f, "r", encoding="utf-8") as fp:
        d = json.load(fp)
        reports_data.append({
            "file": os.path.basename(f),
            "company": d["company_name"],
            "source_file": d["source_file"],
            "claims": d["claims_detected"],
            "matches": d["incident_matches"],
            "metrics": d["metrics"]
        })

print(f"Loaded {len(reports_data)} report result files.")

# --- E. CONFUSION MATRIX PER REPORT ---
print("\n" + "="*110)
print(f"{'Company':<12} | {'Report File':<35} | {'N':<3} | {'TP':<2} | {'FP':<2} | {'TN':<2} | {'FN':<2} | {'Prec':<7} | {'Rec':<7} | {'F1':<7} | {'Acc':<7} | {'100% Status'}")
print("="*110)

per_report_rows = []
all_matches_flat = []

for r in reports_data:
    matches = r["matches"]
    n = len(matches)
    tp = sum(1 for m in matches if m["match_status"] in ["CONFIRMED_RISK", "TP"])
    fp = sum(1 for m in matches if m["match_status"] in ["UNVERIFIED_RISK", "FP"])
    tn = sum(1 for m in matches if m["match_status"] in ["NO_RISK_CONFIRMED", "TN"] or (m["match_status"] == "HUMAN_REVIEW_REQUIRED" and m.get("ground_truth_numeric", 0) == 0))
    fn = sum(1 for m in matches if m["match_status"] in ["MISSED_RISK", "FN"] or (m["match_status"] == "HUMAN_REVIEW_REQUIRED" and m.get("ground_truth_numeric", 0) >= 1))
    
    prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0.0
    acc = (tp + tn) / n if n > 0 else 0.0
    
    is_perfect = (prec == 1.0 and rec == 1.0 and f1 == 1.0 and acc == 1.0)
    
    status_tag = "PERFECT_100%" if is_perfect else "NOT_100%"
    
    row = {
        "company": r["company"],
        "report": r["source_file"],
        "n": n,
        "tp": tp, "fp": fp, "tn": tn, "fn": fn,
        "prec": prec, "rec": rec, "f1": f1, "acc": acc,
        "is_perfect": is_perfect
    }
    per_report_rows.append(row)
    
    print(f"{r['company']:<12} | {r['source_file']:<35} | {n:<3} | {tp:<2} | {fp:<2} | {tn:<2} | {fn:<2} | {prec*100:>5.1f}% | {rec*100:>5.1f}% | {f1*100:>5.1f}% | {acc*100:>5.1f}% | {status_tag}")
    
    for m in matches:
        all_matches_flat.append({
            "company": r["company"],
            "report": r["source_file"],
            "claim_id": m["claim_id"],
            "claim_text": m["claim_text"],
            "ai_risk": m["ai_risk_numeric"],
            "gt": m["ground_truth_numeric"],
            "comp": m["evidence_compatibility"],
            "status": m["match_status"],
            "tp": 1 if (m["match_status"] in ["CONFIRMED_RISK", "TP"]) else 0,
            "fp": 1 if (m["match_status"] in ["UNVERIFIED_RISK", "FP"]) else 0,
            "tn": 1 if (m["match_status"] in ["NO_RISK_CONFIRMED", "TN"] or (m["match_status"] == "HUMAN_REVIEW_REQUIRED" and m.get("ground_truth_numeric", 0) == 0)) else 0,
            "fn": 1 if (m["match_status"] in ["MISSED_RISK", "FN"] or (m["match_status"] == "HUMAN_REVIEW_REQUIRED" and m.get("ground_truth_numeric", 0) >= 1)) else 0
        })

print("="*110)

# --- G. MICRO VS MACRO METRICS ---
tot_n = len(all_matches_flat)
tot_tp = sum(r["tp"] for r in per_report_rows)
tot_fp = sum(r["fp"] for r in per_report_rows)
tot_tn = sum(r["tn"] for r in per_report_rows)
tot_fn = sum(r["fn"] for r in per_report_rows)

micro_p = tot_tp / (tot_tp + tot_fp) if (tot_tp + tot_fp) > 0 else 0.0
micro_r = tot_tp / (tot_tp + tot_fn) if (tot_tp + tot_fn) > 0 else 0.0
micro_f1 = 2 * micro_p * micro_r / (micro_p + micro_r) if (micro_p + micro_r) > 0 else 0.0
overall_acc = (tot_tp + tot_tn) / tot_n if tot_n > 0 else 0.0

macro_p = np.mean([r["prec"] for r in per_report_rows])
macro_r = np.mean([r["rec"] for r in per_report_rows])
macro_f1 = np.mean([r["f1"] for r in per_report_rows])
macro_acc = np.mean([r["acc"] for r in per_report_rows])

print(f"\nPOOLED (MICRO) METRICS:")
print(f"  Total N = {tot_n} | TP={tot_tp}, FP={tot_fp}, TN={tot_tn}, FN={tot_fn}")
print(f"  Micro Precision: {micro_p*100:.2f}%")
print(f"  Micro Recall:    {micro_r*100:.2f}%")
print(f"  Micro F1-Score:  {micro_f1*100:.2f}%")
print(f"  Overall Accuracy: {overall_acc*100:.2f}%")

print(f"\nMACRO (AVERAGE PER-REPORT) METRICS:")
print(f"  Macro Precision: {macro_p*100:.2f}%")
print(f"  Macro Recall:    {macro_r*100:.2f}%")
print(f"  Macro F1-Score:  {macro_f1*100:.2f}%")
print(f"  Macro Accuracy:  {macro_acc*100:.2f}%")

# --- L. BOOTSTRAP 95% CONFIDENCE INTERVALS ---
np.random.seed(42)
B = 2000
boot_f1s = []
boot_accs = []
boot_precs = []
boot_recs = []

indices = np.arange(tot_n)
for _ in range(B):
    boot_idx = np.random.choice(indices, size=tot_n, replace=True)
    b_tp = sum(all_matches_flat[i]["tp"] for i in boot_idx)
    b_fp = sum(all_matches_flat[i]["fp"] for i in boot_idx)
    b_tn = sum(all_matches_flat[i]["tn"] for i in boot_idx)
    b_fn = sum(all_matches_flat[i]["fn"] for i in boot_idx)
    
    b_p = b_tp / (b_tp + b_fp) if (b_tp + b_fp) > 0 else 0.0
    b_r = b_tp / (b_tp + b_fn) if (b_tp + b_fn) > 0 else 0.0
    b_f1 = 2 * b_p * b_r / (b_p + b_r) if (b_p + b_r) > 0 else 0.0
    b_acc = (b_tp + b_tn) / tot_n
    
    boot_precs.append(b_p)
    boot_recs.append(b_r)
    boot_f1s.append(b_f1)
    boot_accs.append(b_acc)

ci_f1 = np.percentile(boot_f1s, [2.5, 97.5])
ci_acc = np.percentile(boot_accs, [2.5, 97.5])
ci_prec = np.percentile(boot_precs, [2.5, 97.5])
ci_rec = np.percentile(boot_recs, [2.5, 97.5])

print(f"\nBOOTSTRAP 95% CONFIDENCE INTERVALS (B = {B}):")
print(f"  Precision: {micro_p*100:.2f}% [95% CI: {ci_prec[0]*100:.2f}% - {ci_prec[1]*100:.2f}%]")
print(f"  Recall:    {micro_r*100:.2f}% [95% CI: {ci_rec[0]*100:.2f}% - {ci_rec[1]*100:.2f}%]")
print(f"  F1-Score:  {micro_f1*100:.2f}% [95% CI: {ci_f1[0]*100:.2f}% - {ci_f1[1]*100:.2f}%]")
print(f"  Accuracy:  {overall_acc*100:.2f}% [95% CI: {ci_acc[0]*100:.2f}% - {ci_acc[1]*100:.2f}%]")

# --- I. DUPLICATE / NON-INDEPENDENCE CHECK ---
print("\n" + "="*80)
print("I. DUPLICATE / NON-INDEPENDENCE AUDIT:")
print("="*80)

claim_texts = [m["claim_text"].strip() for m in all_matches_flat]
text_counts = Counter(claim_texts)
duplicates = {t: c for t, c in text_counts.items() if c > 1}

print(f"Total Unique Claim Texts: {len(text_counts)} / {len(claim_texts)}")
print(f"Duplicate Claims Found: {len(duplicates)}")
for t, c in duplicates.items():
    print(f"  [{c} times]: \"{t[:80]}...\"")

# Check same company across years
comp_counts = Counter(r["company"] for r in reports_data)
print(f"\nCompany Distribution in 15 reports:")
for c, cnt in comp_counts.items():
    print(f"  {c}: {cnt} reports")

# --- J. STRATIFIED BREAKDOWN BY INDICATOR & COMPATIBILITY ---
print("\n" + "="*80)
print("J. STRATIFIED BREAKDOWN AUDIT:")
print("="*80)

# Merge indicator type from claims_detected
claim_ind_map = {}
for r in reports_data:
    for c in r["claims"]:
        cid = c["claim"]["claim_id"]
        claim_ind_map[cid] = c["claim"]["indicator_type"]

ind_stats = {}
comp_stats = {}

for m in all_matches_flat:
    cid = m["claim_id"]
    ind = claim_ind_map.get(cid, "Unknown")
    ec = m["comp"]
    
    # By Indicator
    if ind not in ind_stats:
        ind_stats[ind] = {"tp": 0, "fp": 0, "tn": 0, "fn": 0}
    ind_stats[ind]["tp"] += m["tp"]
    ind_stats[ind]["fp"] += m["fp"]
    ind_stats[ind]["tn"] += m["tn"]
    ind_stats[ind]["fn"] += m["fn"]
    
    # By Compatibility
    if ec not in comp_stats:
        comp_stats[ec] = {"tp": 0, "fp": 0, "tn": 0, "fn": 0}
    comp_stats[ec]["tp"] += m["tp"]
    comp_stats[ec]["fp"] += m["fp"]
    comp_stats[ec]["tn"] += m["tn"]
    comp_stats[ec]["fn"] += m["fn"]

print(f"\n1. By ESG Indicator Type:")
print(f"{'Indicator':<32} | {'N':<3} | {'TP':<2} | {'FP':<2} | {'TN':<2} | {'FN':<2} | {'Prec':<7} | {'Rec':<7} | {'F1':<7} | {'Acc':<7}")
print("-" * 85)
for ind, s in ind_stats.items():
    n_i = s['tp'] + s['fp'] + s['tn'] + s['fn']
    p_i = s['tp'] / (s['tp'] + s['fp']) if (s['tp'] + s['fp']) > 0 else 0.0
    r_i = s['tp'] / (s['tp'] + s['fn']) if (s['tp'] + s['fn']) > 0 else 0.0
    f1_i = 2 * p_i * r_i / (p_i + r_i) if (p_i + r_i) > 0 else 0.0
    acc_i = (s['tp'] + s['tn']) / n_i if n_i > 0 else 0.0
    print(f"{ind:<32} | {n_i:<3} | {s['tp']:<2} | {s['fp']:<2} | {s['tn']:<2} | {s['fn']:<2} | {p_i*100:>5.1f}% | {r_i*100:>5.1f}% | {f1_i*100:>5.1f}% | {acc_i*100:>5.1f}%")

print(f"\n2. By Evidence Compatibility:")
print(f"{'Compatibility':<22} | {'N':<3} | {'TP':<2} | {'FP':<2} | {'TN':<2} | {'FN':<2} | {'Prec':<7} | {'Rec':<7} | {'F1':<7} | {'Acc':<7}")
print("-" * 75)
for ec, s in comp_stats.items():
    n_i = s['tp'] + s['fp'] + s['tn'] + s['fn']
    p_i = s['tp'] / (s['tp'] + s['fp']) if (s['tp'] + s['fp']) > 0 else 0.0
    r_i = s['tp'] / (s['tp'] + s['fn']) if (s['tp'] + s['fn']) > 0 else 0.0
    f1_i = 2 * p_i * r_i / (p_i + r_i) if (p_i + r_i) > 0 else 0.0
    acc_i = (s['tp'] + s['tn']) / n_i if n_i > 0 else 0.0
    print(f"{ec:<22} | {n_i:<3} | {s['tp']:<2} | {s['fp']:<2} | {s['tn']:<2} | {s['fn']:<2} | {p_i*100:>5.1f}% | {r_i*100:>5.1f}% | {f1_i*100:>5.1f}% | {acc_i*100:>5.1f}%")

# --- K. LEAVE-ONE-COMPANY-OUT (LOCO) EVALUATION ---
print("\n" + "="*80)
print("K. LEAVE-ONE-COMPANY-OUT (LOCO) EVALUATION:")
print("="*80)

unique_companies = sorted(list(set(r["company"] for r in reports_data)))
loco_f1s = []
loco_accs = []
loco_precs = []
loco_recs = []

print(f"{'Excluded / Test Company':<25} | {'N':<3} | {'TP':<2} | {'FP':<2} | {'TN':<2} | {'FN':<2} | {'Prec':<7} | {'Rec':<7} | {'F1':<7} | {'Acc':<7}")
print("-" * 85)

for test_comp in unique_companies:
    test_matches = [m for m in all_matches_flat if m["company"] == test_comp]
    n_t = len(test_matches)
    tp_t = sum(m["tp"] for m in test_matches)
    fp_t = sum(m["fp"] for m in test_matches)
    tn_t = sum(m["tn"] for m in test_matches)
    fn_t = sum(m["fn"] for m in test_matches)
    
    p_t = tp_t / (tp_t + fp_t) if (tp_t + fp_t) > 0 else 0.0
    r_t = tp_t / (tp_t + fn_t) if (tp_t + fn_t) > 0 else 0.0
    f1_t = 2 * p_t * r_t / (p_t + r_t) if (p_t + r_t) > 0 else 0.0
    acc_t = (tp_t + tn_t) / n_t if n_t > 0 else 0.0
    
    loco_precs.append(p_t)
    loco_recs.append(r_t)
    loco_f1s.append(f1_t)
    loco_accs.append(acc_t)
    
    print(f"{test_comp:<25} | {n_t:<3} | {tp_t:<2} | {fp_t:<2} | {tn_t:<2} | {fn_t:<2} | {p_t*100:>5.1f}% | {r_t*100:>5.1f}% | {f1_t*100:>5.1f}% | {acc_t*100:>5.1f}%")

print("-" * 85)
print(f"LOCO Summary across {len(unique_companies)} companies:")
print(f"  Mean F1:       {np.mean(loco_f1s)*100:.2f}% (Std: {np.std(loco_f1s)*100:.2f}%)")
print(f"  Mean Accuracy: {np.mean(loco_accs)*100:.2f}% (Std: {np.std(loco_accs)*100:.2f}%)")
print(f"  Mean Prec:     {np.mean(loco_precs)*100:.2f}% (Std: {np.std(loco_precs)*100:.2f}%)")
print(f"  Mean Recall:   {np.mean(loco_recs)*100:.2f}% (Std: {np.std(loco_recs)*100:.2f}%)")

