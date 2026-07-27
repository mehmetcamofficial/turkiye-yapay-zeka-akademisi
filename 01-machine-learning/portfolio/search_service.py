"""High-level search service with ranking, fuzzy fill-in, and recent queries."""

from __future__ import annotations

from dataclasses import dataclass
from difflib import SequenceMatcher
from html import escape
from typing import Any

from portfolio.search_index import (
    SearchDocument,
    SearchIndex,
    SearchResult,
    get_search_index,
    reset_search_index,
)


@dataclass
class SearchSuggestion:
    """Search suggestion with metadata."""

    query: str
    category: str | None = None
    count: int = 0


@dataclass
class FuzzyOutcome:
    """Details about a fuzzy correction attempt."""

    original_query: str
    corrected_query: str | None
    fuzzy_score: float
    top_result: SearchResult | None
    relevant: bool


# Safe, supported suggested queries only — no unsupported structured examples
# beyond the metric filter that is actually implemented (f1 > 0.8).
DEFAULT_SUGGESTIONS: list[str] = [
    "sentiment",
    "duygu analizi",
    "churn",
    "müşteri kaybı",
    "housing",
    "konut tahmini",
    "random forest",
    "best score",
    "grid search",
    "notebook",
    "architecture",
]


class SearchService:
    """Search façade over the product-resource BM25 index."""

    def __init__(self, index: SearchIndex | None = None) -> None:
        self.index = index or get_search_index()
        self._recent_searches: list[str] = []
        self._max_recent = 10

    def search(
        self,
        query: str,
        top_k: int = 10,
        category: str | None = None,
        resource_type: str | None = None,
        fuzzy: bool = True,
    ) -> list[SearchResult]:
        """Search with BM25 primary ranking and optional low-priority fuzzy fill."""
        if not query or not str(query).strip():
            return []

        query = str(query).strip()
        type_filter = resource_type or category

        exact_results = self.index.search(
            query, top_k=top_k, resource_type=type_filter
        )

        # Fuzzy matching must not dominate exact BM25 matches: only fill when
        # exact results are sparse, and always with lower scores.
        if fuzzy and len(exact_results) < min(3, top_k):
            fuzzy_results = self._fuzzy_search(
                query, top_k=top_k, resource_type=type_filter
            )
            existing_ids = {r.document.resource_id for r in exact_results}
            best_exact = exact_results[0].score if exact_results else 0.0
            for fr in fuzzy_results:
                if fr.document.resource_id in existing_ids:
                    continue
                # Cap fuzzy below any exact hit.
                fr.score = min(fr.score, max(best_exact * 0.45, 0.15))
                exact_results.append(fr)
                existing_ids.add(fr.document.resource_id)

        exact_results.sort(key=lambda r: r.score, reverse=True)
        self._add_to_recent(query)
        return exact_results[:top_k]

    def _fuzzy_search(
        self,
        query: str,
        top_k: int,
        resource_type: str | None,
    ) -> list[SearchResult]:
        results: list[SearchResult] = []
        query_lower = query.lower()
        seen: set[str] = set()

        for doc in self.index.documents:
            if resource_type and doc.resource_type != resource_type:
                continue
            title_sim = SequenceMatcher(None, query_lower, doc.title.lower()).ratio()
            tag_blob = " ".join(doc.tags).lower()
            tag_sim = SequenceMatcher(None, query_lower, tag_blob).ratio() if tag_blob else 0.0
            # Token-level fuzzy against title words and tags
            token_best = 0.0
            for token in query_lower.split():
                if len(token) < 3:
                    continue
                for candidate in [doc.title.lower(), *doc.tags, doc.resource_type]:
                    token_best = max(
                        token_best,
                        SequenceMatcher(None, token, candidate.lower()).ratio(),
                    )
                # Partial ratio against full title
                if token in doc.title.lower() or token in tag_blob:
                    token_best = max(token_best, 0.85)

            similarity = max(title_sim, tag_sim * 0.9, token_best * 0.95)
            if similarity < 0.62:
                continue
            if doc.resource_id in seen:
                continue
            seen.add(doc.resource_id)
            results.append(
                SearchResult(
                    document=doc,
                    score=similarity * 0.4,  # intentionally below typical BM25
                    snippet=escape(doc.summary)[:200],
                    match_reason=f"fuzzy~{similarity:.2f}",
                )
            )

        results.sort(key=lambda r: r.score, reverse=True)
        return results[:top_k]

    def fuzzy_diagnose(self, query: str) -> FuzzyOutcome:
        """Return diagnostic info for a misspelled query (acceptance reporting)."""
        results = self.search(query, top_k=5, fuzzy=True)
        top = results[0] if results else None
        # Estimate correction via closest title/tag token
        corrected = None
        best = 0.0
        q = query.lower()
        for doc in self.index.documents:
            for candidate in [doc.title, *doc.tags, doc.resource_type]:
                sim = SequenceMatcher(None, q, candidate.lower()).ratio()
                if sim > best:
                    best = sim
                    corrected = candidate
            for token in q.split():
                for candidate in doc.title.lower().split() + [t.lower() for t in doc.tags]:
                    sim = SequenceMatcher(None, token, candidate).ratio()
                    if sim > best:
                        best = sim
                        corrected = candidate
        relevant = bool(top and top.score > 0)
        return FuzzyOutcome(
            original_query=query,
            corrected_query=corrected,
            fuzzy_score=best,
            top_result=top,
            relevant=relevant,
        )

    def get_suggestions(self, prefix: str = "", limit: int = 8) -> list[SearchSuggestion]:
        if prefix and len(prefix) >= 2:
            prefix_lower = prefix.lower()
            suggestions: list[SearchSuggestion] = []
            seen: set[str] = set()
            for doc in self.index.documents:
                title_lower = doc.title.lower()
                if prefix_lower in title_lower and doc.resource_id not in seen:
                    suggestions.append(
                        SearchSuggestion(query=doc.title, category=doc.resource_type)
                    )
                    seen.add(doc.resource_id)
            return suggestions[:limit]
        return [SearchSuggestion(query=q) for q in DEFAULT_SUGGESTIONS[:limit]]

    def supported_suggestions(self) -> list[str]:
        return list(DEFAULT_SUGGESTIONS)

    def get_recent_searches(self) -> list[str]:
        return self._recent_searches[:]

    def add_recent(self, query: str) -> list[str]:
        """Public helper used by the UI session-state layer."""
        self._add_to_recent(query)
        return self.get_recent_searches()

    @staticmethod
    def dedupe_recent(recent: list[str], query: str, max_items: int = 10) -> list[str]:
        """Insert query at front, remove duplicates, cap length."""
        q = (query or "").strip()
        if not q:
            return list(recent)[:max_items]
        items = [q] + [r for r in recent if r != q]
        return items[:max_items]

    def _add_to_recent(self, query: str) -> None:
        self._recent_searches = self.dedupe_recent(self._recent_searches, query, self._max_recent)

    def get_categories(self) -> list[str]:
        return list(self.index.get_stats().get("resource_types") or [])

    def get_stats(self) -> dict[str, Any]:
        return self.index.get_stats()

    def rebuild_index(self) -> int:
        reset_search_index()
        self.index = get_search_index()
        return self.index.build_index(force_rebuild=True)

    def actions_for(self, doc: SearchDocument) -> list[str]:
        return list(doc.actions or [])


_search_service: SearchService | None = None


def get_search_service() -> SearchService:
    global _search_service
    if _search_service is None:
        _search_service = SearchService()
    return _search_service


def reset_search_service() -> None:
    global _search_service
    _search_service = None
