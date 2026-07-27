from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any


@dataclass
class GoldenQuery:
    query: str
    expected_resource_ids: list[str]
    relevance_grades: dict[str, int]
    query_intent: str = ""
    evaluation_category: str = ""
    must_include: list[str] = field(default_factory=list)
    forbidden_resources: list[str] = field(default_factory=list)
    protected_targets: list[str] = field(default_factory=list)
    categories: list[str] = field(default_factory=list)
    languages: list[str] = field(default_factory=list)
    notes: str = ""

    def validate(self) -> list[str]:
        errors = []
        if not self.query.strip():
            errors.append("query is empty")
        for rid in self.expected_resource_ids:
            if rid not in self.relevance_grades:
                errors.append(f"resource_id '{rid}' missing from relevance_grades")
            grade = self.relevance_grades.get(rid, 0)
            if grade < 0 or grade > 3:
                errors.append(f"grade {grade} for '{rid}' out of range [0, 3]")
        for rid, grade in self.relevance_grades.items():
            if rid not in self.expected_resource_ids and grade > 0:
                errors.append(f"resource_id '{rid}' has grade {grade} but not in expected_resource_ids")
        return errors


@dataclass
class EvaluationResult:
    query: str
    metric_name: str
    score: float
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class QualityGate:
    metric: str
    operator: str
    threshold: float
    description: str = ""

    def evaluate(self, score: float, metric_present: bool = True) -> tuple[bool, str]:
        if not metric_present:
            return False, f"{self.metric}: metric missing → SKIPPED_MISSING_METRIC"
        if self.operator == ">=":
            ok = score >= self.threshold
        elif self.operator == ">":
            ok = score > self.threshold
        elif self.operator == "<=":
            ok = score <= self.threshold
        elif self.operator == "<":
            ok = score < self.threshold
        elif self.operator == "==":
            ok = abs(score - self.threshold) < 1e-9
        else:
            return False, f"unknown operator: {self.operator}"
        status = "PASS" if ok else "FAIL"
        return ok, f"{self.metric} {self.operator} {self.threshold}: {score:.4f} -> {status}"

    def evaluate_with_status(
        self, score: float | None, metric_present: bool = True
    ) -> tuple[str, str]:
        if not metric_present or score is None:
            return "SKIPPED_MISSING_METRIC", "Metric not available in artifact"
        ok, msg = self.evaluate(score, metric_present=True)
        status = "PASS" if ok else "FAIL"
        return status, msg
