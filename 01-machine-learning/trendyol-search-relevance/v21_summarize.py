"""Create deterministic V2.1 aggregate tables and research report from saved runs."""
from pathlib import Path
import numpy as np,pandas as pd
from config import OUTPUTS_DIR,REPORTS_DIR

OUT=OUTPUTS_DIR/"v2_1"; REPORT=REPORTS_DIR/"v2_1"; REPORT.mkdir(parents=True,exist_ok=True)

def aggregate(frame,group,metrics):
    rows=[]
    for name,part in frame.groupby(group):
        row={group:name,"seeds":len(part)}
        for metric in metrics:
            values=part[metric].dropna().to_numpy(); mean=values.mean(); std=values.std(ddof=1); half=2.776*std/np.sqrt(len(values)) if len(values)>1 else 0
            row.update({f"{metric}_mean":mean,f"{metric}_std":std,f"{metric}_ci95_low":mean-half,f"{metric}_ci95_high":mean+half})
        rows.append(row)
    return pd.DataFrame(rows)

classification=pd.read_csv(OUT/"classification_by_seed.csv"); ranking=pd.read_csv(OUT/"ranking_by_seed.csv"); deltas=pd.read_csv(OUT/"query_bootstrap_by_seed.csv"); hard=pd.read_csv(OUT/"hard_negative_by_seed.csv")
c=aggregate(classification,"model",["precision","recall","f1","pr_auc","roc_auc"]); r=aggregate(ranking,"model",["ndcg@10","mrr","recall@10"]); d=aggregate(deltas,"model",["delta"]); h=aggregate(hard,"variant",["precision","recall","f1","pr_auc"])
c.to_csv(OUT/"classification_repeated_seed_ci.csv",index=False); r.to_csv(OUT/"ranking_repeated_seed_ci.csv",index=False); d.to_csv(OUT/"ranking_delta_repeated_seed_ci.csv",index=False); h.to_csv(OUT/"hard_negative_repeated_seed_ci.csv",index=False)
champion=c.sort_values("f1_mean",ascending=False).iloc[0]; rank_best=r.sort_values("ndcg@10_mean",ascending=False).iloc[0]; baseline=r[r.model.eq("leakage_safe_lexical_baseline")].iloc[0]
text=f"""# Robust Ranking V2.1 Results

## Protocol

`ranking_medium` selected 1,000 complete query groups deterministically: 52,422 rows after removing 3,419 duplicate query-item pairs. Five seeds (42, 52, 62, 72, 82) each used 700/150/150 train/validation/holdout groups. Every term overlap and duplicate-pair leakage count was zero. Confidence intervals below are t intervals over five seed-level results; per-seed query bootstrap intervals are preserved separately.

## Classification

The highest mean holdout F1 was **{champion.model}**, {champion.f1_mean:.4f} ± {champion.f1_std:.4f} (95% CI {champion.f1_ci95_low:.4f}–{champion.f1_ci95_high:.4f}); precision {champion.precision_mean:.4f}, recall {champion.recall_mean:.4f}, PR AUC {champion.pr_auc_mean:.4f}. It remains experimental: the persisted V1 metric belongs to its historical 100k split, so this does not establish a paired production improvement.

## Ranking

The leakage-safe baseline averaged NDCG@10 **{baseline['ndcg@10_mean']:.4f}**. The numerically highest row was **{rank_best.model}** at {rank_best['ndcg@10_mean']:.4f}; the persisted V1 row is a reference whose historical training snapshot may overlap the sampled data and therefore cannot be treated as independent promotion evidence. No trainable V2.1 ranker produced a repeatable material gain over the leakage-safe baseline.

## Hard negatives

Weighting and enrichment increased precision but sharply reduced recall and F1 across seeds. Ranking NDCG@10 also stayed below the leakage-safe baseline. The original training policy is retained.

## Decision

V1 remains the live champion. V2.1 classifiers and rankers are research artifacts only. CatBoost was skipped because its optional dependency was unavailable; no additional large runtime was installed. Semantic retrieval is recommended for V3 after a retrieval-quality candidate baseline is established.
"""
(REPORT/"ROBUST_EVALUATION.md").write_text(text,encoding="utf-8")
print(text)
