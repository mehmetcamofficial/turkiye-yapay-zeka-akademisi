import hashlib,json,sys
from pathlib import Path
import numpy as np
PROJECT_ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(PROJECT_ROOT),str(PROJECT_ROOT.parent)]
from search_pipeline import SearchPipeline,SearchRequest
from search_pipeline.contracts import SearchResponse

def test_request_contract_defaults_and_bounds():
 r=SearchRequest(query='  Kablosuz Kulaklık  ').validate();assert r.candidate_pool_size==100 and r.retrieval_mode=='hybrid_rrf' and r.final_ranking_policy=='retrieval_only'
 for bad in [SearchRequest(query=''),SearchRequest(query='x',top_k=21,candidate_pool_size=20),SearchRequest(query='x',retrieval_mode='exec'),SearchRequest(query='x',candidate_pool_size=21)]:
  try:bad.validate()
  except ValueError:pass
  else:raise AssertionError('Invalid request accepted')

def test_response_serialization_has_no_path():
 r=SearchResponse(True,'id','4.0','q','q','tfidf','retrieval_only').to_dict();raw=json.dumps(r);assert ('/'+'Users/') not in raw and ('/'+'tmp/') not in raw and 'traceback' not in raw

def test_tfidf_bm25_and_determinism():
 p=SearchPipeline()
 for mode in ['tfidf','bm25']:
  req=SearchRequest(query='kablosuz kulaklık',retrieval_mode=mode,final_ranking_policy='retrieval_only',top_k=5,candidate_pool_size=20);a=p.search(req);b=p.search(req);assert a['success'] and [x['item_id'] for x in a['results']]==[x['item_id'] for x in b['results']]

def test_semantic_hybrid_v1_and_provenance():
 p=SearchPipeline()
 for mode,policy in [('semantic','retrieval_only'),('hybrid_rrf','v1_relevance')]:
  r=p.search(SearchRequest(query='kablosuz kulaklık',retrieval_mode=mode,final_ranking_policy=policy,top_k=5,candidate_pool_size=20));assert r['success'] and len(r['results'])==5
  assert {'retrieval_sources','lexical_rank','semantic_rank','v1_relevance_probability','rank_changes','artifact_versions'}<=r['results'][0].keys()

def test_ranker_and_blend_degrade_explicitly():
 p=SearchPipeline()
 for policy in ['experimental_ranker','blended_policy']:
  r=p.search(SearchRequest(query='usb c adaptör',retrieval_mode='tfidf',final_ranking_policy=policy,top_k=5,candidate_pool_size=20));assert r['success'] and r['pipeline_status']=='degraded' and r['selected_ranking_policy']=='v1_relevance' and r['warnings']

def test_fallbacks_and_empty_filter():
 p=SearchPipeline();r=p.search(SearchRequest(query='x',retrieval_mode='tfidf',final_ranking_policy='v1_relevance',top_k=5,candidate_pool_size=20,simulated_unavailable=('v1_artifact',)));assert r['success'] and r['pipeline_status']=='degraded' and r['selected_ranking_policy']=='retrieval_only'
 empty=p.search(SearchRequest(query='x',retrieval_mode='tfidf',category_filter='does not exist',top_k=5,candidate_pool_size=20));assert empty['success'] and empty['result_count']==0 and empty['pipeline_status']=='zero_result'
 for missing in ['semantic_model','dense_index']:
  unavailable=p.search(SearchRequest(query='x',retrieval_mode='semantic',simulated_unavailable=(missing,),top_k=5,candidate_pool_size=20));assert not unavailable['success'] and unavailable['pipeline_status']=='unavailable'

def test_stage_metrics_complete():
 r=SearchPipeline().search(SearchRequest(query='kadın sneaker',retrieval_mode='tfidf',top_k=5,candidate_pool_size=20));required={'validation_ms','normalization_ms','lexical_load_ms','lexical_search_ms','semantic_model_load_ms','semantic_index_load_ms','semantic_encode_ms','semantic_search_ms','fusion_ms','enrichment_ms','v1_scoring_ms','ranker_worker_ms','final_sort_ms','serialization_ms','total_ms'};assert required<=r['stage_metrics'].keys()

def test_stable_artifact_hashes_and_v4_config():
 expected={'models/trendyol_relevance_pipeline.pkl':'7a06ccdd7594','models/v2/search_ranker.pkl':'f375362db33b','models/v2_1/v21_ranker_candidate.pkl':'1cc392a5fdaa','models/v3/lexical_demo.joblib':'2396d6ad30aa','models/v3/semantic_demo.npy':'6b6578398944'}
 for relative,want in expected.items():assert hashlib.sha256((PROJECT_ROOT/relative).read_bytes()).hexdigest().startswith(want)
 assert json.loads((PROJECT_ROOT/'models/v4/pipeline_config.json').read_text())['rrf_k']==20

def test_worker_contract_is_isolated_and_no_shell():
 source=(PROJECT_ROOT.parent/'portfolio/trendyol_native_service.py').read_text();assert 'shell=True' not in source and 'subprocess.Popen' in source and 'TIMEOUT_SECONDS' in source
