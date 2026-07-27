"""Single Streamlit boundary for the V5 cross-encoder reranker pipeline."""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Any, Dict

import streamlit as st

from portfolio.config import TRENDYOL_RELEVANCE_DIR

FROZEN_POLICY_PATH = TRENDYOL_RELEVANCE_DIR / "outputs" / "v5" / "v5_frozen_policy.json"
DEFAULT_FROZEN = {
    "model_id": "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1",
    "revision": "1427fd652930e4ba29e8149678df786c240d8825",
    "license": "Apache-2.0",
    "document_variant": "title_compact_metadata",
    "candidate_pool": 20,
    "batch_size": 8,
    "alpha": 1.0,
    "policy": "cross_encoder",
    "normalization": "per-query min-max",
    "tie_break": "deterministic item_id ascending",
    "score_label": "Cross-encoder score",
    "governance": "Best Reranking Research Candidate · Not Production Promoted",
}


def load_frozen_policy() -> dict:
    if FROZEN_POLICY_PATH.is_file():
        try:
            data = json.loads(FROZEN_POLICY_PATH.read_text(encoding="utf-8"))
            return {**DEFAULT_FROZEN, **data}
        except (OSError, json.JSONDecodeError):
            return dict(DEFAULT_FROZEN)
    return dict(DEFAULT_FROZEN)


@st.cache_resource(show_spinner=False)
def v5_runtime():
    """Lazy-initialized V5 pipeline runtime with cross-encoder service."""
    root = str(TRENDYOL_RELEVANCE_DIR)
    if root not in sys.path:
        sys.path.insert(0, root)
    from search_pipeline.orchestrator import SearchPipeline
    from search_pipeline.cross_encoder_service import CrossEncoderService

    frozen = load_frozen_policy()
    pipeline = SearchPipeline()
    
    # Try to load cross-encoder with proper error handling for cloud
    cross_encoder = None
    ce_error = None
    try:
        cross_encoder = CrossEncoderService(
            model_name=frozen["model_id"],
            model_revision=frozen["revision"],
            document_variant=frozen["document_variant"],
            batch_size=int(frozen["batch_size"]),
        )
    except Exception as e:
        ce_error = str(e)
    
    return pipeline, cross_encoder, frozen, ce_error


def v5_search(**values) -> Dict[str, Any]:
    """Execute a V5 search request with optional cross-encoder reranking."""
    root = str(TRENDYOL_RELEVANCE_DIR)
    if root not in sys.path:
        sys.path.insert(0, root)
    from search_pipeline.contracts import SearchRequest

    pipeline, cross_encoder, frozen, ce_error = v5_runtime()
    # Apply frozen defaults unless the caller overrides
    values = {
        "retrieval_mode": "hybrid_rrf",
        "final_ranking_policy": frozen.get("policy", "hybrid_cross_encoder_blend"),
        "candidate_pool_size": int(frozen.get("candidate_pool", 20)),
        "top_k": 10,
        **values,
    }
    request = SearchRequest(**{k: v for k, v in values.items() if k in SearchRequest.__dataclass_fields__})
    response = pipeline.search(request)

    policy = values.get("final_ranking_policy", frozen.get("policy", "retrieval_only"))
    document_variant = values.get("document_variant", frozen.get("document_variant", "title_compact_metadata"))
    batch_size = int(values.get("batch_size", frozen.get("batch_size", 8)))
    alpha = float(values.get("blend_alpha", frozen.get("alpha", 0.80)))
    timeout_ms = int(values.get("timeout_budget_ms", 2500))

    # Check if cross-encoder is available
    if ce_error:
        response["warnings"] = list(response.get("warnings") or []) + [
            f"Cross-encoder unavailable: {ce_error}. Hybrid RRF retrieval-only order preserved."
        ]
        response["selected_ranking_policy"] = "retrieval_only"
        response["pipeline_status"] = "degraded"
        response["cross_encoder_metadata"] = {
            "model_name": frozen["model_id"],
            "model_revision": frozen["revision"],
            "document_variant": document_variant,
            "batch_size": batch_size,
            "alpha": alpha if policy == "hybrid_cross_encoder_blend" else None,
            "score_label": "Cross-encoder score",
            "model_load_count": 0,
            "tokenizer_load_count": 0,
            "governance": frozen.get("governance"),
            "error": ce_error,
        }
        return response

    if policy in ("cross_encoder", "hybrid_cross_encoder_blend") and response.get("success"):
        results = response.get("results", [])
        if results:
            candidates = [
                {
                    "item_id": r.get("item_id", ""),
                    "title": r.get("title", ""),
                    "category": r.get("category", ""),
                    "brand": r.get("brand", ""),
                    "gender": r.get("gender", ""),
                    "age_group": r.get("age_group", ""),
                    "attributes": r.get("attributes", ""),
                    "source_retrievers": r.get("retrieval_sources", []),
                    "fused_rank": r.get("fused_rank"),
                    "retrieval_score": r.get("retrieval_score"),
                    "relevance_label": r.get("relevance_label"),
                }
                for r in results
            ]
            try:
                started = time.perf_counter()
                ce_results = cross_encoder.score_candidates(
                    query=request.query,
                    candidates=candidates,
                    document_variant=document_variant,
                    pool_size=len(candidates),
                    batch_size=batch_size,
                    timeout_seconds=timeout_ms / 1000.0,
                )
                ce_ms = (time.perf_counter() - started) * 1000.0
                ce_by_item = {r["item_id"]: r for r in ce_results}

                if policy == "cross_encoder":
                    results.sort(
                        key=lambda r: (
                            -ce_by_item.get(r["item_id"], {}).get("cross_encoder_score", float("-inf")),
                            str(r["item_id"]),
                        )
                    )
                else:
                    ce_scores = [
                        ce_by_item.get(r["item_id"], {}).get("cross_encoder_score", 0.0) for r in results
                    ]
                    rrf_scores = [r.get("retrieval_score", 0.0) or 0.0 for r in results]

                    def _minmax(values_list):
                        if not values_list:
                            return values_list
                        lo, hi = min(values_list), max(values_list)
                        if hi - lo < 1e-12:
                            return [0.5] * len(values_list)
                        return [(v - lo) / (hi - lo) for v in values_list]

                    ce_norm = _minmax(ce_scores)
                    rrf_norm = _minmax(rrf_scores)
                    for i, r in enumerate(results):
                        r["normalized_cross_encoder_score"] = ce_norm[i]
                        r["normalized_rrf_score"] = rrf_norm[i]
                        r["blended_score"] = alpha * ce_norm[i] + (1 - alpha) * rrf_norm[i]
                    results.sort(key=lambda r: (-r.get("blended_score", 0.0), str(r["item_id"])))

                for final_rank, r in enumerate(results, 1):
                    ce_info = ce_by_item.get(r["item_id"], {})
                    r["cross_encoder_score"] = ce_info.get("cross_encoder_score")
                    r["cross_encoder_rank"] = ce_info.get("cross_encoder_rank")
                    r["pre_rerank_rank"] = r.get("fused_rank")
                    pre = r.get("fused_rank") or final_rank
                    r["rank_delta"] = pre - final_rank
                    r["final_rank"] = final_rank
                    r["model_name"] = ce_info.get("model_name")
                    r["model_revision"] = ce_info.get("model_revision")
                    r["document_variant"] = ce_info.get("document_variant")
                    r["scoring_status"] = ce_info.get("scoring_status")
                    r["score_label"] = "Cross-encoder score"
                    flags = list(r.get("experimental_flags") or [])
                    if "cross_encoder_reranked" not in flags:
                        flags.append("cross_encoder_reranked")
                    r["experimental_flags"] = flags

                response["results"] = results
                response["selected_ranking_policy"] = policy
                stage = dict(response.get("stage_metrics") or {})
                stage["cross_encoder_ms"] = ce_ms
                response["stage_metrics"] = stage
                response["cross_encoder_metadata"] = {
                    "model_name": frozen["model_id"],
                    "model_revision": frozen["revision"],
                    "document_variant": document_variant,
                    "batch_size": batch_size,
                    "alpha": alpha if policy == "hybrid_cross_encoder_blend" else None,
                    "score_label": "Cross-encoder score",
                    "model_load_count": cross_encoder.model_load_count,
                    "tokenizer_load_count": cross_encoder.tokenizer_load_count,
                    "governance": frozen.get("governance"),
                }
            except (RuntimeError, TimeoutError) as exc:
                response["warnings"] = list(response.get("warnings") or []) + [
                    f"Cross-encoder unavailable: {exc}. Hybrid RRF retrieval-only order preserved."
                ]
                response["selected_ranking_policy"] = "retrieval_only"
                response["pipeline_status"] = "degraded"

    return response


def v5_load_counters() -> dict:
    """Return model/tokenizer load counters without forcing a new load when unloaded."""
    try:
        _, cross_encoder, frozen, ce_error = v5_runtime()
        if ce_error:
            return {
                "model_load_count": 0,
                "tokenizer_load_count": 0,
                "model_loaded": False,
                "frozen_policy": frozen.get("policy"),
                "model_id": frozen.get("model_id"),
                "revision": frozen.get("revision"),
                "error": ce_error,
            }
        return {
            "model_load_count": int(cross_encoder.model_load_count),
            "tokenizer_load_count": int(cross_encoder.tokenizer_load_count),
            "model_loaded": cross_encoder._model is not None,
            "frozen_policy": frozen.get("policy"),
            "model_id": frozen.get("model_id"),
            "revision": frozen.get("revision"),
        }
    except Exception as e:
        return {
            "model_load_count": 0,
            "tokenizer_load_count": 0,
            "model_loaded": False,
            "frozen_policy": None,
            "model_id": DEFAULT_FROZEN["model_id"],
            "revision": DEFAULT_FROZEN["revision"],
            "error": str(e),
        }
