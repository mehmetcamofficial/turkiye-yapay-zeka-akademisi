from __future__ import annotations

from typing import Any


def _get_result_ids(per_query_entry: dict[str, Any]) -> list[str]:
    return per_query_entry.get("result_ids", per_query_entry.get("retrieved", []))


def compare_rankings(
    baseline_per_query: dict[str, dict[str, Any]],
    candidate_per_query: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    all_queries = set(baseline_per_query) | set(candidate_per_query)
    if not all_queries:
        return {}

    per_query_diff = {}
    improved = 0
    worsened = 0
    unchanged = 0

    for q in sorted(all_queries):
        base = baseline_per_query.get(q, {})
        cand = candidate_per_query.get(q, {})

        base_retrieved = _get_result_ids(base)
        cand_retrieved = _get_result_ids(cand)

        base_set = set(base_retrieved)
        cand_set = set(cand_retrieved)

        new_items = [r for r in cand_retrieved if r not in base_set]
        lost_items = [r for r in base_retrieved if r not in cand_set]
        common = len(base_set & cand_set)

        overlap = common / max(len(base_set | cand_set), 1) if base_set or cand_set else 1.0

        per_query_diff[q] = {
            "overlap": overlap,
            "common": common,
            "new": new_items,
            "lost": lost_items,
            "baseline_count": len(base_set),
            "candidate_count": len(cand_set),
        }

        if new_items and not lost_items:
            improved += 1
        elif lost_items and not new_items:
            worsened += 1
        else:
            unchanged += 1

    avg_overlap = (
        sum(d["overlap"] for d in per_query_diff.values()) / len(per_query_diff)
        if per_query_diff
        else 0.0
    )

    return {
        "total_queries": len(all_queries),
        "improved": improved,
        "worsened": worsened,
        "unchanged": unchanged,
        "avg_overlap": avg_overlap,
        "per_query": per_query_diff,
    }
