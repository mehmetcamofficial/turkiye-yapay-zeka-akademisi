"""V5 cross-encoder contract and pipeline tests."""
import json
import sys
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(PROJECT_ROOT), str(PROJECT_ROOT.parent)]

from search_pipeline.cross_encoder_contracts import (
    CrossEncoderPair,
    DOCUMENT_VARIANTS,
    build_pairs,
    build_document_text,
    serialize_pairs,
    MAX_QUERY_LENGTH,
    MAX_DOCUMENT_LENGTH,
)
from search_pipeline.contracts import SearchRequest, RANKING_POLICIES


def test_document_variants():
    assert DOCUMENT_VARIANTS == {"title_only", "title_category", "title_category_brand", "title_compact_metadata"}


def test_build_document_text_variants():
    title = "Kablosuz Kulaklık"
    category = "Elektronik"
    brand = "BrandX"
    attrs = "renk: siyah, materyal: plastik"

    text_a = build_document_text(title, category, brand, attrs, variant="title_only")
    assert text_a == "Kablosuz Kulaklık"
    assert "Elektronik" not in text_a

    text_b = build_document_text(title, category, brand, attrs, variant="title_category")
    assert "Kablosuz Kulaklık" in text_b
    assert "Elektronik" in text_b
    assert "BrandX" not in text_b

    text_c = build_document_text(title, category, brand, attrs, variant="title_category_brand")
    assert "Kablosuz Kulaklık" in text_c
    assert "Elektronik" in text_c
    assert "BrandX" in text_c

    text_d = build_document_text(title, category, brand, attrs, variant="title_compact_metadata")
    assert "Kablosuz Kulaklık" in text_d
    assert "Elektronik" in text_d
    assert "BrandX" in text_d
    assert "renk: siyah" in text_d


def test_build_document_text_truncation():
    long_title = "A" * 1000
    text = build_document_text(long_title, "", "", "", variant="title_only")
    assert len(text) <= MAX_DOCUMENT_LENGTH


def test_build_document_text_unknown_variant():
    try:
        build_document_text("title", "cat", "brand", "attrs", variant="unknown")
    except ValueError:
        pass
    else:
        raise AssertionError("Unknown variant should raise ValueError")


def test_build_pairs_deterministic():
    candidates = [
        {"item_id": "ITEM_001", "title": "Kulaklık", "category": "Elektronik", "brand": "BrandX"},
        {"item_id": "ITEM_002", "title": "Telefon", "category": "Elektronik", "brand": "BrandY"},
    ]
    pairs_a = build_pairs("kablosuz kulaklık", candidates, document_variant="title_category_brand")
    pairs_b = build_pairs("kablosuz kulaklık", candidates, document_variant="title_category_brand")
    assert len(pairs_a) == 2
    assert [p.item_id for p in pairs_a] == [p.item_id for p in pairs_b]
    assert pairs_a[0].document_text == pairs_b[0].document_text


def test_build_pairs_skips_missing_title():
    candidates = [
        {"item_id": "ITEM_001", "title": "Kulaklık", "category": "Elektronik"},
        {"item_id": "ITEM_002", "title": "", "category": "Elektronik"},
    ]
    pairs = build_pairs("kablosuz kulaklık", candidates, document_variant="title_only")
    assert len(pairs) == 1
    assert pairs[0].item_id == "ITEM_001"


def test_build_pairs_pool_size():
    candidates = [{"item_id": f"ITEM_{i:03d}", "title": f"Title {i}"} for i in range(10)]
    pairs = build_pairs("query", candidates, pool_size=5)
    assert len(pairs) == 5


def test_build_pairs_query_too_long():
    long_query = "x" * (MAX_QUERY_LENGTH + 1)
    candidates = [{"item_id": "ITEM_001", "title": "Title"}]
    try:
        build_pairs(long_query, candidates)
    except ValueError:
        pass
    else:
        raise AssertionError("Long query should raise ValueError")


def test_cross_encoder_pair_validation():
    pair = CrossEncoderPair(
        query="kablosuz kulaklık",
        item_id="ITEM_001",
        title="Kulaklık",
        document_variant="title_category_brand",
        document_text="Kulaklık Elektronik BrandX",
    )
    assert pair.validate() is pair


def test_cross_encoder_pair_validation_empty_query():
    pair = CrossEncoderPair(query="", item_id="ITEM_001", title="Title")
    try:
        pair.validate()
    except ValueError:
        pass
    else:
        raise AssertionError("Empty query should raise ValueError")


def test_cross_encoder_pair_validation_empty_item_id():
    pair = CrossEncoderPair(query="query", item_id="", title="Title")
    try:
        pair.validate()
    except ValueError:
        pass
    else:
        raise AssertionError("Empty item_id should raise ValueError")


def test_cross_encoder_pair_validation_empty_title():
    pair = CrossEncoderPair(query="query", item_id="ITEM_001", title="")
    try:
        pair.validate()
    except ValueError:
        pass
    else:
        raise AssertionError("Empty title should raise ValueError")


def test_cross_encoder_pair_validation_unknown_variant():
    pair = CrossEncoderPair(query="query", item_id="ITEM_001", title="Title", document_variant="unknown")
    try:
        pair.validate()
    except ValueError:
        pass
    else:
        raise AssertionError("Unknown variant should raise ValueError")


def test_serialize_pairs():
    pairs = build_pairs("query", [{"item_id": "ITEM_001", "title": "Title"}], document_variant="title_only")
    serialized = serialize_pairs(pairs)
    assert len(serialized) == 1
    assert serialized[0]["item_id"] == "ITEM_001"
    assert serialized[0]["query"] == "query"
    assert serialized[0]["document_variant"] == "title_only"
    # Verify JSON serializable
    json.dumps(serialized)


def test_request_contract_includes_cross_encoder_policies():
    assert "cross_encoder" in RANKING_POLICIES
    assert "hybrid_cross_encoder_blend" in RANKING_POLICIES


def test_request_contract_accepts_cross_encoder_policy():
    req = SearchRequest(
        query="kablosuz kulaklık",
        final_ranking_policy="cross_encoder",
        top_k=5,
        candidate_pool_size=20,
    )
    assert req.validate().final_ranking_policy == "cross_encoder"


def test_request_contract_accepts_hybrid_blend_policy():
    req = SearchRequest(
        query="kablosuz kulaklık",
        final_ranking_policy="hybrid_cross_encoder_blend",
        top_k=5,
        candidate_pool_size=20,
    )
    assert req.validate().final_ranking_policy == "hybrid_cross_encoder_blend"


def test_request_contract_rejects_unknown_policy():
    req = SearchRequest(query="x", final_ranking_policy="unknown_policy")
    try:
        req.validate()
    except ValueError:
        pass
    else:
        raise AssertionError("Unknown policy should raise ValueError")


def test_response_serialization_no_path():
    from search_pipeline.contracts import SearchResponse
    r = SearchResponse(
        True, "id", "4.0", "q", "q", "hybrid_rrf", "cross_encoder",
        results=[{"item_id": "ITEM_001", "cross_encoder_score": 0.5}],
    )
    raw = json.dumps(r.to_dict())
    assert "/Users/" not in raw
    assert "/tmp/" not in raw
    assert "traceback" not in raw
