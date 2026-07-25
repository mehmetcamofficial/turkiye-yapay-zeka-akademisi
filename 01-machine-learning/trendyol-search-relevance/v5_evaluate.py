"""V5 cross-encoder evaluation with validation-only selection and holdout reporting.

Protocol:
  - Reuse frozen Hybrid RRF candidate pools from V4 candidate scores
  - Selection seed: 42
  - Validation (150 queries): document variants, alpha grid, batch/pool latency
  - Holdout (150 queries): frozen-policy final metrics only
  - Holdout is never used for alpha, variant, batch, or pool selection
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
sys.path[:0] = [str(ROOT), str(ROOT.parent)]

from retrieval.contracts import fingerprint
from retrieval.metrics import evaluate_query, paired_bootstrap
from v3_evaluate import build_catalogue, select_queries, splits
from search_pipeline.cross_encoder_contracts import build_pairs, DOCUMENT_VARIANTS as VARIANT_SET
from search_pipeline.cross_encoder_service import CrossEncoderService
from search_pipeline.memory_utils import get_rss_mib, get_process_tree_rss

OUT = ROOT / "outputs" / "v5"
MODEL = ROOT / "models" / "v3"
V4_CANDIDATES = ROOT / "outputs" / "v4" / "v4_candidate_scores.csv"
SELECTION_SEED = 42
SEEDS = [42, 52, 62, 72, 82]
METRICS = ["recall@10", "recall@20", "recall@50", "recall@100", "precision@10", "map@10", "ndcg@10", "mrr"]
DOCUMENT_VARIANTS = ["title_only", "title_category", "title_category_brand", "title_compact_metadata"]
ALPHA_GRID = [0.50, 0.65, 0.80, 0.90, 1.00]
BATCH_SIZES = [1, 4, 8, 16]
POOL_SIZES = [20, 50, 100]
MODEL_ID = "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1"
MODEL_REVISION = "1427fd652930e4ba29e8149678df786c240d8825"
LICENSE = "Apache-2.0"


def minmax(values: np.ndarray) -> np.ndarray:
    if len(values) == 0:
        return values
    lo, hi = float(values.min()), float(values.max())
    if hi - lo < 1e-12:
        return np.full_like(values, 0.5, dtype=float)
    return (values - lo) / (hi - lo)


def mean_metrics(rows: list[dict]) -> dict:
    frame = pd.DataFrame(rows)
    return {metric: float(frame[metric].mean()) for metric in METRICS}


def candidate_frame_for(hybrid: pd.DataFrame, term: str, pool: int) -> pd.DataFrame:
    part = hybrid[hybrid.term_id.eq(term)].sort_values(["retrieval_rank", "item_id"], kind="stable")
    return part.head(pool)


def score_query(
    service: CrossEncoderService,
    query: str,
    candidates: pd.DataFrame,
    catalogue: pd.DataFrame,
    document_variant: str,
    pool_size: int,
    batch_size: int,
    timeout_seconds: float = 30.0,
) -> tuple[list[dict], float]:
    cat = catalogue.set_index("item_id")
    rows = []
    for _, row in candidates.iterrows():
        item = str(row.item_id)
        if item not in cat.index:
            continue
        product = cat.loc[item]
        rows.append(
            {
                "item_id": item,
                "title": str(product.get("title", "")),
                "category": str(product.get("category", "")),
                "brand": str(product.get("brand", "")),
                "gender": str(product.get("gender", "")),
                "age_group": str(product.get("age_group", "")),
                "attributes": str(product.get("attributes", "")),
                "source_retrievers": ["lexical", "semantic"],
                "fused_rank": int(row.retrieval_rank),
                "retrieval_score": float(row.retrieval_score),
            }
        )
    started = time.perf_counter()
    scored = service.score_candidates(
        query=query,
        candidates=rows,
        document_variant=document_variant,
        pool_size=pool_size,
        batch_size=batch_size,
        timeout_seconds=timeout_seconds,
    )
    elapsed = time.perf_counter() - started
    return scored, elapsed


def pure_ce_order(scored: list[dict]) -> list[str]:
    ordered = sorted(scored, key=lambda r: (-r["cross_encoder_score"], str(r["item_id"])))
    return [r["item_id"] for r in ordered]


def blend_order(candidates: pd.DataFrame, scored: list[dict], alpha: float) -> list[str]:
    ce_by_item = {r["item_id"]: float(r["cross_encoder_score"]) for r in scored}
    items = candidates.item_id.astype(str).tolist()
    ce = np.array([ce_by_item.get(item, 0.0) for item in items], dtype=float)
    rrf = candidates.retrieval_score.to_numpy(dtype=float)
    blended = alpha * minmax(ce) + (1.0 - alpha) * minmax(rrf)
    order = np.lexsort((np.asarray(items), -blended))
    return [items[i] for i in order]


def main() -> None:
    assert set(DOCUMENT_VARIANTS) == VARIANT_SET
    OUT.mkdir(parents=True, exist_ok=True)

    selected, positive, queries, _ = select_queries("retrieval_medium")
    required = set().union(*positive.values())
    catalogue, audit = build_catalogue(required)
    ids = catalogue.item_id.astype(str).to_numpy()
    persisted = np.load(MODEL / "semantic_medium_item_ids.npy")
    assert np.array_equal(ids, persisted), "Catalogue ID mismatch with frozen V3 semantic index"
    fp = fingerprint(catalogue)
    assert fp

    hybrid_raw = pd.read_csv(V4_CANDIDATES)
    hybrid = hybrid_raw[hybrid_raw.retrieval_mode.eq("hybrid_rrf")].copy()
    hybrid["item_id"] = hybrid["item_id"].astype(str)
    hybrid["term_id"] = hybrid["term_id"].astype(str)
    assert hybrid.term_id.nunique() == 1000, "Expected 1000 Hybrid RRF query groups from V4"

    split_map, split_audit = splits(selected)
    validation_terms = [str(t) for t in split_map[SELECTION_SEED]["validation"]]
    holdout_terms = [str(t) for t in split_map[SELECTION_SEED]["holdout"]]
    assert len(validation_terms) == 150
    assert len(holdout_terms) == 150
    assert set(validation_terms).isdisjoint(set(holdout_terms))

    service = CrossEncoderService(
        model_name=MODEL_ID,
        model_revision=MODEL_REVISION,
        document_variant="title_compact_metadata",
        batch_size=8,
    )
    # Force one lazy load for cold-start measurement
    cold_rss_before = get_rss_mib()
    cold_started = time.perf_counter()
    _ = service.metadata
    cold_load_seconds = time.perf_counter() - cold_started
    cold_rss_after = get_rss_mib()

    # ------------------------------------------------------------------
    # VALIDATION: document variants (pool 20, pure CE)
    # ------------------------------------------------------------------
    variant_rows = []
    variant_latency = {variant: [] for variant in DOCUMENT_VARIANTS}
    for variant in DOCUMENT_VARIANTS:
        rows = []
        for term in validation_terms:
            candidates = candidate_frame_for(hybrid, term, 20)
            scored, elapsed = score_query(
                service, queries[term], candidates, catalogue, variant, 20, 8
            )
            variant_latency[variant].append(elapsed * 1000)
            ranked = pure_ce_order(scored)
            metrics = evaluate_query(positive[term], ranked)
            rows.append({"term_id": term, "document_variant": variant, "split": "validation", **metrics})
        mean = mean_metrics(rows)
        variant_rows.append(
            {
                "split": "validation",
                "document_variant": variant,
                "candidate_pool_size": 20,
                "policy": "cross_encoder",
                **{f"{k}_mean": v for k, v in mean.items()},
                "latency_p50_ms": float(np.percentile(variant_latency[variant], 50)),
                "latency_mean_ms": float(np.mean(variant_latency[variant])),
            }
        )
    variant_summary = pd.DataFrame(variant_rows)
    selected_variant = str(
        variant_summary.sort_values(["ndcg@10_mean", "mrr_mean"], ascending=False).iloc[0]["document_variant"]
    )

    # ------------------------------------------------------------------
    # VALIDATION: batch benchmark (selected variant, pool 20)
    # ------------------------------------------------------------------
    batch_rows = []
    # Warm once
    warm_term = validation_terms[0]
    warm_candidates = candidate_frame_for(hybrid, warm_term, 20)
    score_query(service, queries[warm_term], warm_candidates, catalogue, selected_variant, 20, 8)
    for batch_size in BATCH_SIZES:
        latencies = []
        for term in validation_terms[:30]:  # bounded warm benchmark
            candidates = candidate_frame_for(hybrid, term, 20)
            _, elapsed = score_query(
                service, queries[term], candidates, catalogue, selected_variant, 20, batch_size
            )
            latencies.append(elapsed * 1000)
        batch_rows.append(
            {
                "batch_size": batch_size,
                "n_queries": len(latencies),
                "pool_size": 20,
                "document_variant": selected_variant,
                "latency_mean_ms": float(np.mean(latencies)),
                "latency_p50_ms": float(np.percentile(latencies, 50)),
                "latency_p95_ms": float(np.percentile(latencies, 95)),
            }
        )
    batch_summary = pd.DataFrame(batch_rows)
    # Prefer batch 8 when within 5% of best mean latency; otherwise choose min mean
    best_mean = float(batch_summary.latency_mean_ms.min())
    eligible = batch_summary[batch_summary.latency_mean_ms <= best_mean * 1.05]
    if 8 in set(eligible.batch_size.astype(int)):
        selected_batch = 8
    else:
        selected_batch = int(batch_summary.sort_values("latency_mean_ms").iloc[0]["batch_size"])

    # ------------------------------------------------------------------
    # VALIDATION: pool latency/quality with selected variant
    # ------------------------------------------------------------------
    pool_rows = []
    for pool in POOL_SIZES:
        rows = []
        latencies = []
        for term in validation_terms:
            candidates = candidate_frame_for(hybrid, term, pool)
            scored, elapsed = score_query(
                service, queries[term], candidates, catalogue, selected_variant, pool, selected_batch
            )
            latencies.append(elapsed * 1000)
            ranked = pure_ce_order(scored)
            rows.append(evaluate_query(positive[term], ranked))
        mean = mean_metrics(rows)
        pool_rows.append(
            {
                "split": "validation",
                "candidate_pool_size": pool,
                "document_variant": selected_variant,
                "policy": "cross_encoder",
                **{f"{k}_mean": v for k, v in mean.items()},
                "latency_mean_ms": float(np.mean(latencies)),
                "latency_p50_ms": float(np.percentile(latencies, 50)),
                "latency_p95_ms": float(np.percentile(latencies, 95)),
            }
        )
    pool_summary = pd.DataFrame(pool_rows)
    # Live default: prefer pool 20 if quality is competitive; otherwise best NDCG with latency < 500ms
    live_candidates = pool_summary[pool_summary.latency_p95_ms < 500]
    if live_candidates.empty:
        selected_pool = 20
    else:
        # Prefer 20 when within 2% of best NDCG among latency-eligible pools
        best_ndcg = float(live_candidates["ndcg@10_mean"].max())
        preferred = live_candidates[live_candidates["ndcg@10_mean"] >= best_ndcg * 0.98]
        if 20 in set(preferred.candidate_pool_size.astype(int)):
            selected_pool = 20
        else:
            selected_pool = int(preferred.sort_values("ndcg@10_mean", ascending=False).iloc[0]["candidate_pool_size"])

    # ------------------------------------------------------------------
    # VALIDATION: alpha grid for hybrid blend (selected variant + pool)
    # ------------------------------------------------------------------
    # Cache pure CE scores on validation once
    val_scores: dict[str, list[dict]] = {}
    val_candidates: dict[str, pd.DataFrame] = {}
    for term in validation_terms:
        candidates = candidate_frame_for(hybrid, term, selected_pool)
        scored, _ = score_query(
            service, queries[term], candidates, catalogue, selected_variant, selected_pool, selected_batch
        )
        val_scores[term] = scored
        val_candidates[term] = candidates

    alpha_rows = []
    for alpha in ALPHA_GRID:
        rows = []
        for term in validation_terms:
            if alpha >= 1.0 - 1e-12:
                ranked = pure_ce_order(val_scores[term])
            else:
                ranked = blend_order(val_candidates[term], val_scores[term], alpha)
            rows.append(evaluate_query(positive[term], ranked))
        mean = mean_metrics(rows)
        alpha_rows.append(
            {
                "split": "validation",
                "alpha": alpha,
                "document_variant": selected_variant,
                "candidate_pool_size": selected_pool,
                "policy": "hybrid_cross_encoder_blend" if alpha < 1.0 else "cross_encoder",
                **{f"{k}_mean": v for k, v in mean.items()},
            }
        )
    alpha_summary = pd.DataFrame(alpha_rows)
    selected_alpha = float(
        alpha_summary.sort_values(["ndcg@10_mean", "mrr_mean"], ascending=False).iloc[0]["alpha"]
    )
    selected_policy = "cross_encoder" if selected_alpha >= 1.0 - 1e-12 else "hybrid_cross_encoder_blend"

    # ------------------------------------------------------------------
    # HOLDOUT (seed 42): frozen policy evaluation
    # ------------------------------------------------------------------
    holdout_query_rows = []
    holdout_latencies = []
    holdout_scored: dict[str, list[dict]] = {}
    for term in holdout_terms:
        candidates = candidate_frame_for(hybrid, term, selected_pool)
        baseline_ranked = candidates.item_id.astype(str).tolist()
        scored, elapsed = score_query(
            service, queries[term], candidates, catalogue, selected_variant, selected_pool, selected_batch
        )
        holdout_scored[term] = scored
        holdout_latencies.append(elapsed * 1000)
        pure_ranked = pure_ce_order(scored)
        blended_ranked = blend_order(candidates, scored, selected_alpha)

        for policy, ranked in [
            ("retrieval_only", baseline_ranked),
            ("cross_encoder", pure_ranked),
            ("hybrid_cross_encoder_blend", blended_ranked),
        ]:
            metrics = evaluate_query(positive[term], ranked)
            holdout_query_rows.append(
                {
                    "seed": SELECTION_SEED,
                    "term_id": term,
                    "split": "holdout",
                    "retrieval_mode": "hybrid_rrf",
                    "policy": policy,
                    "document_variant": selected_variant,
                    "candidate_pool_size": selected_pool,
                    "alpha": selected_alpha if policy == "hybrid_cross_encoder_blend" else None,
                    **metrics,
                    "candidate_recall@20": evaluate_query(positive[term], baseline_ranked[:20])["recall@20"],
                }
            )

    holdout_detail = pd.DataFrame(holdout_query_rows)
    holdout_summary_rows = []
    for policy, part in holdout_detail.groupby("policy"):
        holdout_summary_rows.append(
            {
                "split": "holdout",
                "seed": SELECTION_SEED,
                "retrieval_mode": "hybrid_rrf",
                "policy": policy,
                "document_variant": selected_variant,
                "candidate_pool_size": selected_pool,
                "n_queries": int(part.term_id.nunique()),
                **{f"{m}_mean": float(part[m].mean()) for m in METRICS},
                "candidate_recall@20_mean": float(part["candidate_recall@20"].mean()),
            }
        )
    holdout_summary = pd.DataFrame(holdout_summary_rows)

    baseline = holdout_detail[holdout_detail.policy.eq("retrieval_only")]
    blended = holdout_detail[holdout_detail.policy.eq("hybrid_cross_encoder_blend")]
    pure = holdout_detail[holdout_detail.policy.eq("cross_encoder")]
    paired_rows = []
    for name, candidate in [
        ("hybrid_rrf+cross_encoder", pure),
        ("hybrid_rrf+hybrid_cross_encoder_blend", blended),
    ]:
        for metric in ["ndcg@10", "mrr", "recall@20"]:
            stats = paired_bootstrap(candidate, baseline, metric, seed=SELECTION_SEED, n=2000)
            paired_rows.append(
                {
                    "candidate": name,
                    "baseline": "hybrid_rrf+retrieval_only",
                    "metric": metric,
                    "split": "holdout",
                    "seed": SELECTION_SEED,
                    **stats,
                }
            )
    paired = pd.DataFrame(paired_rows)

    # Error samples (bounded, no full candidate text dumps)
    pivot = holdout_detail.pivot_table(index="term_id", columns="policy", values="ndcg@10").reset_index()
    pivot["delta"] = pivot["hybrid_cross_encoder_blend"] - pivot["retrieval_only"]
    samples = pd.concat([pivot.nlargest(8, "delta"), pivot.nsmallest(5, "delta")]).drop_duplicates("term_id")
    error_samples = []
    for row in samples.itertuples():
        base_ids = candidate_frame_for(hybrid, row.term_id, selected_pool).item_id.astype(str).tolist()
        blended_ids = blend_order(
            candidate_frame_for(hybrid, row.term_id, selected_pool),
            holdout_scored[row.term_id],
            selected_alpha,
        )
        error_samples.append(
            {
                "query": queries[row.term_id],
                "term_id": row.term_id,
                "baseline_ndcg": float(row.retrieval_only),
                "v5_ndcg": float(row.hybrid_cross_encoder_blend),
                "delta": float(row.delta),
                "top_item_before": base_ids[0] if base_ids else None,
                "top_item_after": blended_ids[0] if blended_ids else None,
            }
        )

    # Multi-seed holdout summary for selected frozen policy only (selection still seed-42 only)
    score_cache: dict[str, list[dict]] = {}
    score_cache.update(holdout_scored)
    # Validation scores are only reusable when they were built at selected_pool
    if selected_pool == int(pool_summary.loc[pool_summary.candidate_pool_size.eq(selected_pool)].iloc[0]["candidate_pool_size"]):
        score_cache.update(val_scores)

    multi_seed_rows = []
    for seed in SEEDS:
        terms = [str(t) for t in split_map[seed]["holdout"]]
        # Ensure scores exist for this seed's holdout
        for term in terms:
            if term in score_cache:
                continue
            candidates = candidate_frame_for(hybrid, term, selected_pool)
            scored, _ = score_query(
                service,
                queries[term],
                candidates,
                catalogue,
                selected_variant,
                selected_pool,
                selected_batch,
            )
            score_cache[term] = scored
        for policy_name in ["retrieval_only", "cross_encoder", "hybrid_cross_encoder_blend"]:
            rows = []
            for term in terms:
                candidates = candidate_frame_for(hybrid, term, selected_pool)
                baseline_ranked = candidates.item_id.astype(str).tolist()
                scored = score_cache[term]
                if policy_name == "retrieval_only":
                    ranked = baseline_ranked
                elif policy_name == "cross_encoder":
                    ranked = pure_ce_order(scored)
                else:
                    ranked = blend_order(candidates, scored, selected_alpha)
                rows.append(evaluate_query(positive[term], ranked))
            mean = mean_metrics(rows)
            multi_seed_rows.append(
                {
                    "seed": seed,
                    "retrieval_mode": "hybrid_rrf",
                    "policy": policy_name,
                    "document_variant": selected_variant,
                    "candidate_pool_size": selected_pool,
                    "n_queries": len(terms),
                    **mean,
                }
            )
    multi_seed = pd.DataFrame(multi_seed_rows)

    def seed_ci(frame: pd.DataFrame) -> pd.DataFrame:
        rows = []
        for policy, part in frame.groupby("policy"):
            row = {
                "retrieval_mode": "hybrid_rrf",
                "policy": policy,
                "document_variant": selected_variant,
                "candidate_pool_size": selected_pool,
                "seeds": int(part.seed.nunique()),
            }
            for metric in METRICS:
                v = part[metric].to_numpy()
                mean = float(v.mean())
                std = float(v.std(ddof=1)) if len(v) > 1 else 0.0
                half = 2.776 * std / np.sqrt(len(v)) if len(v) > 1 else 0.0
                row.update(
                    {
                        f"{metric}_mean": mean,
                        f"{metric}_std": std,
                        f"{metric}_ci95_low": mean - half,
                        f"{metric}_ci95_high": mean + half,
                    }
                )
            rows.append(row)
        return pd.DataFrame(rows)

    repeated = seed_ci(multi_seed)

    tree = get_process_tree_rss()
    blend_ndcg = float(holdout_summary.loc[holdout_summary.policy.eq("hybrid_cross_encoder_blend"), "ndcg@10_mean"].iloc[0])
    base_ndcg = float(holdout_summary.loc[holdout_summary.policy.eq("retrieval_only"), "ndcg@10_mean"].iloc[0])
    pure_ndcg = float(holdout_summary.loc[holdout_summary.policy.eq("cross_encoder"), "ndcg@10_mean"].iloc[0])
    blend_mrr = float(holdout_summary.loc[holdout_summary.policy.eq("hybrid_cross_encoder_blend"), "mrr_mean"].iloc[0])
    base_mrr = float(holdout_summary.loc[holdout_summary.policy.eq("retrieval_only"), "mrr_mean"].iloc[0])
    pure_mrr = float(holdout_summary.loc[holdout_summary.policy.eq("cross_encoder"), "mrr_mean"].iloc[0])

    blend_pair_ndcg = paired[
        (paired.candidate.eq("hybrid_rrf+hybrid_cross_encoder_blend")) & (paired.metric.eq("ndcg@10"))
    ].iloc[0]
    blend_pair_mrr = paired[
        (paired.candidate.eq("hybrid_rrf+hybrid_cross_encoder_blend")) & (paired.metric.eq("mrr"))
    ].iloc[0]

    absolute_delta = float(blend_pair_ndcg["delta"])
    relative_pct = (absolute_delta / base_ndcg * 100.0) if base_ndcg > 0 else None

    results = {
        "pipeline_version": "5.0",
        "catalogue_rows": int(len(catalogue)),
        "queries_total": int(len(queries)),
        "selection_seed": SELECTION_SEED,
        "validation_query_count": 150,
        "holdout_query_count": 150,
        "validation_holdout_isolation": True,
        "selection_uses_holdout": False,
        "cross_encoder_model": MODEL_ID,
        "cross_encoder_revision": MODEL_REVISION,
        "license": LICENSE,
        "selected_document_variant": selected_variant,
        "selected_candidate_pool": selected_pool,
        "selected_batch_size": selected_batch,
        "selected_alpha": selected_alpha,
        "selected_policy": selected_policy,
        "score_normalization": "per-query min-max",
        "tie_break": "deterministic item_id ascending",
        "score_label": "Cross-encoder score",
        "not_probability": True,
        "holdout_hybrid_rrf_ndcg@10": base_ndcg,
        "holdout_hybrid_rrf_mrr": base_mrr,
        "holdout_pure_cross_encoder_ndcg@10": pure_ndcg,
        "holdout_pure_cross_encoder_mrr": pure_mrr,
        "holdout_blended_ndcg@10": blend_ndcg,
        "holdout_blended_mrr": blend_mrr,
        "holdout_ndcg_absolute_delta": absolute_delta,
        "holdout_ndcg_relative_pct_vs_hybrid": relative_pct,
        "holdout_mrr_delta": float(blend_pair_mrr["delta"]),
        "holdout_ndcg_ci95": [float(blend_pair_ndcg["ci_low"]), float(blend_pair_ndcg["ci_high"])],
        "holdout_mrr_ci95": [float(blend_pair_mrr["ci_low"]), float(blend_pair_mrr["ci_high"])],
        "holdout_improved": int(blend_pair_ndcg["improved"]),
        "holdout_unchanged": int(blend_pair_ndcg["unchanged"]),
        "holdout_worsened": int(blend_pair_ndcg["worsened"]),
        "candidate_recall_note": "Candidate Recall@20 is a retrieval property preserved during reranking of the same pool.",
        "pool20_warm_latency_mean_ms": float(np.mean(holdout_latencies)),
        "pool20_warm_latency_p50_ms": float(np.percentile(holdout_latencies, 50)),
        "pool20_warm_latency_p95_ms": float(np.percentile(holdout_latencies, 95)),
        "cold_tokenizer_model_load_seconds": float(cold_load_seconds),
        "model_load_count": int(service.model_load_count),
        "tokenizer_load_count": int(service.tokenizer_load_count),
        "main_rss_mib": float(tree["main_rss_mib"]),
        "total_rss_mib": float(tree["total_rss_mib"]),
        "cold_rss_before_mib": float(cold_rss_before),
        "cold_rss_after_mib": float(cold_rss_after),
        "v4_aggregate_hybrid_rrf_ndcg@10": 0.619136,
        "metric_scope_note": (
            "On the frozen 150-query V5 holdout (seed 42), Hybrid RRF achieved the holdout baseline. "
            "The previously verified V4 aggregate evaluation reported 0.619136 NDCG@10 on its original multi-seed holdout scope."
        ),
        "governance": "Best Reranking Research Candidate · Not Production Promoted",
        "catalogue_audit": audit,
        "device": service.device,
    }

    # Persist bounded outputs only (no full raw pair dump)
    variant_summary.to_csv(OUT / "v5_validation_document_variants.csv", index=False)
    batch_summary.to_csv(OUT / "v5_batch_benchmark.csv", index=False)
    pool_summary.to_csv(OUT / "v5_pool_benchmark.csv", index=False)
    alpha_summary.to_csv(OUT / "v5_alpha_grid.csv", index=False)
    holdout_detail.to_csv(OUT / "v5_holdout_query_metrics.csv", index=False)
    holdout_summary.to_csv(OUT / "v5_holdout_summary.csv", index=False)
    multi_seed.to_csv(OUT / "v5_metrics_by_seed.csv", index=False)
    repeated.to_csv(OUT / "v5_repeated_seed_ci.csv", index=False)
    paired.to_csv(OUT / "v5_paired_bootstrap.csv", index=False)
    (OUT / "v5_error_samples.json").write_text(json.dumps(error_samples, ensure_ascii=False, indent=2))
    (OUT / "v5_results.json").write_text(json.dumps(results, indent=2))
    (OUT / "v5_frozen_policy.json").write_text(
        json.dumps(
            {
                "model_id": MODEL_ID,
                "revision": MODEL_REVISION,
                "license": LICENSE,
                "document_variant": selected_variant,
                "candidate_pool": selected_pool,
                "batch_size": selected_batch,
                "alpha": selected_alpha,
                "policy": selected_policy,
                "normalization": "per-query min-max",
                "tie_break": "deterministic item_id ascending",
                "selection_seed": SELECTION_SEED,
                "validation_query_count": 150,
                "holdout_query_count": 150,
                "score_label": "Cross-encoder score",
                "governance": "Best Reranking Research Candidate · Not Production Promoted",
            },
            indent=2,
        )
    )
    split_audit.to_csv(OUT / "v5_split_audit.csv", index=False)

    print(json.dumps(results, indent=2))
    print("\nValidation variants:")
    print(variant_summary[["document_variant", "ndcg@10_mean", "mrr_mean"]].to_string(index=False))
    print("\nHoldout summary:")
    print(holdout_summary[["policy", "ndcg@10_mean", "mrr_mean"]].to_string(index=False))
    print("\nSelected:", selected_variant, selected_pool, selected_batch, selected_alpha, selected_policy)


if __name__ == "__main__":
    main()
