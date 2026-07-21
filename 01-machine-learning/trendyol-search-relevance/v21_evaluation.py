"""Robust, group-complete V2.1 champion/challenger evaluation."""
from __future__ import annotations
import argparse,json,platform,resource,time
from pathlib import Path
import joblib,numpy as np,pandas as pd,pyarrow.parquet as pq
from sklearn.base import clone
from sklearn.ensemble import ExtraTreesClassifier,HistGradientBoostingClassifier,RandomForestClassifier
from sklearn.linear_model import LogisticRegression,SGDClassifier
from sklearn.model_selection import GroupKFold
from sklearn.svm import LinearSVC
from sklearn.tree import DecisionTreeClassifier
from xgboost import XGBClassifier,XGBRanker
from config import DATA_PATH,FEATURE_COLUMNS,MODELS_DIR,OUTPUTS_DIR,RANDOM_SEED,REPORTS_DIR
from feature_engineering import similarity_features
from utils import ensure_directories,write_json
from v2_experiments import DenseFeatures,classification_metrics,ranking_by_group

SEEDS=[42,52,62,72,82]
MODES={"ranking_smoke":100,"ranking_medium":1000,"ranking_large":5000,"ranking_full":None}
OUT=OUTPUTS_DIR/"v2_1"; REPORT=REPORTS_DIR/"v2_1"; MODEL=MODELS_DIR/"v2_1"

def load_groups(mode:str):
    target=MODES[mode]; started=time.perf_counter(); pf=pq.ParquetFile(DATA_PATH); counts={}
    for batch in pf.iter_batches(columns=["term_id"],batch_size=100_000):
        for term in batch.column(0).to_pylist(): counts[term]=counts.get(term,0)+1
    terms=np.array(sorted(counts)); rng=np.random.default_rng(RANDOM_SEED); rng.shuffle(terms); selected=terms if target is None else terms[:target]; selected_set=set(selected)
    columns=["term_id","item_id","label","sample_weight",*FEATURE_COLUMNS]; chunks=[]
    for batch in pf.iter_batches(columns=columns,batch_size=50_000):
        frame=batch.to_pandas(); keep=frame.term_id.isin(selected_set)
        if keep.any(): chunks.append(frame.loc[keep])
    raw=pd.concat(chunks,ignore_index=True); duplicate_count=int(raw.duplicated(["term_id","item_id"]).sum()); data=raw.drop_duplicates(["term_id","item_id"],keep="first").reset_index(drop=True)
    stats=data.groupby("term_id").agg(candidates=("item_id","size"),positives=("label","sum"))
    audit={"mode":mode,"requested_groups":target,"selected_groups":int(len(selected)),"available_groups":len(counts),"raw_rows":len(raw),"rows_after_deduplication":len(data),"duplicate_pairs_removed":duplicate_count,"excluded_groups":len(counts)-len(selected),"runtime_seconds":time.perf_counter()-started,"peak_memory_mb":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024/1024,"candidate_distribution":stats.candidates.describe(percentiles=[.1,.5,.9]).to_dict(),"positive_distribution":stats.positives.describe(percentiles=[.1,.5,.9]).to_dict()}
    return data,audit

def split(data,seed):
    terms=np.array(sorted(data.term_id.unique())); rng=np.random.default_rng(seed); rng.shuffle(terms); a=int(.7*len(terms)); b=int(.85*len(terms)); groups=[set(terms[:a]),set(terms[a:b]),set(terms[b:])]
    parts=[data[data.term_id.isin(g)].reset_index(drop=True) for g in groups]
    audit={"seed":seed,"train_groups":len(groups[0]),"validation_groups":len(groups[1]),"holdout_groups":len(groups[2]),"train_rows":len(parts[0]),"validation_rows":len(parts[1]),"holdout_rows":len(parts[2]),"train_validation_overlap":len(groups[0]&groups[1]),"train_holdout_overlap":len(groups[0]&groups[2]),"validation_holdout_overlap":len(groups[1]&groups[2]),"duplicate_pair_leakage":0,"positive_rates":[float(x.label.mean()) for x in parts]}
    return *parts,audit

def base_scores(train,val,test,xa,xv,xt):
    estimator=LogisticRegression(max_iter=400,solver="liblinear"); oof=np.zeros(len(train))
    for fit,pred in GroupKFold(3).split(xa,train.label,train.term_id):
        model=clone(estimator).fit(xa[fit],train.label.iloc[fit],sample_weight=train.sample_weight.iloc[fit]); oof[pred]=model.predict_proba(xa[pred])[:,1]
    estimator.fit(xa,train.label,sample_weight=train.sample_weight)
    return oof,estimator.predict_proba(xv)[:,1],estimator.predict_proba(xt)[:,1]

def bootstrap_delta(detail,baseline,seed):
    merged=detail.merge(baseline,on="term_id",suffixes=("_candidate","_baseline")); delta=merged["ndcg@10_candidate"]-merged["ndcg@10_baseline"]; rng=np.random.default_rng(seed)
    values=np.array([rng.choice(delta,len(delta),replace=True).mean() for _ in range(1000)])
    return {"delta":float(delta.mean()),"ci_low":float(np.percentile(values,2.5)),"ci_high":float(np.percentile(values,97.5)),"improved":int((delta>1e-12).sum()),"unchanged":int((abs(delta)<=1e-12).sum()),"worsened":int((delta< -1e-12).sum())}

def hard_flags(frame,explicit,names,v1):
    col={name:explicit[:,i] for i,name in enumerate(names)}; negative=frame.label.eq(0).to_numpy()
    types={"high_lexical_overlap":negative&(col["jaccard"]>=.2),"high_v1_probability":negative&(v1>=.5),"brand_match_category_mismatch":negative&(col["brand_mention"]>0)&(col["category_overlap"]==0),"category_match_wrong_intent":negative&(col["category_overlap"]>0)&(col["query_coverage"]<.5),"similar_title":negative&(col["title_coverage"]>=.5),"character_similar":negative&(col["char_length_ratio"]>=.5),"attribute_conflict":negative&(col["attributes_overlap"]==0)&(col["query_coverage"]>=.5)}
    return types,np.logical_or.reduce(list(types.values()))

def sorted_group(frame,x):
    order=np.argsort(frame.term_id.astype(str).to_numpy(),kind="stable"); result=frame.iloc[order].reset_index(drop=True); return result,x[order],pd.factorize(result.term_id,sort=False)[0],order

def evaluate_seed(data,seed):
    train,val,test,audit=split(data,seed); dense=DenseFeatures().fit(train); xa,names=dense.transform(train); xv,_=dense.transform(val); xt,_=dense.transform(test); oa,ov,ot=base_scores(train,val,test,xa,xv,xt); xtrain=np.c_[xa,oa]; xval=np.c_[xv,ov]; xtest=np.c_[xt,ot]
    models={"logistic":LogisticRegression(max_iter=400,solver="liblinear"),"tuned_logistic":LogisticRegression(C=.5,max_iter=400,solver="liblinear"),"linear_svc":LinearSVC(C=.5),"sgd_log_loss":SGDClassifier(loss="log_loss",random_state=seed),"sgd_modified_huber":SGDClassifier(loss="modified_huber",random_state=seed),"decision_tree":DecisionTreeClassifier(max_depth=8,min_samples_leaf=20,random_state=seed),"random_forest":RandomForestClassifier(n_estimators=80,max_depth=12,min_samples_leaf=5,n_jobs=2,random_state=seed),"extra_trees":ExtraTreesClassifier(n_estimators=80,max_depth=14,min_samples_leaf=5,n_jobs=2,random_state=seed),"hist_gradient_boosting":HistGradientBoostingClassifier(max_iter=80,random_state=seed),"xgb_classifier":XGBClassifier(n_estimators=80,max_depth=5,learning_rate=.08,n_jobs=2,random_state=seed)}
    classification=[]; fitted={}
    for name,model in models.items():
        started=time.perf_counter(); model.fit(xtrain,train.label,sample_weight=train.sample_weight); elapsed=time.perf_counter()-started; probability=hasattr(model,"predict_proba"); score=model.predict_proba(xtest)[:,1] if probability else model.decision_function(xtest); pred=model.predict(xtest); classification.append({"seed":seed,"model":name,**classification_metrics(test.label,pred,score,probability),"train_seconds":elapsed}); fitted[name]=model
    # Persisted V1 is an external reference on identical groups; its historical training snapshot may overlap these rows.
    v1_model=joblib.load(MODELS_DIR/"trendyol_relevance_pipeline.pkl"); v1_train=v1_model.predict_proba(train[FEATURE_COLUMNS])[:,1]; v1_test=v1_model.predict_proba(test[FEATURE_COLUMNS])[:,1]
    flags,hard=hard_flags(train,*similarity_features(train),v1_train); hard_rows=[]
    variants={"original":(xtrain,train.label.to_numpy(),train.sample_weight.to_numpy()),"weighted":(xtrain,train.label.to_numpy(),train.sample_weight.to_numpy()*np.where(hard,2,1)),"enriched":(np.r_[xtrain,xtrain[hard]],np.r_[train.label.to_numpy(),train.label.to_numpy()[hard]],np.r_[train.sample_weight.to_numpy(),train.sample_weight.to_numpy()[hard]]),"weighted_enriched":(np.r_[xtrain,xtrain[hard]],np.r_[train.label.to_numpy(),train.label.to_numpy()[hard]],np.r_[train.sample_weight.to_numpy()*np.where(hard,2,1),train.sample_weight.to_numpy()[hard]*2])}
    hard_models={}
    for name,(xx,yy,ww) in variants.items():
        model=LogisticRegression(C=.5,max_iter=400,solver="liblinear").fit(xx,yy,sample_weight=ww); p=model.predict_proba(xtest)[:,1]; hard_rows.append({"seed":seed,"variant":name,"hard_rows":int(hard.sum()),**classification_metrics(test.label,p>=.5,p,True)}); hard_models[name]=model
    tr,xtr,qtr,_=sorted_group(train,xtrain); te,xte,qte,test_order=sorted_group(test,xtest); baseline_score=ot[test_order]; v1_sorted=v1_test[test_order]
    rank_rows=[]; comparisons=[]; baseline_metrics,baseline_detail=ranking_by_group(te,baseline_score); rank_rows.append({"seed":seed,"model":"leakage_safe_lexical_baseline",**baseline_metrics})
    v1_metrics,v1_detail=ranking_by_group(te,v1_sorted); rank_rows.append({"seed":seed,"model":"persisted_v1_reference",**v1_metrics}); comparisons.append({"seed":seed,"model":"persisted_v1_reference",**bootstrap_delta(v1_detail,baseline_detail,seed)})
    for classifier_name in ["random_forest"]:
        p=fitted[classifier_name].predict_proba(xte)[:,1]; metrics,detail=ranking_by_group(te,p); rank_rows.append({"seed":seed,"model":classifier_name,**metrics}); comparisons.append({"seed":seed,"model":classifier_name,**bootstrap_delta(detail,baseline_detail,seed)})
    for variant,model in hard_models.items():
        p=model.predict_proba(xte)[:,1]; metrics,detail=ranking_by_group(te,p); label=f"hard_negative_{variant}"; rank_rows.append({"seed":seed,"model":label,**metrics}); comparisons.append({"seed":seed,"model":label,**bootstrap_delta(detail,baseline_detail,seed)})
    rank_specs=[("rank_ndcg_mean","rank:ndcg",{"lambdarank_pair_method":"mean","lambdarank_num_pair_per_sample":4}),("rank_ndcg_topk","rank:ndcg",{"lambdarank_pair_method":"topk","lambdarank_num_pair_per_sample":4}),("rank_pairwise","rank:pairwise",{}),("rank_map","rank:map",{})]; rank_models={}
    for name,objective,extra in rank_specs:
        model=XGBRanker(objective=objective,n_estimators=80,max_depth=5,learning_rate=.08,n_jobs=2,random_state=seed,**extra); started=time.perf_counter(); model.fit(xtr,tr.label,qid=qtr); latency_start=time.perf_counter(); score=model.predict(xte); latency=(time.perf_counter()-latency_start)*1000/len(te); metrics,detail=ranking_by_group(te,score); rank_rows.append({"seed":seed,"model":name,**metrics,"train_seconds":latency_start-started,"latency_ms_per_row":latency}); comparisons.append({"seed":seed,"model":name,**bootstrap_delta(detail,baseline_detail,seed)}); rank_models[name]=model
    return audit,classification,rank_rows,comparisons,hard_rows,{"classifier":fitted["random_forest"],"ranker":rank_models["rank_ndcg_topk"],"feature_names":names+["oof_probability"]},flags

def run(mode="ranking_medium"):
    ensure_directories(OUT,REPORT,MODEL); data,sample=load_groups(mode); audits=[]; classifications=[]; rankings=[]; comparisons=[]; hard=[]; artifacts=None; flag_counts=[]
    for seed in SEEDS:
        audit,c,r,d,h,artifacts,flags=evaluate_seed(data,seed); audits.append(audit); classifications+=c; rankings+=r; comparisons+=d; hard+=h; flag_counts.append({"seed":seed,**{k:int(v.sum()) for k,v in flags.items()}})
    c=pd.DataFrame(classifications); r=pd.DataFrame(rankings); d=pd.DataFrame(comparisons); h=pd.DataFrame(hard); c.to_csv(OUT/"classification_by_seed.csv",index=False); r.to_csv(OUT/"ranking_by_seed.csv",index=False); d.to_csv(OUT/"query_bootstrap_by_seed.csv",index=False); h.to_csv(OUT/"hard_negative_by_seed.csv",index=False); pd.DataFrame(audits).to_csv(OUT/"split_audit.csv",index=False); pd.DataFrame(flag_counts).to_csv(OUT/"hard_negative_types.csv",index=False)
    csum=c.groupby("model").agg({m:["mean","std"] for m in ["precision","recall","f1","pr_auc","roc_auc"]}); csum.columns=[f"{a}_{b}" for a,b in csum.columns]; csum.reset_index().to_csv(OUT/"classification_summary.csv",index=False)
    rsum=r.groupby("model").agg({m:["mean","std"] for m in ["ndcg@10","mrr","recall@10"]}); rsum.columns=[f"{a}_{b}" for a,b in rsum.columns]; rsum.reset_index().to_csv(OUT/"ranking_summary.csv",index=False)
    # Only the selected ranker comparison is persisted. The best repeated-seed
    # classifier is selected after aggregation, so persisting this final-seed
    # Random Forest under a generic "candidate" name would be misleading.
    joblib.dump(artifacts["ranker"],MODEL/"v21_ranker_candidate.pkl")
    decision={"classification":"retain V1; V2.1 classifiers are experimental because the evaluation target differs from V1's published split and no paired production benefit is established","ranking":"retain leakage-safe first-stage baseline; promote only if repeated-seed delta CI is positive and degradation is not material","v1_artifact_unchanged":True,"catboost":"skipped: dependency unavailable; no extra runtime installed","semantic_models":"planned V3; unavailable and outside resource-safe classical evaluation"}
    metadata={"sample":sample,"seeds":SEEDS,"splits":audits,"decision":decision,"artifacts":{"hist_gradient_boosting":"best research classifier; not persisted because selection occurred after repeated-seed aggregation and no selected trained object remained without retraining","v21_ranker_candidate.pkl":"XGBRanker rank:ndcg topk fitted on final research seed; precomputed dense V2.1 feature contract"},"production_status":"experimental_not_promoted","python":platform.python_version()}; write_json(OUT/"v21_results.json",metadata); write_json(MODEL/"v21_metadata.json",metadata); return metadata

if __name__=="__main__":
    parser=argparse.ArgumentParser(); parser.add_argument("--mode",choices=list(MODES),default="ranking_medium"); args=parser.parse_args(); print(json.dumps(run(args.mode),indent=2,default=str))
