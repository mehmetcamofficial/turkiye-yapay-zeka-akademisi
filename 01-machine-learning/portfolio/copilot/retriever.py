from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional
from pathlib import Path

from portfolio.copilot.schema import CopilotChunk, CopilotCitation
from portfolio.copilot.config import MAX_CITATIONS

ALIAS_MAP = {
    "mrr": "mean reciprocal rank",
    "ndcg": "normalized discounted cumulative gain",
    "ndcg@10": "normalized discounted cumulative gain at 10",
    "precision@10": "precision at 10",
    "recall@20": "recall at 20",
    "quality gate": "quality_gates threshold gate validation rule evaluator",
    "quality gates": "quality_gates threshold gate validation rule evaluator",
    "gate": "quality_gates threshold",
    "threshold": "quality_gates threshold",
    "validation": "test evaluation quality_gates evaluator",
    "test": "test_search_evaluation pytest quality_gates",
    "tests": "test_search_evaluation pytest quality_gates",
    "pytest": "test quality_gates test_search_evaluation",
    "live inference": "live_inference inference prediction",
    "inference": "live_inference inference prediction",
    "prediction": "live_inference inference prediction",
    "runtime": "runtime_diagnostics live_inference",
    "churn": "customer churn churn_model",
    "customer churn": "customer churn churn_model",
    "housing": "housing regression housing_model",
    "housing forecast": "housing regression housing_model",
    "sentiment": "sentiment nlp sentiment_model",
    "nlp": "sentiment nlp sentiment_model",
    "search relevance": "search pipeline relevance",
    "cross encoder": "cross-encoder reranking trendyol_v5 search_index",
    "cross-encoder": "cross-encoder reranking trendyol_v5 search_index",
    "reranking": "cross-encoder reranking search_index",
    "workspace": "search workspace",
    "search workspace": "search workspace",
    "gecitleri": "quality_gates threshold",
    "gecerlik": "quality_gates threshold",
    "gecerli": "quality_gates",
    "varyans": "ranking_diff ranking",
    "i18n": "i18n.py portfolio i18n translation",
    "streamlit": "portfolio_app.py",
    "model registry": "model_registry",
    "pipeline stages": "search_index pipeline stage ordered",
    "cross encoder reranking": "search_index trendyol_v5 cross_encoder",
    "performance summary": "performance_summary.json performance",
    "unsupported": "answer no evidence limitations",
    "datasets formats": "csv dataset data",
    "inventory sayfalari": "inventory data_science_overview",
    "quality gate threshold": "quality_gates.yaml evaluator.py metrics.py",
    "kalite geçit": "quality_gates.yaml evaluator.py",
    "geçit": "quality_gates threshold gate",
}

TURKISH_ALIASES = {
    "neden": "why",
    "nerede": "where",
    "nasıl": "how",
    "ne": "what",
    "hangisi": "which",
    "küme": "set",
    "değer": "value",
    "skoru": "score",
    "performans": "performance",
    "açıklaması": "description",
    "canlı": "live",
    "envanter": "inventory",
    "arama": "search",
    "geçit": "gate",
    "geçitleri": "gates",
    "kaçırılan": "skip skipped",
    "kalan": "remaining",
    "dosya": "file",
    "dosyalar": "files",
    "dosyalardan": "files sources",
    "besleniyor": "feeds sources loads",
    "hangi": "which",
    "implement": "implement implemented",
    "çalışır": "works works how",
    "sıralanır": "ordered sorted stages",
    "eski": "old legacy",
    "yeni": "new",
}

INTENT_WEIGHTS = {
    "find_file": {"path_boost": 4.0, "symbol_boost": 2.0, "heading_boost": 2.0, "lexical_weight": 2.0, "project_boost": 2.0},
    "explain_code": {"path_boost": 1.5, "symbol_boost": 2.0, "heading_boost": 2.0, "lexical_weight": 1.5, "project_boost": 0.5},
    "explain_metric": {"path_boost": 3.0, "symbol_boost": 1.5, "heading_boost": 3.0, "lexical_weight": 3.0, "project_boost": 3.0},
    "compare_projects": {"path_boost": 1.5, "symbol_boost": 1.0, "heading_boost": 1.0, "lexical_weight": 1.0, "project_boost": 2.0},
    "summarize_project": {"path_boost": 1.0, "symbol_boost": 0.5, "heading_boost": 1.5, "lexical_weight": 1.5, "project_boost": 1.0},
    "locate_symbol": {"path_boost": 0.5, "symbol_boost": 4.0, "heading_boost": 1.0, "lexical_weight": 0.5, "project_boost": 0.5},
    "architecture_question": {"path_boost": 3.0, "symbol_boost": 1.0, "heading_boost": 2.0, "lexical_weight": 2.0, "project_boost": 1.0},
    "test_question": {"path_boost": 1.0, "symbol_boost": 1.0, "heading_boost": 2.0, "lexical_weight": 1.5, "project_boost": 1.5},
    "general_repository_question": {"path_boost": 0.5, "symbol_boost": 0.5, "heading_boost": 1.0, "lexical_weight": 1.0, "project_boost": 0.5},
}


def _tokenize(text: str) -> set[str]:
    return set(re.findall(r"[a-zA-Z0-9_]+", text.lower()))


def _split_snake_pascal(text: str) -> set[str]:
    tokens = set()
    for part in text.split("_"):
        tokens.add(part.lower())
    camel = re.findall(r"[A-Z][a-z]+|[A-Z]+(?=[A-Z][a-z])|[a-z]+", text)
    for c in camel:
        tokens.add(c.lower())
    return tokens


def _normalize_query(query: str) -> tuple[str, set[str]]:
    q = query.lower().strip()
    q = q.replace("?", "").replace("!", "").replace(":", " ").replace(",", " ")
    q = re.sub(r"[\s]+", " ", q)
    parts = set(re.findall(r"[a-zA-Z0-9_]+", q))
    expanded: set[str] = set(parts)
    for token in list(parts):
        if token in ALIAS_MAP:
            expanded.update(re.findall(r"[a-zA-Z0-9_]+", ALIAS_MAP[token]))
        if len(token) > 3 and token in TURKISH_ALIASES:
            expanded.update(re.findall(r"[a-zA-Z0-9_]+", TURKISH_ALIASES[token]))
        # Split snake_case / CamelCase tokens
        for sub in _split_snake_pascal(token):
            if sub in ALIAS_MAP:
                expanded.update(re.findall(r"[a-zA-Z0-9_]+", ALIAS_MAP[sub]))
    if not expanded:
        expanded = parts
    return q, expanded


def lexical_score(query_tokens: set[str], chunk_text: str, chunk_title: str | None) -> float:
    title_tokens: set[str] = set()
    if chunk_title:
        title_tokens = _tokenize(chunk_title)
    body_tokens = _tokenize(chunk_text)
    combined = title_tokens | body_tokens
    combined.update(_split_snake_pascal(chunk_text[:200]))
    if not combined:
        return 0.0
    return len(query_tokens & combined) / max(len(query_tokens), 1)


def symbol_score(query: str, query_tokens: set[str], chunk: CopilotChunk) -> float:
    score = 0.0
    symbol = (chunk.symbol_name or "").lower()
    if symbol:
        sym_tokens = set(re.findall(r"[a-zA-Z0-9_]+", symbol))
        sym_tokens.update(_split_snake_pascal(symbol))
        if query_tokens & sym_tokens:
            score += 0.5
    if query in symbol.lower():
        score += 0.3
    heading = (chunk.heading or "").lower()
    heading_tokens = _tokenize(heading)
    heading_tokens.update(_split_snake_pascal(heading))
    if query_tokens & heading_tokens:
        score += 0.2
    return min(score, 1.0)


def path_score(query: str, query_tokens: set[str], chunk: CopilotChunk) -> float:
    score = 0.0
    path = chunk.file_path.lower()
    project = chunk.project_area.lower()
    parts = path.split("/")
    for part in parts:
        if query in part.lower() or (query_tokens & set(_split_snake_pascal(part))):
            score += 0.3
            break
    if query_tokens & set(_split_snake_pascal(project)):
        score += 0.2
    if chunk.file_type == "markdown" and query in path:
        score += 0.15
    if query_tokens & _tokenize(path):
        score += 0.1
    return min(score, 0.7)


def heading_score(query_tokens: set[str], chunk: CopilotChunk) -> float:
    if not chunk.heading:
        return 0.0
    heading_tokens = _tokenize(chunk.heading)
    heading_tokens.update(_split_snake_pascal(chunk.heading))
    if not heading_tokens:
        return 0.0
    return len(query_tokens & heading_tokens) / max(len(query_tokens), 1) * 0.35


def project_area_score(query: str, query_tokens: set[str], chunk: CopilotChunk, query_intent: str) -> float:
    project = chunk.project_area.lower()
    score = 0.0
    intent_map = {
        "find_file": ["search", "ml", "evaluation", "portfolio"],
        "explain_code": ["search", "ml", "portfolio"],
        "compare_projects": ["churn", "housing", "sentiment", "search"],
        "architecture_question": ["search", "ml", "portfolio", "evaluation"],
        "test_question": ["evaluation", "ml"],
        "explain_metric": ["evaluation", "search", "ml"],
        "runtime_metadata_question": ["evaluation", "search", "ml", "portfolio"],
    }
    relevant_areas = intent_map.get(query_intent, [])
    if project in relevant_areas or not relevant_areas:
        score += 0.15
    if query_tokens & set(_split_snake_pascal(project)):
        score += 0.25
    # Penalize copilot package for explain_metric (avoid self-referential matches)
    if query_intent == "explain_metric" and project == "portfolio" and "copilot" in chunk.file_path:
        score -= 0.8
    # Penalize test files for find_file
    if query_intent == "find_file" and "test" in chunk.file_path:
        score -= 0.5
    # Boost evaluation/search for explain_metric
    if query_intent == "explain_metric" and project == "evaluation":
        score += 0.5
    # Boost search for locate_symbol
    if query_intent == "locate_symbol" and project == "search":
        score += 0.5
    return max(min(score, 0.5), -0.5)


def source_priority_score(chunk: CopilotChunk) -> float:
    return chunk.source_priority * 0.15


def file_alias_score(query: str, query_tokens: set[str], chunk: CopilotChunk) -> float:
    """Boost score when query terms match the file name directly."""
    file_name = Path(chunk.file_path).stem.lower()
    score = 0.0
    # Direct query in file name
    if query and query in file_name:
        score += 0.6
    # Query tokens in file name
    file_tokens = set(_split_snake_pascal(file_name))
    if query_tokens & file_tokens:
        score += 0.3 * len(query_tokens & file_tokens) / max(len(query_tokens), 1)
    return min(score, 0.8)


@dataclass
class RetrievalConfig:
    query_intent: str = "general"
    project_filter: str | None = None
    file_type_filter: str | None = None
    max_results: int = 10
    min_score: float = 0.0


def retrieve(query: str, chunks: list[CopilotChunk], config: RetrievalConfig | None = None) -> list[CopilotChunk]:
    if config is None:
        config = RetrievalConfig()
    if not query.strip():
        return []

    query_normalized, query_tokens = _normalize_query(query)
    weights = INTENT_WEIGHTS.get(config.query_intent, INTENT_WEIGHTS["general_repository_question"])

    scored: list[tuple[CopilotChunk, float]] = []
    for chunk in chunks:
        if config.project_filter and chunk.project_area != config.project_filter:
            continue
        if config.file_type_filter and chunk.file_type != config.file_type_filter:
            continue

        combined = (
            lexical_score(query_tokens, chunk.text, chunk.heading) * weights["lexical_weight"]
            + symbol_score(query_normalized, query_tokens, chunk) * weights["symbol_boost"]
            + path_score(query_normalized, query_tokens, chunk) * weights["path_boost"]
            + heading_score(query_tokens, chunk) * weights["heading_boost"]
            + project_area_score(query_normalized, query_tokens, chunk, config.query_intent) * weights["project_boost"]
            + source_priority_score(chunk)
            + file_alias_score(query_normalized, query_tokens, chunk) * 5.0
        )
        if combined > config.min_score:
            scored.append((chunk, combined))

    scored.sort(key=lambda x: x[1], reverse=True)
    return [chunk for chunk, _ in scored[: config.max_results]]


def citations_for(chunks: list[CopilotChunk], max_citations: int = MAX_CITATIONS) -> list[CopilotCitation]:
    citations: list[CopilotCitation] = []
    seen_paths: set[str] = set()
    for chunk in chunks:
        path_key = chunk.file_path
        if path_key in seen_paths and chunk.cell_index is None:
            continue
        seen_paths.add(path_key)
        snippet = chunk.text[:300] if len(chunk.text) > 300 else chunk.text
        citations.append(CopilotCitation(
            file_path=chunk.file_path,
            start_line=chunk.start_line,
            end_line=chunk.end_line,
            cell_index=chunk.cell_index,
            snippet=snippet,
            source_type=chunk.file_type,
            project_area=chunk.project_area,
            retrieval_score=chunk.score,
        ))
    return citations[:max_citations]
