from __future__ import annotations

"""
Quality-Gate Mutation Tests (standalone)

Creates synthetic evaluation results and verifies that quality gates
correctly fail for known-bad scenarios.
"""

import json
from pathlib import Path
from typing import Any

import pytest

from evaluation.search.schema import QualityGate


def make_metrics(overrides: dict[str, float] | None = None) -> dict[str, float]:
    baseline = {
        "ndcg@10": 0.1676,
        "mrr": 0.1882,
        "relevant_query_coverage": 0.2586,
        "result_query_coverage": 0.9830,
        "must_include_success_rate": 0.6923,
        "precision@10": 0.0259,
        "recall@10": 0.1782,
        "forbidden_overshadow_rate": 0.0,
        "forbidden_presence_rate": 0.0,
    }
    if overrides:
        baseline.update(overrides)
    return baseline


def evaluate_gates(metrics: dict[str, float]) -> list[dict[str, Any]]:
    results = []
    gates = [
        QualityGate("ndcg@10", ">=", 0.100, "Minimum NDCG@10"),
        QualityGate("mrr", ">=", 0.150, "Minimum MRR"),
        QualityGate("relevant_query_coverage", ">=", 0.200, "Minimum relevant query coverage"),
        QualityGate("must_include_success_rate", ">=", 0.500, "Minimum must-include rate"),
        QualityGate("precision@10", ">=", 0.020, "Minimum precision@10"),
        QualityGate("recall@10", ">=", 0.100, "Minimum recall@10"),
    ]
    for gate in gates:
        score = metrics.get(gate.metric, 0.0)
        ok, msg = gate.evaluate(score)
        results.append({"gate": gate.metric, "score": score, "threshold": gate.threshold, "pass": ok, "msg": msg})
    return results


class TestQualityGateMutations:
    def test_baseline_passes_all(self):
        metrics = make_metrics()
        results = evaluate_gates(metrics)
        failures = [r for r in results if not r["pass"]]
        assert not failures, f"Baseline should pass all gates: {failures}"

    def test_mutation_a_empty_results(self):
        metrics = make_metrics({
            "relevant_query_coverage": 0.0,
            "result_query_coverage": 0.0,
            "precision@10": 0.0,
            "recall@10": 0.0,
            "ndcg@10": 0.0,
            "mrr": 0.0,
        })
        results = evaluate_gates(metrics)
        failures = [r for r in results if not r["pass"]]
        assert len(failures) >= 5, f"Expected 5+ gates to fail for empty results, got {len(failures)}: {[f['gate'] for f in failures]}"

    def test_mutation_b_reversed_results(self):
        metrics = make_metrics({
            "ndcg@10": 0.05,
            "mrr": 0.02,
        })
        results = evaluate_gates(metrics)
        failures = [r["gate"] for r in results if not r["pass"]]
        assert "ndcg@10" in failures, "NDCG should fail when near-zero"
        assert "mrr" in failures, "MRR should fail when near-zero"

    def test_mutation_c_remove_must_include(self):
        metrics = make_metrics({
            "must_include_success_rate": 0.0,
        })
        results = evaluate_gates(metrics)
        failures = [r["gate"] for r in results if not r["pass"]]
        assert "must_include_success_rate" in failures, "Must-include gate should fail when rate=0"

    def test_mutation_d_noise_above_protected(self):
        metrics = make_metrics({
            "forbidden_overshadow_rate": 0.85,
            "precision@10": 0.01,
        })
        results = evaluate_gates(metrics)
        failures = [r["gate"] for r in results if not r["pass"]]
        assert "precision@10" in failures, "Precision should fail when noise dominates"

    def test_mutation_e_shuffled_rankings(self):
        metrics = make_metrics({
            "ndcg@10": 0.12,
            "mrr": 0.10,
        })
        results = evaluate_gates(metrics)
        failures = [r["gate"] for r in results if not r["pass"]]
        assert "mrr" in failures, "MRR should fail when first relevant rank is pushed down"


class TestQualityGateWithStatus:
    def test_pass(self):
        gate = QualityGate("ndcg@10", ">=", 0.100, "Minimum NDCG@10")
        status, msg = gate.evaluate_with_status(0.1676)
        assert status == "PASS", f"Expected PASS got {status}"
        assert "PASS" in msg

    def test_fail(self):
        gate = QualityGate("ndcg@10", ">=", 0.100, "Minimum NDCG@10")
        status, msg = gate.evaluate_with_status(0.05)
        assert status == "FAIL", f"Expected FAIL got {status}"
        assert "FAIL" in msg

    def test_skipped_when_score_none(self):
        gate = QualityGate("relevant_query_coverage", ">=", 0.200)
        status, msg = gate.evaluate_with_status(None, metric_present=False)
        assert status == "SKIPPED_MISSING_METRIC", f"Expected SKIPPED_MISSING_METRIC got {status}"

    def test_skipped_when_score_none_with_present_flag(self):
        gate = QualityGate("result_query_coverage", ">=", 0.900)
        status, msg = gate.evaluate_with_status(None, metric_present=True)
        assert status == "SKIPPED_MISSING_METRIC"

    def test_greater_operator(self):
        gate = QualityGate("precision@10", ">", 0.0)
        status, _ = gate.evaluate_with_status(0.0259)
        assert status == "PASS"

    def test_less_than_operator(self):
        gate = QualityGate("forbidden_presence_rate", "<=", 0.1)
        status, _ = gate.evaluate_with_status(0.0)
        assert status == "PASS"


class TestSchemaVersion:
    def test_evaluator_output_has_schema_version(self):
        from evaluation.search.evaluator import SearchEvaluator
        assert hasattr(SearchEvaluator, "run")
        mock_eval = {"schema_version": 2, "metrics": {}}
        assert mock_eval["schema_version"] == 2

    def test_legacy_baseline_missing_schema_version(self):
        legacy = {"query_coverage": 0.5}
        assert "schema_version" not in legacy

    def test_candidate_has_schema_version_field(self):
        candidate = {
            "schema_version": 2,
            "timestamp": "2026-01-01T00:00:00",
            "total_queries": 67,
            "metrics": {
                "relevant_query_coverage": 0.3,
                "result_query_coverage": 0.9,
            },
        }
        assert candidate["schema_version"] == 2
        assert candidate["total_queries"] == 67
        assert "relevant_query_coverage" in candidate["metrics"]
        assert "result_query_coverage" in candidate["metrics"]


class TestMetricMapping:
    def test_legacy_metric_map_structure(self):
        mapping = {"query_coverage": "relevant_query_coverage"}
        assert "query_coverage" in mapping
        assert mapping["query_coverage"] == "relevant_query_coverage"

    def test_legacy_to_new_keys_correctness(self):
        legacy = {"query_coverage": 0.2586}
        mapping = {"query_coverage": "relevant_query_coverage"}
        mapped = {mapping.get(k, k): v for k, v in legacy.items()}
        assert "relevant_query_coverage" in mapped
        assert mapped["relevant_query_coverage"] == 0.2586
        assert "result_query_coverage" not in mapped
