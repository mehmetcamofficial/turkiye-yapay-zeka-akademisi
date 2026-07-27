from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest
import yaml

from evaluation.search.metrics import (
    average_precision,
    compute_all_metrics,
    mean_reciprocal_rank,
    ndcg_at_k,
    precision_at_k,
    quality_delta,
    ranking_stability_index,
    recall_at_k,
    top_k_jaccard,
    top_1_unchanged_rate,
    must_include_success_rate,
    must_include_resource_coverage,
    forbidden_overshadow_rate,
    forbidden_presence_rate,
    result_query_coverage,
    relevant_query_coverage,
    parse_metrics_report,
)
from evaluation.search.schema import GoldenQuery, QualityGate
from evaluation.search.report import generate_comparison_report, generate_report


class TestPrecisionAtK:
    def test_perfect_precision(self):
        retrieved = ["a", "b", "c", "d"]
        relevant = {"a", "b"}
        assert precision_at_k(retrieved, relevant, 2) == 1.0

    def test_partial_precision(self):
        retrieved = ["a", "b", "c", "d"]
        relevant = {"a", "c"}
        assert precision_at_k(retrieved, relevant, 4) == 0.5

    def test_no_relevant(self):
        retrieved = ["a", "b", "c"]
        relevant = {"d"}
        assert precision_at_k(retrieved, relevant, 3) == 0.0

    def test_k_larger_than_retrieved(self):
        retrieved = ["a", "b"]
        relevant = {"a"}
        assert precision_at_k(retrieved, relevant, 5) == 0.5

    def test_empty_retrieved(self):
        assert precision_at_k([], {"a"}, 10) == 0.0

    def test_k_zero(self):
        retrieved = ["a", "b"]
        relevant = {"a"}
        assert precision_at_k(retrieved, relevant, 0) == 0.0


class TestRecallAtK:
    def test_perfect_recall(self):
        retrieved = ["a", "b", "c"]
        relevant = {"a", "b"}
        assert recall_at_k(retrieved, relevant, 3) == 1.0

    def test_partial_recall(self):
        retrieved = ["a", "b", "c"]
        relevant = {"a", "d"}
        assert recall_at_k(retrieved, relevant, 3) == 0.5

    def test_no_relevant_retrieved(self):
        retrieved = ["a", "b"]
        relevant = {"c", "d"}
        assert recall_at_k(retrieved, relevant, 2) == 0.0

    def test_empty_relevant(self):
        retrieved = ["a", "b"]
        assert recall_at_k(retrieved, {}, 2) == 0.0


class TestAveragePrecision:
    def test_perfect_ranking(self):
        retrieved = ["a", "b", "c", "d"]
        relevant = {"a", "b", "c"}
        ap = average_precision(retrieved, relevant)
        assert abs(ap - 1.0) < 1e-9

    def test_imperfect_ranking(self):
        retrieved = ["a", "b", "c", "d", "e"]
        relevant = {"b", "d"}
        ap = average_precision(retrieved, relevant)
        assert abs(ap - 0.5) < 1e-9

    def test_no_relevant(self):
        retrieved = ["a", "b"]
        assert average_precision(retrieved, {}) == 0.0

    def test_k_truncation(self):
        retrieved = ["x", "a", "b", "c"]
        relevant = {"a", "b"}
        ap = average_precision(retrieved, relevant, k=2)
        assert abs(ap - 0.25) < 1e-9


class TestMeanReciprocalRank:
    def test_perfect_mrr(self):
        queries = [
            (["a", "b"], {"a"}),
            (["c", "d"], {"c"}),
        ]
        mrr = mean_reciprocal_rank(queries)
        assert abs(mrr - 1.0) < 1e-9

    def test_mixed_mrr(self):
        queries = [
            (["a", "b"], {"a"}),
            (["x", "y"], {"y"}),
            (["p", "q"], {"z"}),
        ]
        mrr = mean_reciprocal_rank(queries)
        assert abs(mrr - 0.5) < 1e-9

    def test_empty_queries(self):
        assert mean_reciprocal_rank([]) == 0.0


class TestNDCG:
    def test_perfect_ndcg(self):
        retrieved = ["a", "b", "c"]
        relevance = {"a": 3, "b": 2, "c": 1}
        ndcg = ndcg_at_k(retrieved, relevance, 3)
        assert abs(ndcg - 1.0) < 1e-9

    def test_imperfect_ndcg(self):
        retrieved = ["a", "b", "c", "d"]
        relevance = {"a": 1, "c": 3}
        ndcg = ndcg_at_k(retrieved, relevance, 4)
        assert 0.58 < ndcg < 0.60

    def test_empty_relevance(self):
        retrieved = ["a", "b"]
        assert ndcg_at_k(retrieved, {}, 2) == 0.0


class TestComputeAllMetrics:
    def test_basic_run(self):
        retrieved = {
            "sentiment": ["model:nlp", "experiment:e1", "doc:d1"],
            "churn": ["model:churn", "experiment:e2"],
        }
        relevance = {
            "sentiment": {"model:nlp": 3, "experiment:e1": 2},
            "churn": {"model:churn": 3},
        }
        expected = {
            "sentiment": {"model:nlp", "experiment:e1"},
            "churn": {"model:churn"},
        }
        metrics = compute_all_metrics(
            retrieved_by_query=retrieved,
            relevance_by_query=relevance,
            expected_by_query=expected,
            must_include_by_query={},
            must_not_by_query={},
            protected_targets_by_query={},
            intent_by_query={},
            languages_by_query={},
            top_k=10,
        )
        assert "ndcg@10" in metrics
        assert "mrr" in metrics
        assert "precision@10" in metrics
        assert "recall@10" in metrics
        assert "relevant_query_coverage" in metrics
        assert "result_query_coverage" in metrics
        assert "must_include_success_rate" in metrics


class TestQualityDelta:
    def test_delta_calculation(self):
        baseline = {"ndcg@10": 0.5, "mrr": 0.6}
        candidate = {"ndcg@10": 0.7, "mrr": 0.5}
        delta = quality_delta(baseline, candidate)
        assert abs(delta["ndcg@10"] - 0.2) < 1e-9
        assert abs(delta["mrr"] - (-0.1)) < 1e-9

    def test_new_metric_in_candidate(self):
        baseline = {"ndcg@10": 0.5}
        candidate = {"ndcg@10": 0.6, "mrr": 0.7}
        delta = quality_delta(baseline, candidate)
        assert abs(delta["ndcg@10"] - 0.1) < 1e-9
        assert abs(delta["mrr"] - 0.7) < 1e-9


class TestRankingStabilityIndex:
    def test_identical_rankings(self):
        baseline = {"q1": ["a", "b", "c"]}
        candidate = {"q1": ["a", "b", "c"]}
        rsi = ranking_stability_index(baseline, candidate, k=3)
        assert abs(rsi - 1.0) < 1e-9

    def test_half_overlap(self):
        baseline = {"q1": ["a", "b", "c", "d"]}
        candidate = {"q1": ["a", "b", "e", "f"]}
        rsi = ranking_stability_index(baseline, candidate, k=4)
        assert abs(rsi - 0.75) < 0.001

    def test_no_overlap(self):
        baseline = {"q1": ["a", "b"]}
        candidate = {"q1": ["c", "d"]}
        rsi = ranking_stability_index(baseline, candidate, k=2)
        assert abs(rsi - 0.25) < 0.001


class TestTopKJaccard:
    def test_identical_rankings(self):
        baseline = {"q1": ["a", "b", "c"]}
        candidate = {"q1": ["a", "b", "c"]}
        jac = top_k_jaccard(baseline, candidate, k=3)
        assert abs(jac - 1.0) < 1e-9

    def test_half_overlap(self):
        baseline = {"q1": ["a", "b", "c", "d"]}
        candidate = {"q1": ["a", "b", "e", "f"]}
        jac = top_k_jaccard(baseline, candidate, k=4)
        assert abs(jac - 0.333) < 0.001

    def test_no_overlap(self):
        baseline = {"q1": ["a", "b"]}
        candidate = {"q1": ["c", "d"]}
        jac = top_k_jaccard(baseline, candidate, k=2)
        assert abs(jac - 0.0) < 1e-9


class TestTop1UnchangedRate:
    def test_identical(self):
        assert top_1_unchanged_rate({"q1": ["a"]}, {"q1": ["a"]}) == 1.0

    def test_different(self):
        assert top_1_unchanged_rate({"q1": ["a"]}, {"q1": ["b"]}) == 0.0

    def test_empty(self):
        assert top_1_unchanged_rate({}, {}) == 0.0


class TestMustIncludeSemantics:
    def test_query_level_all_or_nothing_pass(self):
        queries = [("q1", ["a", "b", "c"], ["a", "b"])]
        assert must_include_success_rate(queries) == 1.0

    def test_query_level_all_or_nothing_fail(self):
        queries = [("q1", ["a", "c"], ["a", "b"])]
        assert must_include_success_rate(queries) == 0.0

    def test_resource_coverage_partial(self):
        queries = [("q1", ["a", "c"], ["a", "b"])]
        assert must_include_resource_coverage(queries) == 0.5

    def test_no_must_include(self):
        assert must_include_success_rate([]) == 1.0

    def test_multiple_queries_mixed(self):
        queries = [
            ("q1", ["a", "b"], ["a", "b"]),
            ("q2", ["a"], ["a", "b"]),
        ]
        assert must_include_success_rate(queries) == 0.5
        assert must_include_resource_coverage(queries) == 0.75


class TestForbiddenOvershadow:
    def test_no_forbidden(self):
        queries = [("q1", ["a", "b"], [], ["a"])]
        assert forbidden_overshadow_rate(queries) == 0.0

    def test_forbidden_below_protected(self):
        queries = [("q1", ["a", "b"], ["b"], ["a"])]
        assert forbidden_overshadow_rate(queries) == 0.0

    def test_forbidden_above_protected(self):
        queries = [("q1", ["b", "a"], ["b"], ["a"])]
        assert forbidden_overshadow_rate(queries) == 1.0

    def test_no_protected_target(self):
        queries = [("q1", ["b", "a"], ["b"], [])]
        assert forbidden_overshadow_rate(queries) == 0.0

    def test_both_absent(self):
        queries = [("q1", ["x", "y"], ["b"], ["a"])]
        assert forbidden_overshadow_rate(queries) == 0.0

    def test_forbidden_presence_rate(self):
        queries = [("q1", ["a", "b", "c"], ["b", "x"])]
        assert forbidden_presence_rate(queries) == 0.5


class TestCoverageMetrics:
    def test_result_coverage_all_return(self):
        queries = [("q1", ["a"]), ("q2", ["b"])]
        assert result_query_coverage(queries) == 1.0

    def test_result_coverage_partial(self):
        queries = [("q1", ["a"]), ("q2", [])]
        assert result_query_coverage(queries) == 0.5

    def test_relevant_coverage(self):
        queries = [("q1", ["a", "b"], {"a"}), ("q2", ["c", "d"], {"e"})]
        assert relevant_query_coverage(queries) == 0.5


class TestParseMetricsReport:
    def test_self_comparison(self):
        per_query = {
            "q1": {
                "result_ids": ["a", "b", "c"],
                "metrics": {"ndcg@k": 0.5},
            },
            "q2": {
                "result_ids": ["d", "e"],
                "metrics": {"ndcg@k": 0.3},
            },
        }
        baseline = {"per_query": per_query}
        candidate = {"per_query": per_query}
        report = parse_metrics_report(baseline, candidate)
        assert report["ranking_stability_index"] == 1.0
        assert report["top_1_unchanged_rate"] == 1.0
        assert report["top_3_jaccard"] == 1.0
        assert report["top_10_jaccard"] == 1.0
        assert report["changed_queries"] == 0
        assert report["improved"] == 0
        assert report["regressed"] == 0
        assert report["unchanged"] == 2


class TestGoldenQuery:
    def test_valid_golden_query(self):
        gq = GoldenQuery(
            query="sentiment",
            expected_resource_ids=["model:nlp", "experiment:e1"],
            relevance_grades={"model:nlp": 3, "experiment:e1": 2},
        )
        assert gq.validate() == []

    def test_missing_relevance_grade(self):
        gq = GoldenQuery(
            query="sentiment",
            expected_resource_ids=["model:nlp"],
            relevance_grades={"other": 2},
        )
        errors = gq.validate()
        assert any("missing from relevance_grades" in e for e in errors)

    def test_grade_without_expected(self):
        gq = GoldenQuery(
            query="sentiment",
            expected_resource_ids=["model:nlp"],
            relevance_grades={"model:nlp": 3, "extra:doc": 2},
        )
        errors = gq.validate()
        assert any("not in expected_resource_ids" in e for e in errors)

    def test_out_of_range_grade(self):
        gq = GoldenQuery(
            query="sentiment",
            expected_resource_ids=["model:nlp"],
            relevance_grades={"model:nlp": 5},
        )
        errors = gq.validate()
        assert any("out of range [0, 3]" in e for e in errors)

    def test_empty_query(self):
        gq = GoldenQuery(
            query="",
            expected_resource_ids=[],
            relevance_grades={},
        )
        errors = gq.validate()
        assert any("query is empty" in e for e in errors)

    def test_empty_expected_allowed(self):
        gq = GoldenQuery(
            query="broad search",
            expected_resource_ids=[],
            relevance_grades={},
        )
        assert gq.validate() == []


class TestQualityGate:
    def test_pass_greater_equal(self):
        gate = QualityGate(metric="ndcg@10", operator=">=", threshold=0.5)
        ok, msg = gate.evaluate(0.7)
        assert ok
        assert "PASS" in msg

    def test_fail_greater_equal(self):
        gate = QualityGate(metric="ndcg@10", operator=">=", threshold=0.5)
        ok, msg = gate.evaluate(0.3)
        assert not ok
        assert "FAIL" in msg

    def test_less_than(self):
        gate = QualityGate(metric="forbidden_rate", operator="<=", threshold=0.1)
        ok, msg = gate.evaluate(0.05)
        assert ok
        ok, msg = gate.evaluate(0.5)
        assert not ok


class TestReportGeneration:
    def test_generate_report(self):
        result = {
            "timestamp": "2026-07-27T00:00:00",
            "total_queries": 2,
            "top_k": 10,
            "metrics": {"ndcg@10": 0.5, "mrr": 0.6},
            "per_query": {
                "sentiment": {"result_ids": ["a", "b"], "expected": ["a"], "intent": "lookup"},
            },
        }
        report = generate_report(result)
        assert "Search Evaluation Report" in report
        assert "ndcg@10" in report
        assert "sentiment" in report

    def test_generate_comparison_report(self):
        comparison = {
            "timestamp": "2026-07-27T00:00:00",
            "baseline_metrics": {"ndcg@10": 0.4},
            "candidate_metrics": {"ndcg@10": 0.6},
            "delta": {"ndcg@10": 0.2},
            "ranking_diff": {"total_queries": 5, "improved": 2, "worsened": 1, "unchanged": 2, "avg_overlap": 0.6},
            "metrics_report": {"ranking_stability_index": 0.8, "top_1_unchanged_rate": 0.9, "top_3_jaccard": 0.7, "top_10_jaccard": 0.6, "changed_queries": 2},
        }
        report = generate_comparison_report(comparison)
        assert "Comparison Report" in report
        assert "+0.2000" in report or "+0.2" in report


class TestGoldenQueryYaml:
    def test_golden_yaml_exists(self):
        path = Path(__file__).parent.parent / "evaluation" / "search" / "golden_queries.yaml"
        assert path.exists(), f"Golden queries YAML not found at {path}"
        with open(path) as f:
            data = yaml.safe_load(f)
        assert "queries" in data
        assert len(data["queries"]) >= 30

    def test_quality_gates_yaml_exists(self):
        path = Path(__file__).parent.parent / "evaluation" / "search" / "quality_gates.yaml"
        assert path.exists(), f"Quality gates YAML not found at {path}"
        with open(path) as f:
            data = yaml.safe_load(f)
        assert "gates" in data
        assert len(data["gates"]) >= 3


class TestDatasetLoading:
    def test_load_golden_queries(self):
        path = Path(__file__).parent.parent / "evaluation" / "search" / "golden_queries.yaml"
        if not path.exists():
            pytest.skip("Golden queries file not available")
        from evaluation.search.dataset import load_golden_queries
        queries = load_golden_queries(path)
        assert len(queries) >= 30
        assert all(gq.validate() == [] for gq in queries)


class TestMetricBounds:
    def test_all_metrics_in_valid_range(self):
        retrieved_by_query = {
            "q1": ["a", "b", "c", "d", "e"],
            "q2": ["a", "x", "y", "z"],
            "q3": ["m", "n"],
        }
        relevance_by_query = {
            "q1": {"a": 3, "b": 2, "c": 1},
            "q2": {"a": 3},
            "q3": {},
        }
        expected_by_query = {
            "q1": {"a", "b", "c"},
            "q2": {"a"},
            "q3": set(),
        }
        must_include = {"q1": ["a"]}
        intents = {"q1": "capability_lookup", "q2": "resource_discovery", "q3": "code_search"}
        languages = {"q1": ["en"], "q2": ["tr"], "q3": ["en"]}

        metrics = compute_all_metrics(
            retrieved_by_query=retrieved_by_query,
            relevance_by_query=relevance_by_query,
            expected_by_query=expected_by_query,
            must_include_by_query=must_include,
            must_not_by_query={},
            protected_targets_by_query={},
            intent_by_query=intents,
            languages_by_query=languages,
            top_k=10,
        )

        assert isinstance(metrics, dict)
        for name, value in metrics.items():
            if isinstance(value, float):
                assert 0.0 <= value <= 1.0, (
                    f"Metric '{name}' = {value} is outside valid range [0.0, 1.0]"
                )

    def test_metric_bounds_with_extremes(self):
        retrieved_by_query = {
            "q1": ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j"],
            "q2": ["x"],
        }
        relevance_by_query = {
            "q1": {"a": 3, "b": 3, "c": 3, "d": 3, "e": 3,
                   "f": 3, "g": 3, "h": 3, "i": 3, "j": 3},
            "q2": {},
        }
        expected_by_query = {
            "q1": {"a", "b", "c", "d", "e", "f", "g", "h", "i", "j"},
            "q2": set(),
        }

        metrics = compute_all_metrics(
            retrieved_by_query=retrieved_by_query,
            relevance_by_query=relevance_by_query,
            expected_by_query=expected_by_query,
            must_include_by_query={},
            must_not_by_query={},
            protected_targets_by_query={},
            intent_by_query={},
            languages_by_query={},
            top_k=10,
        )

        assert metrics["precision@10"] == 0.5
        assert metrics["recall@10"] == 0.5
        assert metrics["ndcg@10"] == 0.5
        assert metrics["mrr"] == 0.5
        assert metrics["relevant_query_coverage"] == 0.5
        assert metrics["result_query_coverage"] == 1.0

    def test_metric_bounds_handle_empty_inputs(self):
        metrics = compute_all_metrics(
            retrieved_by_query={},
            relevance_by_query={},
            expected_by_query={},
            must_include_by_query={},
            must_not_by_query={},
            protected_targets_by_query={},
            intent_by_query={},
            languages_by_query={},
            top_k=10,
        )
        assert isinstance(metrics, dict)
        for name, value in metrics.items():
            if isinstance(value, float):
                assert 0.0 <= value <= 1.0, (
                    f"Metric '{name}' = {value} is outside valid range [0.0, 1.0]"
                )
