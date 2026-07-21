import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = PROJECT_ROOT.parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(REPOSITORY_ROOT / "01-machine-learning"))

import numpy as np,pandas as pd
import json,joblib
from retrieval.contracts import prepare_catalogue,validate_judgments
from retrieval.hybrid import candidate_union,minmax,reciprocal_rank_fusion,weighted_fusion
from retrieval.lexical import BM25Retriever,TfidfRetriever
from retrieval.metrics import evaluate_query,paired_bootstrap
from retrieval.semantic import DenseIndex,MODEL_DIMENSION,encode_texts,load_encoder
from retrieval.text_normalization import build_searchable_text,normalize_retrieval_text

def test_retrieval_normalization_preserves_identifiers():
    cases={"Kablosuz Kulaklık":"kablosuz kulaklık","iPhone 15 Pro Max":"iphone 15 pro max","43 Numara Erkek Ayakkabı":"43 numara erkek ayakkabı","500 ml Şampuan":"500ml şampuan","USB-C Hızlı Şarj":"usb-c hızlı şarj","Çocuk Yağmurluk":"çocuk yağmurluk","Kadın Beyaz Sneaker":"kadın beyaz sneaker","Samsung Galaxy S24 Ultra":"samsung galaxy s24 ultra"}
    for source,want in cases.items():assert normalize_retrieval_text(source)==want
    assert normalize_retrieval_text(None)==""
    weighted=build_searchable_text({"title":"Kulaklık","brand":"Marka"},field_weights={"title":2,"brand":1})
    assert weighted=="kulaklık kulaklık marka"

def test_catalogue_contract_and_determinism():
    raw=pd.DataFrame([{"item_id":"b","title":"İkinci","category":"c","brand":"","gender":"","age_group":"","attributes":""},{"item_id":"a","title":"Birinci","category":"c","brand":"x","gender":"","age_group":"","attributes":""},{"item_id":"a","title":"duplicate","category":"c","brand":"x","gender":"","age_group":"","attributes":""}]); catalogue=prepare_catalogue(raw)
    assert catalogue.item_id.tolist()==["a","b"] and catalogue.item_id.is_unique
    judgments=pd.DataFrame({"term_id":[1],"query":["birinci"],"item_id":["a"],"relevance_label":[1]}); assert validate_judgments(judgments,set(catalogue.item_id))["relevant_item_coverage"]==1

def test_retrieval_metrics_exact():
    result=evaluate_query({"a","c"},["a","b","c"])
    assert result["recall@1"]==.5 and result["recall@5"]==1
    assert result["hit_rate@1"]==1 and result["precision@1"]==1
    assert result["mrr"]==1 and np.isclose(result["map@100"],(1+2/3)/2)
    assert result["candidate_coverage"]==.03 and result["zero_result_rate"]==0
    assert result["relevant_product_availability"]==1 and 0<=result["ndcg@10"]<=1

def test_query_bootstrap_counts():
    base=pd.DataFrame({"term_id":[1,2,3],"recall@50":[0,1,.5]}); cand=pd.DataFrame({"term_id":[1,2,3],"recall@50":[1,1,0]}); result=paired_bootstrap(cand,base); assert (result["improved"],result["unchanged"],result["worsened"])==(1,1,1)

def test_tfidf_and_bm25_ranking_and_empty_query():
    docs=["kablosuz bluetooth kulaklık","kablosuz kulaklık kılıfı","kadın beyaz sneaker","çocuk yağmurluk"]
    for model in [TfidfRetriever().fit(docs),BM25Retriever().fit(docs)]:
        idx,score=model.search("kablosuz kulaklık",3); assert idx[0]==0 and score[idx[0]]>=score[idx[-1]]
        empty,_=model.search("",2); assert len(empty)==2

def test_hybrid_fusion_and_union_are_deterministic():
    assert np.allclose(minmax([1,2]),[0,1])
    assert minmax([]).size==0
    fused=weighted_fusion([0,1],[1,0],.5); assert len(fused)==2
    assert candidate_union(["a","b"],["b","c"])==["a","b","c"]
    assert reciprocal_rank_fusion([1,2],[2,1]).shape==(2,)

def test_semantic_service_uses_real_scores_when_assets_exist():
    from portfolio.trendyol_retrieval_service import search
    result,_=search("kablosuz kulaklık","Semantic",5)
    assert len(result)==5 and result.semantic_score.notna().all()
    assert result.lexical_score.isna().all() and result.retrieval_source.eq("Semantic").all()

def test_group_safe_retrieval_splits():
    from v3_evaluate import splits
    mapping,audit=splits(np.arange(100)); assert len(audit)==5
    for groups in mapping.values():
        assert set(groups["train"]).isdisjoint(groups["validation"])
        assert set(groups["train"]).isdisjoint(groups["holdout"])
        assert set(groups["validation"]).isdisjoint(groups["holdout"])

def test_lexical_asset_reload_and_fingerprint_contract():
    root=PROJECT_ROOT/"models/v3"; asset=joblib.load(root/"lexical_demo.joblib"); metadata=json.loads((root/"lexical_demo_metadata.json").read_text())
    assert asset["fingerprint"]==metadata["fingerprint"] and len(asset["catalogue"])==metadata["rows"]
    assert asset["tfidf"].matrix.shape[0]==asset["bm25"].matrix.shape[0]==len(asset["catalogue"])
    assert np.isfinite(asset["tfidf"].matrix.data).all() and np.isfinite(asset["bm25"].matrix.data).all()

def test_semantic_model_and_query_encoding_contract():
    model=load_encoder(PROJECT_ROOT); values=encode_texts(model,["Kablosuz Kulaklık","iPhone 15 Pro 500 ml"],kind="query",batch_size=2)
    assert values.shape==(2,MODEL_DIMENSION) and values.dtype==np.float32
    assert np.isfinite(values).all() and np.allclose(np.linalg.norm(values,axis=1),1,atol=1e-5)

def test_semantic_missing_cache_fails_clearly(tmp_path,monkeypatch):
    monkeypatch.setenv("TRENDYOL_SEMANTIC_CACHE",str(tmp_path/"missing"))
    try:load_encoder(PROJECT_ROOT)
    except RuntimeError as exc:assert "Model Cache Required" in str(exc)
    else:raise AssertionError("Missing model cache must fail")

def test_dense_index_reload_search_and_corruption(tmp_path):
    matrix=np.zeros((3,MODEL_DIMENSION),dtype=np.float32); matrix[0,0]=1; matrix[1,1]=1; matrix[2,2]=1; matrix_path=tmp_path/"index.npy"; metadata_path=tmp_path/"metadata.json"; np.save(matrix_path,matrix)
    metadata={"product_count":3,"embedding_dimension":MODEL_DIMENSION,"dtype":"float32","model_id":"intfloat/multilingual-e5-small","model_revision":"614241f622f53c4eeff9890bdc4f31cfecc418b3","catalogue_fingerprint":"abc","finite_values":True,"normalized":True}; metadata_path.write_text(json.dumps(metadata))
    query=np.zeros(MODEL_DIMENSION,dtype=np.float32); query[0]=1; index=DenseIndex.load(matrix_path,metadata_path,catalogue_fingerprint="abc"); idx,score=index.search(query,2,2)
    assert idx.tolist()==[0,1] and score.tolist()==[1,0]
    metadata["embedding_dimension"]=MODEL_DIMENSION-1; metadata_path.write_text(json.dumps(metadata))
    try:DenseIndex.load(matrix_path,metadata_path)
    except RuntimeError as exc:assert "dimension" in str(exc)
    else:raise AssertionError("Corrupted index metadata must fail")

def test_dense_index_deterministic_tie_breaking():
    matrix=np.array([[1,0],[1,0],[0,1]],dtype=np.float32); metadata={"product_count":3,"embedding_dimension":2,"dtype":"float32","model_id":"intfloat/multilingual-e5-small","model_revision":"614241f622f53c4eeff9890bdc4f31cfecc418b3","finite_values":True,"normalized":True}; index=DenseIndex(matrix,metadata)
    first,_=index.search(np.array([1,0],dtype=np.float32),3,2); second,_=index.search(np.array([1,0],dtype=np.float32),3,2); assert first.tolist()==second.tolist()==[0,1,2]
