"""Strict request and response contracts for Search Pipeline V4."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
import json
from typing import Any

REQUEST_VERSION = "4.0"
RETRIEVAL_MODES = {"tfidf", "bm25", "semantic", "hybrid_rrf"}
RANKING_POLICIES = {"retrieval_only", "v1_relevance", "experimental_ranker", "blended_policy"}
MAX_QUERY_LENGTH = 300
MAX_PAYLOAD_BYTES = 16_384


@dataclass(frozen=True)
class SearchRequest:
    query: str
    request_version: str = REQUEST_VERSION
    top_k: int = 10
    candidate_pool_size: int = 100
    retrieval_mode: str = "hybrid_rrf"
    final_ranking_policy: str = "retrieval_only"
    category_filter: str = ""
    brand_filter: str = ""
    gender_filter: str = ""
    age_group_filter: str = ""
    include_stage_debug: bool = False
    include_explanations: bool = False
    timeout_budget_ms: int = 2500
    simulated_unavailable: tuple[str, ...] = ()

    def validate(self) -> "SearchRequest":
        if self.request_version != REQUEST_VERSION: raise ValueError("Unsupported request version.")
        if not isinstance(self.query, str) or not self.query.strip(): raise ValueError("Query cannot be empty.")
        if len(self.query) > MAX_QUERY_LENGTH: raise ValueError("Query is too long.")
        if self.retrieval_mode not in RETRIEVAL_MODES: raise ValueError("Unknown retrieval mode.")
        if self.final_ranking_policy not in RANKING_POLICIES: raise ValueError("Unknown ranking policy.")
        if not 1 <= int(self.top_k) <= 50: raise ValueError("top_k must be between 1 and 50.")
        if int(self.candidate_pool_size) not in {20, 50, 100, 200}: raise ValueError("Unsupported candidate pool size.")
        if self.top_k > self.candidate_pool_size: raise ValueError("top_k cannot exceed candidate_pool_size.")
        if not 100 <= int(self.timeout_budget_ms) <= 10_000: raise ValueError("Invalid timeout budget.")
        if set(self.simulated_unavailable) - {"semantic_model", "dense_index", "v1_artifact", "ranker_worker"}: raise ValueError("Unknown simulation state.")
        if len(json.dumps(asdict(self), ensure_ascii=False).encode()) > MAX_PAYLOAD_BYTES: raise ValueError("Request payload is too large.")
        return self

    def normalized_filters(self) -> dict[str, str]:
        return {k: " ".join(str(v).split()).casefold() for k, v in {
            "category": self.category_filter, "brand": self.brand_filter,
            "gender": self.gender_filter, "age_group": self.age_group_filter,
        }.items() if str(v).strip()}


@dataclass
class SearchResponse:
    success: bool
    request_id: str
    request_version: str
    query: str
    normalized_query: str
    selected_retrieval_mode: str
    selected_ranking_policy: str
    result_count: int = 0
    results: list[dict[str, Any]] = field(default_factory=list)
    stage_metrics: dict[str, Any] = field(default_factory=dict)
    pipeline_status: str = "completed"
    warnings: list[str] = field(default_factory=list)
    governance: dict[str, Any] = field(default_factory=dict)
    error: dict[str, str] | None = None

    def to_dict(self) -> dict[str, Any]:
        value=asdict(self)
        json.dumps(value,ensure_ascii=False,sort_keys=True)
        return value
