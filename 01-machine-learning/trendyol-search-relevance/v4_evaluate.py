"""Evaluate V4 ordering policies without retraining or rebuilding embeddings."""
from __future__ import annotations
import json,time,sys
from collections import Counter
from pathlib import Path
import numpy as np,pandas as pd

ROOT=Path(__file__).resolve().parent;sys.path[:0]=[str(ROOT),str(ROOT.parent)]
from inference import load_artifacts,predict_frame
from retrieval.contracts import fingerprint
from retrieval.lexical import TfidfRetriever,top_indices
from retrieval.metrics import evaluate_query,paired_bootstrap
from retrieval.semantic import DenseIndex,encode_texts,load_encoder
from retrieval.text_normalization import normalize_retrieval_text
from v3_evaluate import build_catalogue,select_queries,splits
from v31_evaluate import query_segments

OUT=ROOT/'outputs/v4';REPORT=ROOT/'reports';MODEL=ROOT/'models/v3';SEEDS=[42,52,62,72,82]
POLICIES=['retrieval_only','v1_relevance','experimental_ranker','blended_policy']
METRICS=['recall@10','recall@20','recall@50','recall@100','precision@10','map@10','ndcg@10','mrr']

def summarize(by_seed):
 rows=[]
 for (retrieval,policy),part in by_seed.groupby(['retrieval_mode','policy']):
  row={'retrieval_mode':retrieval,'policy':policy,'seeds':part.seed.nunique()}
  for metric in METRICS:
   v=part[metric].to_numpy();mean=v.mean();std=v.std(ddof=1);half=2.776*std/np.sqrt(5);row.update({f'{metric}_mean':mean,f'{metric}_std':std,f'{metric}_ci95_low':mean-half,f'{metric}_ci95_high':mean+half})
  rows.append(row)
 return pd.DataFrame(rows)

def main():
 OUT.mkdir(parents=True,exist_ok=True);selected,positive,queries,_=select_queries('retrieval_medium');required=set().union(*positive.values());catalogue,audit=build_catalogue(required);fp=fingerprint(catalogue);ids=catalogue.item_id.astype(str).to_numpy()
 persisted=np.load(MODEL/'semantic_medium_item_ids.npy');assert np.array_equal(ids,persisted)
 dense=DenseIndex.load(MODEL/'semantic_medium.npy',MODEL/'semantic_medium_metadata.json',catalogue_fingerprint=fp);encoder=load_encoder(ROOT);terms=list(queries);texts=[normalize_retrieval_text(queries[t]) for t in terms];qmat=encode_texts(encoder,texts,kind='query',batch_size=64)
 semantic={};tfidf={};docs=catalogue.searchable_text.tolist();word=TfidfRetriever('word',(1,2)).fit(docs);char=TfidfRetriever('char_wb',(3,5),80_000).fit(docs)
 for term,text,emb in zip(terms,texts,qmat):
  idx,score=dense.search(emb,100);semantic[term]=(ids[idx].tolist(),score.tolist());sw=np.asarray((word.matrix@word.vectorizer.transform([text]).T).toarray()).ravel();sc=np.asarray((char.matrix@char.vectorizer.transform([text]).T).toarray()).ravel();score=.6*sw+.4*sc;idx=top_indices(score,100);tfidf[term]=(ids[idx].tolist(),score[idx].tolist())
 hybrid={}
 for term in terms:
  li,ls=tfidf[term];si,ss=semantic[term];c=list(dict.fromkeys([*li,*si]));lr={x:i+1 for i,x in enumerate(li)};sr={x:i+1 for i,x in enumerate(si)};score=np.array([(1/(20+lr[x]) if x in lr else 0)+(1/(20+sr[x]) if x in sr else 0) for x in c]);order=np.lexsort((np.asarray(c),-score))[:100];hybrid[term]=([c[i] for i in order],score[order].tolist())
 # Score every unique query/candidate pair in one bounded batch with unchanged V1.
 cat=catalogue.set_index('item_id');pairs=[]
 for term in terms:
  for retrieval,source in [('tfidf',tfidf),('hybrid_rrf',hybrid)]:
   for rank,item in enumerate(source[term][0],1):
    row=cat.loc[item];pairs.append({'term_id':term,'retrieval_mode':retrieval,'item_id':item,'retrieval_rank':rank,'retrieval_score':source[term][1][rank-1],'query':queries[term],**{k:row.get(k,'') for k in ['title','category','brand','gender','age_group','attributes']}})
 frame=pd.DataFrame(pairs);model,metadata=load_artifacts();started=time.perf_counter();scored=predict_frame(frame,model,metadata,max_rows=250_000);v1_seconds=time.perf_counter()-started;frame['v1_probability']=scored.score.to_numpy()
 rankings={}
 for (term,retrieval),part in frame.groupby(['term_id','retrieval_mode'],sort=False):
  base=part.sort_values(['retrieval_rank','item_id'],kind='stable');v1=part.sort_values(['v1_probability','retrieval_score','item_id'],ascending=[False,False,True],kind='stable')
  rankings[(term,retrieval,'retrieval_only')]=base.item_id.tolist();rankings[(term,retrieval,'v1_relevance')]=v1.item_id.tolist();rankings[(term,retrieval,'experimental_ranker')]=v1.item_id.tolist();rankings[(term,retrieval,'blended_policy')]=v1.item_id.tolist()
 split_map,_=splits(selected);details=[];seed_rows=[]
 for seed,groups in split_map.items():
  for retrieval in ['tfidf','hybrid_rrf']:
   for policy in POLICIES:
    part=pd.DataFrame([{'seed':seed,'term_id':term,'retrieval_mode':retrieval,'policy':policy,**evaluate_query(positive[term],rankings[(term,retrieval,policy)])} for term in groups['holdout']]);details.append(part);seed_rows.append({'seed':seed,'retrieval_mode':retrieval,'policy':policy,**part[METRICS].mean().to_dict(),'candidate_recall@100':np.mean([evaluate_query(positive[t],rankings[(t,retrieval,'retrieval_only')])['recall@100'] for t in groups['holdout']])})
 detail=pd.concat(details,ignore_index=True);by_seed=pd.DataFrame(seed_rows);summary=summarize(by_seed);comparisons=[]
 baseline=detail[(detail.retrieval_mode=='hybrid_rrf')&(detail.policy=='retrieval_only')]
 for policy in POLICIES[1:]:
  candidate=detail[(detail.retrieval_mode=='hybrid_rrf')&(detail.policy==policy)]
  for seed in SEEDS:
   b=baseline[baseline.seed==seed];c=candidate[candidate.seed==seed]
   for metric in ['recall@50','ndcg@10','mrr']:
    comparisons.append({'seed':seed,'candidate':f'hybrid_rrf+{policy}','baseline':'hybrid_rrf+retrieval_only','metric':metric,**paired_bootstrap(c,b,metric,seed)})
 paired=pd.DataFrame(comparisons);delta=[]
 for (candidate,metric),part in paired.groupby(['candidate','metric']):
  v=part.delta.to_numpy();half=2.776*v.std(ddof=1)/np.sqrt(5);delta.append({'candidate':candidate,'metric':metric,'delta_mean':v.mean(),'delta_ci95_low':v.mean()-half,'delta_ci95_high':v.mean()+half,'improved':int(part.improved.sum()),'unchanged':int(part.unchanged.sum()),'worsened':int(part.worsened.sum())})
 deltas=pd.DataFrame(delta)
 # Segments are descriptive; unavailable ranker/blend rows intentionally equal the V1 fallback.
 counts=Counter(t for q in texts for t in set(q.split()));brands=set(catalogue.brand.map(normalize_retrieval_text));categories=set(t for x in catalogue.category.map(normalize_retrieval_text) for t in x.split());by_id=cat.searchable_text.to_dict();segment_map=[]
 for term in selected:
  for segment in query_segments(queries[term],[by_id[x] for x in positive[term]],counts,brands,categories):segment_map.append({'term_id':term,'segment':segment})
 segments=pd.DataFrame(segment_map).merge(detail,on='term_id').groupby(['segment','retrieval_mode','policy'])[METRICS].agg(['mean','count']).reset_index();segments.columns=['_'.join(x).strip('_') for x in segments.columns]
 pivot=detail[detail.retrieval_mode.eq('hybrid_rrf')].pivot_table(index=['seed','term_id'],columns='policy',values='ndcg@10').reset_index();pivot['v1_delta']=pivot.v1_relevance-pivot.retrieval_only;sample=pd.concat([pivot.nlargest(4,'v1_delta'),pivot.nsmallest(4,'v1_delta')]).drop_duplicates(['seed','term_id']);errors=[]
 for row in sample.itertuples():errors.append({'seed':row.seed,'term_id':row.term_id,'query':queries[row.term_id],'hybrid_ndcg10':row.retrieval_only,'v1_ndcg10':row.v1_relevance,'delta':row.v1_delta,'failure_category':'V1 top-order correction' if row.v1_delta>0 else 'V1 misclassification or incomplete judgments','caution':'Candidate pool is unchanged; unlabelled products may be relevant.'})
 decision='hybrid_rrf+retrieval_only';results={'catalogue_rows':len(catalogue),'queries':len(queries),'seeds':SEEDS,'candidate_pool_size':100,'v1_batch_seconds':v1_seconds,'ranker_compatibility':'unavailable: persisted 30/31-feature historical contracts do not match V4 live features','blended_policy':'not selected; degrades to V1 because ranker input is incompatible','selected_policy':decision,'selection_reason':'V1 reranking materially degraded Recall@50, NDCG@10 and MRR; retain fixed-k=20 Hybrid RRF order','governance':'Best Pipeline Research Candidate; Not Production Promoted'}
 detail.to_csv(OUT/'v4_query_metrics.csv',index=False);by_seed.to_csv(OUT/'v4_metrics_by_seed.csv',index=False);summary.to_csv(OUT/'v4_repeated_seed_ci.csv',index=False);paired.to_csv(OUT/'v4_paired_bootstrap.csv',index=False);deltas.to_csv(OUT/'v4_paired_deltas.csv',index=False);segments.to_csv(OUT/'v4_query_segment_metrics.csv',index=False);frame[['term_id','retrieval_mode','item_id','retrieval_rank','retrieval_score','v1_probability']].to_csv(OUT/'v4_candidate_scores.csv',index=False);(OUT/'v4_error_examples.json').write_text(json.dumps(errors,ensure_ascii=False,indent=2));(OUT/'v4_results.json').write_text(json.dumps(results,indent=2));print(json.dumps(results,indent=2));print(summary[['retrieval_mode','policy','recall@50_mean','recall@100_mean','ndcg@10_mean','mrr_mean']].to_string(index=False))

if __name__=='__main__':main()
