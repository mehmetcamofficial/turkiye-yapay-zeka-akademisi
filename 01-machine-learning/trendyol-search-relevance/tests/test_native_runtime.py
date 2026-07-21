import sys
from pathlib import Path

import numpy as np

PROJECT_ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(PROJECT_ROOT),str(PROJECT_ROOT.parent)]


def test_xgboost_worker_survives_semantic_before_and_after():
    from retrieval.semantic import encode_texts,load_encoder
    from portfolio.trendyol_native_service import ranker_predict,ranker_worker
    model=load_encoder(PROJECT_ROOT)
    assert encode_texts(model,["kablosuz kulaklık"],kind="query").shape==(1,384)
    result=ranker_predict(np.zeros((2,30),dtype=np.float32),top_k=2)
    assert result["success"] and len(result["results"])==2
    assert encode_texts(model,["spor ayakkabı"],kind="query").shape==(1,384)
    pid=ranker_worker().process.pid
    for _ in range(5):
        assert ranker_predict(np.ones((2,30),dtype=np.float32),top_k=1)["success"]
        assert ranker_worker().process.pid==pid


def test_ranker_worker_rejects_bad_feature_contract():
    from portfolio.trendyol_native_service import ranker_predict
    try:ranker_predict(np.zeros((1,29),dtype=np.float32))
    except RuntimeError as exc:assert "validated" in str(exc)
    else:raise AssertionError("Invalid feature contract must fail safely")
