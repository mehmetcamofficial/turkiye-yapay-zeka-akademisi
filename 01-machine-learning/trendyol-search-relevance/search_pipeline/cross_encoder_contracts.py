"""Deterministic cross-encoder input contracts for Search Pipeline V5."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

DOCUMENT_VARIANTS = {"title_only", "title_category", "title_category_brand", "title_compact_metadata"}
MAX_QUERY_LENGTH = 300
MAX_DOCUMENT_LENGTH = 512
MAX_PAIRS_PER_QUERY = 200


@dataclass(frozen=True)
class CrossEncoderPair:
    """A single query-document pair for cross-encoder scoring."""
    query: str
    item_id: str
    title: str
    category: str = ""
    brand: str = ""
    gender: str = ""
    age_group: str = ""
    attributes: str = ""
    source_retrievers: tuple[str, ...] = ()
    fused_rank: int | None = None
    retrieval_score: float | None = None
    relevance_label: int | None = None
    document_variant: str = "title_category_brand"
    document_text: str = ""

    def validate(self) -> "CrossEncoderPair":
        if not isinstance(self.query, str) or not self.query.strip():
            raise ValueError("Query cannot be empty.")
        if len(self.query) > MAX_QUERY_LENGTH:
            raise ValueError("Query is too long.")
        if not isinstance(self.item_id, str) or not self.item_id.strip():
            raise ValueError("item_id cannot be empty.")
        if not isinstance(self.title, str) or not self.title.strip():
            raise ValueError("title cannot be empty.")
        if self.document_variant not in DOCUMENT_VARIANTS:
            raise ValueError(f"Unknown document variant: {self.document_variant}")
        return self


def normalize_text(text: str) -> str:
    """Whitespace-normalize and strip a text field."""
    return " ".join(str(text).split())


def build_document_text(
    title: str,
    category: str,
    brand: str,
    attributes: str,
    variant: str = "title_category_brand",
    attribute_limit: int = 240,
) -> str:
    """Build a bounded document text from catalogue fields.

    Variants:
      A. title_only
      B. title_category
      C. title_category_brand
      D. title_compact_metadata
    """
    if variant not in DOCUMENT_VARIANTS:
        raise ValueError(f"Unknown document variant: {variant}")
    title = normalize_text(title)
    if variant == "title_only":
        return title[:MAX_DOCUMENT_LENGTH]
    category = normalize_text(category)
    parts = [title]
    if category:
        parts.append(category)
    if variant in ("title_category_brand", "title_compact_metadata"):
        brand = normalize_text(brand)
        if brand:
            parts.append(brand)
    if variant == "title_compact_metadata":
        attrs = normalize_text(attributes)[:attribute_limit]
        if attrs:
            parts.append(attrs)
    text = " ".join(parts)
    if len(text) > MAX_DOCUMENT_LENGTH:
        text = text[:MAX_DOCUMENT_LENGTH]
    return text


def build_pairs(
    query: str,
    candidates: list[dict[str, Any]],
    document_variant: str = "title_category_brand",
    pool_size: int | None = None,
) -> list[CrossEncoderPair]:
    """Build deterministic cross-encoder pairs from retrieval candidates.

    Args:
        query: Normalized query text.
        candidates: List of candidate dicts with keys: item_id, title,
            category, brand, gender, age_group, attributes, source_retrievers,
            fused_rank, retrieval_score, relevance_label.
        document_variant: One of DOCUMENT_VARIANTS.
        pool_size: Maximum number of pairs to return.

    Returns:
        List of validated CrossEncoderPair objects, ordered by fused_rank.
    """
    if document_variant not in DOCUMENT_VARIANTS:
        raise ValueError(f"Unknown document variant: {document_variant}")
    query = normalize_text(query)
    if len(query) > MAX_QUERY_LENGTH:
        raise ValueError("Query is too long.")
    if pool_size is not None:
        candidates = candidates[:pool_size]
    pairs: list[CrossEncoderPair] = []
    for candidate in candidates:
        item_id = str(candidate.get("item_id", "")).strip()
        title = str(candidate.get("title", "")).strip()
        if not item_id or not title:
            continue
        document_text = build_document_text(
            title=title,
            category=str(candidate.get("category", "")),
            brand=str(candidate.get("brand", "")),
            attributes=str(candidate.get("attributes", "")),
            variant=document_variant,
        )
        pair = CrossEncoderPair(
            query=query,
            item_id=item_id,
            title=title,
            category=str(candidate.get("category", "")),
            brand=str(candidate.get("brand", "")),
            gender=str(candidate.get("gender", "")),
            age_group=str(candidate.get("age_group", "")),
            attributes=str(candidate.get("attributes", "")),
            source_retrievers=tuple(candidate.get("source_retrievers", [])),
            fused_rank=candidate.get("fused_rank"),
            retrieval_score=candidate.get("retrieval_score"),
            relevance_label=candidate.get("relevance_label"),
            document_variant=document_variant,
            document_text=document_text,
        )
        pairs.append(pair.validate())
    return pairs


def serialize_pairs(pairs: list[CrossEncoderPair]) -> list[dict[str, Any]]:
    """Serialize pairs to a deterministic JSON-safe list."""
    return [
        {
            "query": p.query,
            "item_id": p.item_id,
            "document_text": p.document_text,
            "document_variant": p.document_variant,
            "source_retrievers": list(p.source_retrievers),
            "fused_rank": p.fused_rank,
            "retrieval_score": p.retrieval_score,
            "relevance_label": p.relevance_label,
        }
        for p in pairs
    ]
