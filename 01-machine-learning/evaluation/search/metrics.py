from __future__ import annotations

import math
from typing import Any

import numpy as np


def precision_at_k(
    retrieved: list[str],
    relevant: set[str],
    k: int,
) -> float:
    if k <= 0 or not retrieved:
        return 0.0
    prefix = retrieved[:k]
    if not prefix:
        return 0.0
    hits = sum(1 for r in prefix if r in relevant)
    return hits / len(prefix)


def recall_at_k(
    retrieved: list[str],
    relevant: set[str],
    k: int,
) -> float:
    if not relevant:
        return 0.0
    prefix = retrieved[:k]
    if not prefix:
        return 0.0
    hits = sum(1 for r in prefix if r in relevant)
    return hits / len(relevant)


def average_precision(
    retrieved: list[str],
    relevant: set[str],
    k: int | None = None,
) -> float:
    if not relevant:
        return 0.0
    if k is not None:
        retrieved = retrieved[:k]
    if not retrieved:
        return 0.0
    score = 0.0
    hits = 0
    for i, rid in enumerate(retrieved):
        if rid in relevant:
            hits += 1
            score += hits / (i + 1)
    return score / len(relevant)


def mean_reciprocal_rank(
    queries: list[tuple[list[str], set[str]]],
) -> float:
    if not queries:
        return 0.0
    total = 0.0
    for retrieved, relevant in queries:
        if not relevant:
            continue
        for i, rid in enumerate(retrieved):
            if rid in relevant:
                total += 1.0 / (i + 1)
                break
    return total / len(queries)


def _dcg(relevances: list[int], k: int) -> float:
    relevances = relevances[:k]
    if not relevances:
        return 0.0
    gain = np.array([2**rel - 1 for rel in relevances], dtype=float)
    discount = np.log2(np.arange(2, len(gain) + 2))
    return float(np.sum(gain / discount))


def ndcg_at_k(
    retrieved: list[str],
    relevance: dict[str, int],
    k: int,
) -> float:
    relevances = [relevance.get(rid, 0) for rid in retrieved[:k]]
    if not relevances:
        return 0.0
    ideal = sorted(relevance.values(), reverse=True)
    dcg = _dcg(relevances, k)
    idcg = _dcg(ideal, k)
    if idcg <= 0:
        return 0.0
    return dcg / idcg


def result_query_coverage(
    queries: list[tuple[str, list[str]]],
) -> float:
    if not queries:
        return 0.0
    covered = sum(1 for _, retrieved in queries if retrieved)
    return covered / len(queries)


def relevant_query_coverage(
    queries: list[tuple[str, list[str], set[str]]],
) -> float:
    if not queries:
        return 0.0
    covered = 0
    for _query_text, retrieved, relevant in queries:
        hits = sum(1 for r in retrieved if r in relevant)
        if hits > 0:
            covered += 1
    return covered / len(queries)


def must_include_success_rate(
    queries: list[tuple[str, list[str], list[str]]],
) -> float:
    total_queries_with_must = 0
    passing_queries = 0
    for _query_text, retrieved, must_include in queries:
        if not must_include:
            continue
        total_queries_with_must += 1
        if all(mid in retrieved for mid in must_include):
            passing_queries += 1
    if total_queries_with_must == 0:
        return 1.0
    return passing_queries / total_queries_with_must


def must_include_resource_coverage(
    queries: list[tuple[str, list[str], list[str]]],
) -> float:
    total_mandatory = 0
    found = 0
    for _query_text, retrieved, must_include in queries:
        for mid in must_include:
            total_mandatory += 1
            if mid in retrieved:
                found += 1
    if total_mandatory == 0:
        return 1.0
    return found / total_mandatory


def forbidden_overshadow_rate(
    queries: list[tuple[str, list[str], list[str], list[str]]],
) -> float:
    overshadowed = 0
    total_protected = 0
    for _query_text, retrieved, forbidden, protected in queries:
        if not protected:
            continue
        total_protected += len(protected)
        for target in protected:
            if target not in retrieved:
                continue
            target_rank = retrieved.index(target)
            for fid in forbidden:
                if fid in retrieved and retrieved.index(fid) < target_rank:
                    overshadowed += 1
                    break
    if total_protected == 0:
        return 0.0
    return overshadowed / total_protected


def forbidden_presence_rate(
    queries: list[tuple[str, list[str], list[str]]],
) -> float:
    total_forbidden = 0
    present = 0
    for _query_text, retrieved, forbidden in queries:
        for fid in forbidden:
            total_forbidden += 1
            if fid in retrieved:
                present += 1
    if total_forbidden == 0:
        return 0.0
    return present / total_forbidden


def resource_type_coverage(
    results: dict[str, list[str]],
    expected_types: set[str],
) -> float:
    if not expected_types:
        return 1.0
    found = sum(1 for t in expected_types if t in results)
    return found / len(expected_types)


def language_breakdown(
    queries: list[tuple[str, set[str]]],
) -> dict[str, float]:
    if not queries:
        return {}
    counts: dict[str, int] = {}
    for _query_text, languages in queries:
        for lang in languages:
            counts[lang] = counts.get(lang, 0) + 1
    total = sum(counts.values())
    if total == 0:
        return {}
    return {lang: cnt / total for lang, cnt in counts.items()}


def intent_breakdown(
    queries: list[tuple[str, str]],
) -> dict[str, float]:
    if not queries:
        return {}
    counts: dict[str, int] = {}
    for _query_text, intent in queries:
        counts[intent] = counts.get(intent, 0) + 1
    total = sum(counts.values())
    if total == 0:
        return {}
    return {intent: cnt / total for intent, cnt in counts.items()}


def top_k_jaccard(
    baseline_rankings: dict[str, list[str]],
    candidate_rankings: dict[str, list[str]],
    k: int = 10,
) -> float:
    scores = []
    all_queries = set(baseline_rankings) & set(candidate_rankings)
    if not all_queries:
        return 0.0
    for query_text in all_queries:
        base = set(baseline_rankings[query_text][:k])
        cand = set(candidate_rankings[query_text][:k])
        union = base | cand
        if not union:
            scores.append(1.0)
        else:
            scores.append(len(base & cand) / len(union))
    return float(np.mean(scores)) if scores else 0.0


def ranking_stability_index(
    baseline_rankings: dict[str, list[str]],
    candidate_rankings: dict[str, list[str]],
    k: int = 10,
) -> float:
    all_queries = set(baseline_rankings) & set(candidate_rankings)
    if not all_queries:
        return 0.0

    displacements = []

    for query_text in all_queries:
        base = baseline_rankings[query_text][:k]
        cand = candidate_rankings[query_text][:k]
        union_ids = set(base) | set(cand)

        if not union_ids:
            displacements.append(0.0)
            continue

        for rid in union_ids:
            base_rank = base.index(rid) + 1 if rid in base else k + 1
            cand_rank = cand.index(rid) + 1 if rid in cand else k + 1
            displacements.append(abs(base_rank - cand_rank))

    if not displacements:
        return 0.0

    max_displacement = k
    mean_displacement = float(np.mean(displacements))
    normalized = mean_displacement / max_displacement
    stability = 1.0 - normalized
    return float(np.clip(stability, 0.0, 1.0))


def top_1_unchanged_rate(
    baseline_rankings: dict[str, list[str]],
    candidate_rankings: dict[str, list[str]],
) -> float:
    all_queries = set(baseline_rankings) & set(candidate_rankings)
    if not all_queries:
        return 0.0
    unchanged = 0
    for q in all_queries:
        base_top1 = baseline_rankings[q][:1]
        cand_top1 = candidate_rankings[q][:1]
        if base_top1 == cand_top1:
            unchanged += 1
    return unchanged / len(all_queries)


def quality_delta(
    baseline: dict[str, float],
    candidate: dict[str, float],
) -> dict[str, float]:
    all_metrics = set(baseline) | set(candidate)
    deltas = {}
    for metric in all_metrics:
        base = baseline.get(metric, 0.0)
        cand = candidate.get(metric, 0.0)
        deltas[metric] = cand - base
    return deltas


def compute_all_metrics(
    retrieved_by_query: dict[str, list[str]],
    relevance_by_query: dict[str, dict[str, int]],
    expected_by_query: dict[str, set[str]],
    must_include_by_query: dict[str, list[str]],
    must_not_by_query: dict[str, list[str]],
    protected_targets_by_query: dict[str, list[str]],
    intent_by_query: dict[str, str],
    languages_by_query: dict[str, set[str]],
    top_k: int = 10,
) -> dict[str, Any]:
    metrics = {}
    queries_list = list(retrieved_by_query.keys())

    precisions = []
    recalls = []
    maps = []
    ndcgs = []
    rr_pairs = []

    for q in queries_list:
        retrieved = retrieved_by_query[q]
        relevant = expected_by_query.get(q, set())
        rel_grades = relevance_by_query.get(q, {})

        precisions.append(precision_at_k(retrieved, relevant, top_k))
        recalls.append(recall_at_k(retrieved, relevant, top_k))
        maps.append(average_precision(retrieved, relevant, top_k))
        ndcgs.append(ndcg_at_k(retrieved, rel_grades, top_k))
        rr_pairs.append((retrieved, relevant))

    metrics[f"precision@{top_k}"] = float(np.mean(precisions)) if precisions else 0.0
    metrics[f"recall@{top_k}"] = float(np.mean(recalls)) if recalls else 0.0
    metrics[f"map@{top_k}"] = float(np.mean(maps)) if maps else 0.0
    metrics[f"ndcg@{top_k}"] = float(np.mean(ndcgs)) if ndcgs else 0.0
    metrics["mrr"] = mean_reciprocal_rank(rr_pairs)

    result_cov_items = [(q, retrieved_by_query[q]) for q in queries_list]
    metrics["result_query_coverage"] = result_query_coverage(result_cov_items)

    relevant_cov_items = [
        (q, retrieved_by_query[q], expected_by_query.get(q, set()))
        for q in queries_list
    ]
    metrics["relevant_query_coverage"] = relevant_query_coverage(relevant_cov_items)

    mi_items = [
        (q, retrieved_by_query[q], must_include_by_query.get(q, []))
        for q in queries_list
    ]
    metrics["must_include_success_rate"] = must_include_success_rate(mi_items)
    metrics["must_include_resource_coverage"] = must_include_resource_coverage(mi_items)

    fn_items = [
        (q, retrieved_by_query[q], must_not_by_query.get(q, []), protected_targets_by_query.get(q, []))
        for q in queries_list
    ]
    metrics["forbidden_overshadow_rate"] = forbidden_overshadow_rate(fn_items)
    fn_presence_items = [
        (q, retrieved_by_query[q], must_not_by_query.get(q, []))
        for q in queries_list
    ]
    metrics["forbidden_presence_rate"] = forbidden_presence_rate(fn_presence_items)

    return metrics


def parse_metrics_report(
    baseline: dict[str, Any],
    candidate: dict[str, Any],
) -> dict[str, Any]:
    baseline_rankings = {
        q: d.get("result_ids", d.get("retrieved", []))
        for q, d in baseline.get("per_query", {}).items()
    }
    candidate_rankings = {
        q: d.get("result_ids", d.get("retrieved", []))
        for q, d in candidate.get("per_query", {}).items()
    }

    all_queries = set(baseline_rankings) & set(candidate_rankings)

    improved = 0
    regressed = 0
    unchanged = 0
    changed_queries = 0
    largest_movement = 0

    for q in all_queries:
        base_metrics = baseline.get("per_query", {}).get(q, {}).get("metrics", {})
        cand_metrics = candidate.get("per_query", {}).get(q, {}).get("metrics", {})
        base_ndcg = base_metrics.get("ndcg@k", 0.0)
        cand_ndcg = cand_metrics.get("ndcg@k", 0.0)

        if cand_ndcg > base_ndcg + 1e-9:
            improved += 1
        elif cand_ndcg < base_ndcg - 1e-9:
            regressed += 1
        else:
            unchanged += 1

        if abs(cand_ndcg - base_ndcg) > 1e-9:
            changed_queries += 1

        base_ret = baseline_rankings[q]
        cand_ret = candidate_rankings[q]
        for rid in set(base_ret) | set(cand_ret):
            br = base_ret.index(rid) if rid in base_ret else len(base_ret)
            cr = cand_ret.index(rid) if rid in cand_ret else len(cand_ret)
            movement = abs(br - cr)
            if movement > largest_movement:
                largest_movement = movement

    rsi = ranking_stability_index(baseline_rankings, candidate_rankings, k=10)
    top3_jac = top_k_jaccard(baseline_rankings, candidate_rankings, k=3)
    top10_jac = top_k_jaccard(baseline_rankings, candidate_rankings, k=10)
    top1_unc = top_1_unchanged_rate(baseline_rankings, candidate_rankings)

    return {
        "total_queries": len(all_queries),
        "changed_queries": changed_queries,
        "improved": improved,
        "regressed": regressed,
        "unchanged": unchanged,
        "ranking_stability_index": rsi,
        "top_1_unchanged_rate": top1_unc,
        "top_3_jaccard": top3_jac,
        "top_10_jaccard": top10_jac,
        "largest_rank_movement": largest_movement,
        "baseline_top_result": (
            next(iter(baseline_rankings.values()))[0]
            if baseline_rankings and next(iter(baseline_rankings.values()))
            else None
        ),
        "candidate_top_result": (
            next(iter(candidate_rankings.values()))[0]
            if candidate_rankings and next(iter(candidate_rankings.values()))
            else None
        ),
    }
