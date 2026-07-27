from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from evaluation.search.dataset import (
    load_golden_queries,
    load_quality_gates,
    load_baseline,
    save_baseline,
)
from evaluation.search.metrics import (
    compute_all_metrics,
    quality_delta,
    parse_metrics_report,
    precision_at_k,
    recall_at_k,
    ndcg_at_k,
    average_precision,
    ranking_stability_index,
    top_k_jaccard,
    top_1_unchanged_rate,
)
from evaluation.search.ranking_diff import compare_rankings
from evaluation.search.report import generate_report
from evaluation.search.schema import GoldenQuery


class SearchEvaluator:
    def __init__(self, search_fn, golden_path: str | Path, top_k: int = 10):
        self.search_fn = search_fn
        self.golden_path = Path(golden_path)
        self.top_k = top_k
        self._golden_queries: list[GoldenQuery] | None = None

    @property
    def golden_queries(self) -> list[GoldenQuery]:
        if self._golden_queries is None:
            self._golden_queries = load_golden_queries(self.golden_path)
        return self._golden_queries

    def run(self) -> dict[str, Any]:
        retrieved_by_query: dict[str, list[str]] = {}
        relevance_by_query: dict[str, dict[str, int]] = {}
        expected_by_query: dict[str, set[str]] = {}
        must_include_by_query: dict[str, list[str]] = {}
        must_not_by_query: dict[str, list[str]] = {}
        protected_targets_by_query: dict[str, list[str]] = {}
        intent_by_query: dict[str, str] = {}
        languages_by_query: dict[str, set[str]] = {}
        raw_results: dict[str, list[dict[str, Any]]] = {}
        snapshot_per_query: dict[str, dict[str, Any]] = {}

        for gq in self.golden_queries:
            results = self.search_fn(gq.query, top_k=self.top_k)
            retrieved = [r.document.resource_id for r in results]
            scores = [r.score for r in results]
            resource_types = [r.document.resource_type for r in results]

            expected_set = set(gq.expected_resource_ids)
            first_relevant_rank = -1
            for i, rid in enumerate(retrieved):
                if rid in expected_set:
                    first_relevant_rank = i + 1
                    break

            per_query_metrics = {}
            if expected_set:
                per_query_metrics = {
                    "precision@k": precision_at_k(retrieved, expected_set, self.top_k),
                    "recall@k": recall_at_k(retrieved, expected_set, self.top_k),
                    "ndcg@k": ndcg_at_k(retrieved, gq.relevance_grades, self.top_k),
                    "map@k": average_precision(retrieved, expected_set, self.top_k),
                }

            retrieved_by_query[gq.query] = retrieved
            relevance_by_query[gq.query] = gq.relevance_grades
            expected_by_query[gq.query] = expected_set
            must_include_by_query[gq.query] = gq.must_include
            must_not_by_query[gq.query] = gq.forbidden_resources
            protected_targets_by_query[gq.query] = gq.protected_targets
            intent_by_query[gq.query] = gq.query_intent
            languages_by_query[gq.query] = set(gq.languages)
            raw_results[gq.query] = [
                {
                    "resource_id": r.document.resource_id,
                    "title": r.document.title,
                    "resource_type": r.document.resource_type,
                    "score": r.score,
                    "snippet": r.snippet,
                    "match_reason": r.match_reason,
                }
                for r in results
            ]

            snapshot_per_query[gq.query] = {
                "query_id": gq.query,
                "query_text": gq.query,
                "result_ids": retrieved,
                "scores": scores,
                "resource_types": resource_types,
                "evaluation_depth": self.top_k,
                "first_relevant_rank": first_relevant_rank,
                "metrics": per_query_metrics,
            }

        metrics = compute_all_metrics(
            retrieved_by_query=retrieved_by_query,
            relevance_by_query=relevance_by_query,
            expected_by_query=expected_by_query,
            must_include_by_query=must_include_by_query,
            must_not_by_query=must_not_by_query,
            protected_targets_by_query=protected_targets_by_query,
            intent_by_query=intent_by_query,
            languages_by_query=languages_by_query,
            top_k=self.top_k,
        )

        return {
            "schema_version": 2,
            "timestamp": datetime.now().isoformat(),
            "top_k": self.top_k,
            "total_queries": len(self.golden_queries),
            "metrics": metrics,
            "per_query": {
                gq.query: {
                    "query_id": gq.query,
                    "query_text": gq.query,
                    "result_ids": retrieved_by_query[gq.query],
                    "scores": [r.score for r in self.search_fn(gq.query, top_k=self.top_k)],
                    "resource_types": [r.document.resource_type for r in self.search_fn(gq.query, top_k=self.top_k)],
                    "evaluation_depth": self.top_k,
                    "first_relevant_rank": next(
                        (i + 1 for i, rid in enumerate(retrieved_by_query[gq.query])
                         if rid in set(gq.expected_resource_ids)),
                        -1,
                    ),
                    "metrics": {
                        "precision@k": precision_at_k(retrieved_by_query[gq.query], set(gq.expected_resource_ids), self.top_k),
                        "recall@k": recall_at_k(retrieved_by_query[gq.query], set(gq.expected_resource_ids), self.top_k),
                        "ndcg@k": ndcg_at_k(retrieved_by_query[gq.query], gq.relevance_grades, self.top_k),
                        "map@k": average_precision(retrieved_by_query[gq.query], set(gq.expected_resource_ids), self.top_k),
                    },
                    "expected": list(expected_by_query[gq.query]),
                    "intent": gq.query_intent,
                }
                for gq in self.golden_queries
            },
            "raw_results": raw_results,
        }

    def compare_with_baseline(
        self, baseline_path: str | Path, candidate_result: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        if candidate_result is None:
            candidate_result = self.run()
        baseline = load_baseline(baseline_path)
        if not baseline:
            return {"error": "baseline not found", "candidate": candidate_result}

        delta = quality_delta(
            baseline.get("metrics", {}),
            candidate_result.get("metrics", {}),
        )

        ranking_diff = compare_rankings(
            baseline.get("per_query", {}),
            candidate_result.get("per_query", {}),
        )

        metrics_report = parse_metrics_report(baseline, candidate_result)

        return {
            "timestamp": datetime.now().isoformat(),
            "baseline_metrics": baseline.get("metrics", {}),
            "candidate_metrics": candidate_result.get("metrics", {}),
            "delta": delta,
            "ranking_diff": ranking_diff,
            "metrics_report": metrics_report,
            "candidate": candidate_result,
        }

    def freeze_baseline(self, output_path: str | Path, result: dict[str, Any] | None = None) -> None:
        if result is None:
            result = self.run()
        save_baseline(result, output_path)
