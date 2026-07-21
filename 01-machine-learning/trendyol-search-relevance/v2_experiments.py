"""Group-safe V2 classification and learning-to-rank challenger experiments."""
from __future__ import annotations
import argparse,json,platform,resource,time
from pathlib import Path
import joblib,numpy as np,pandas as pd,pyarrow.parquet as pq
from scipy import sparse
from sklearn.base import clone
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import ExtraTreesClassifier,HistGradientBoostingClassifier,RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression,SGDClassifier
from sklearn.metrics import (average_precision_score,brier_score_loss,f1_score,log_loss,ndcg_score,
 precision_score,recall_score,roc_auc_score)
from sklearn.model_selection import GroupKFold
from sklearn.svm import LinearSVC
from sklearn.tree import DecisionTreeClassifier
from config import DATA_PATH,FEATURE_COLUMNS,MODELS_DIR,OUTPUTS_DIR,RANDOM_SEED,REPORTS_DIR
from feature_engineering import normalized_frame,similarity_features
from utils import ensure_directories,write_json

V2_OUT=OUTPUTS_DIR/"v2"; V2_MODELS=MODELS_DIR/"v2"; V2_REPORTS=REPORTS_DIR/"v2"

def load_complete_groups(mode="ranking-sample"):
    targets={"ranking-smoke":3_000,"ranking-sample":8_000,"ranking-full":None}; target=targets[mode]
    pf=pq.ParquetFile(DATA_PATH); counts={}
    for batch in pf.iter_batches(columns=["term_id"],batch_size=100_000):
        for term in batch.column(0).to_pylist(): counts[term]=counts.get(term,0)+1
    terms=np.array(sorted(counts)); rng=np.random.default_rng(RANDOM_SEED); rng.shuffle(terms)
    if target is not None:
        chosen=[]; rows=0
        for term in terms:
            chosen.append(term); rows+=counts[term]
            if rows>=target: break
        selected=set(chosen)
    else: selected=set(terms)
    columns=["term_id","item_id","label","sample_weight",*FEATURE_COLUMNS]; pieces=[]
    for batch in pf.iter_batches(columns=columns,batch_size=50_000):
        frame=batch.to_pandas(); keep=frame.term_id.isin(selected)
        if keep.any(): pieces.append(frame.loc[keep])
    data=pd.concat(pieces,ignore_index=True).drop_duplicates(["term_id","item_id"],keep="first")
    return data,{"mode":mode,"rows":len(data),"groups":data.term_id.nunique(),"complete_group_sampling":True,"seed":RANDOM_SEED}

def split_groups(data):
    terms=np.array(sorted(data.term_id.unique())); rng=np.random.default_rng(RANDOM_SEED); rng.shuffle(terms)
    n=len(terms); train_terms=set(terms[:int(.70*n)]); val_terms=set(terms[int(.70*n):int(.85*n)]); test_terms=set(terms[int(.85*n):])
    parts=[data[data.term_id.isin(group)].reset_index(drop=True) for group in [train_terms,val_terms,test_terms]]
    report={"train_rows":len(parts[0]),"validation_rows":len(parts[1]),"test_rows":len(parts[2]),"train_groups":len(train_terms),"validation_groups":len(val_terms),"test_groups":len(test_terms),"train_validation_overlap":len(train_terms&val_terms),"train_test_overlap":len(train_terms&test_terms),"validation_test_overlap":len(val_terms&test_terms),"positive_rates":[float(x.label.mean()) for x in parts]}
    return (*parts,report)

class DenseFeatures:
    def fit(self,frame):
        n=normalized_frame(frame); corpus=pd.concat([n.query_text,n.title_text],ignore_index=True)
        self.word=TfidfVectorizer(ngram_range=(1,2),min_df=2,max_features=30_000,sublinear_tf=True).fit(corpus)
        self.char=TfidfVectorizer(analyzer="char_wb",ngram_range=(3,5),min_df=2,max_features=25_000,sublinear_tf=True).fit(corpus)
        self.freq={c:frame[c].fillna("").astype(str).value_counts().to_dict() for c in ["query","item_id","category","brand"]}
        self.codes={c:{v:i+1 for i,v in enumerate(frame[c].fillna("").astype(str).value_counts().index)} for c in ["category","brand","gender","age_group"]}
        return self
    def transform(self,frame):
        n=normalized_frame(frame); explicit,names=similarity_features(frame)
        def cosine(vectorizer):
            q=vectorizer.transform(n.query_text); t=vectorizer.transform(n.title_text)
            return np.asarray(q.multiply(t).sum(axis=1)).ravel()
        arrays=[explicit,cosine(self.word)[:,None],cosine(self.char)[:,None]]; names=names+["word_tfidf_cosine","char_tfidf_cosine"]
        for c in ["category","brand","gender","age_group"]:
            values=frame[c].fillna("").astype(str); arrays += [values.map(self.codes[c]).fillna(0).to_numpy()[:,None],values.eq("").astype(int).to_numpy()[:,None]]; names += [c+"_code",c+"_missing"]
        for c in ["query","item_id","category","brand"]:
            values=frame[c].fillna("").astype(str); arrays.append(values.map(self.freq[c]).fillna(0).to_numpy()[:,None]); names.append(c+"_train_frequency")
        return np.hstack(arrays).astype(np.float32),names

def oof_scores(train,val,test,xtrain,xval,xtest):
    base=LogisticRegression(max_iter=400,solver="liblinear"); svc=LinearSVC(C=1.0)
    oof_prob=np.zeros(len(train)); oof_svc=np.zeros(len(train)); groups=train.term_id
    for fit_idx,pred_idx in GroupKFold(3).split(train,train.label,groups):
        fit=train.iloc[fit_idx]
        for estimator,target in [(clone(base),oof_prob),(clone(svc),oof_svc)]:
            estimator.fit(xtrain[fit_idx],fit.label,sample_weight=fit.sample_weight); target[pred_idx]=estimator.predict_proba(xtrain[pred_idx])[:,1] if hasattr(estimator,"predict_proba") else estimator.decision_function(xtrain[pred_idx])
    outputs=[]
    for estimator in [base,svc]:
        estimator.fit(xtrain,train.label,sample_weight=train.sample_weight)
        outputs.append([estimator.predict_proba(x)[:,1] if hasattr(estimator,"predict_proba") else estimator.decision_function(x) for x in [xval,xtest]])
    return (np.c_[oof_prob,oof_svc],np.c_[outputs[0][0],outputs[1][0]],np.c_[outputs[0][1],outputs[1][1]],["v1_style_dense_oof_probability","dense_oof_decision"])

def ece(y,p,bins=10):
    cuts=np.linspace(0,1,bins+1); total=0
    for lo,hi in zip(cuts[:-1],cuts[1:]):
        mask=(p>=lo)&(p<(hi if hi<1 else hi+1e-9))
        if mask.any(): total+=mask.mean()*abs(y[mask].mean()-p[mask].mean())
    return float(total)

def classification_metrics(y,pred,score,probability=True):
    out={"precision":precision_score(y,pred,zero_division=0),"recall":recall_score(y,pred,zero_division=0),"f1":f1_score(y,pred,zero_division=0),"pr_auc":average_precision_score(y,score),"roc_auc":roc_auc_score(y,score)}
    if probability: out.update({"log_loss":log_loss(y,score),"brier":brier_score_loss(y,score),"ece":ece(np.asarray(y),np.asarray(score))})
    else: out.update({"log_loss":None,"brier":None,"ece":None})
    return out

def ranking_by_group(frame,score):
    rows=[]
    for term,idx in frame.groupby("term_id",sort=False).groups.items():
        y=frame.loc[idx,"label"].to_numpy(); s=np.asarray(score)[idx]; order=np.argsort(-s); ranked=y[order]
        row={"term_id":term}
        for k in [1,3,5,10]: row[f"ndcg@{k}"]=ndcg_score([y],[s],k=min(k,len(y)))
        positive=np.flatnonzero(ranked==1); row["mrr"]=1/(positive[0]+1) if len(positive) else 0
        for k in [5,10]:
            kk=min(k,len(y)); row[f"precision@{k}"]=ranked[:kk].mean(); row[f"recall@{k}"]=ranked[:kk].sum()/max(y.sum(),1); row[f"map@{k}"]=np.mean([ranked[:i+1].mean() for i in range(kk) if ranked[i]==1]) if ranked[:kk].sum() else 0
        rows.append(row)
    detail=pd.DataFrame(rows); return {c:float(detail[c].mean()) for c in detail if c!="term_id"},detail

def threshold_table(y,p):
    rows=[]
    for threshold in np.linspace(.1,.9,33):
        pred=(p>=threshold).astype(int); rows.append({"threshold":threshold,"precision":precision_score(y,pred,zero_division=0),"recall":recall_score(y,pred,zero_division=0),"f1":f1_score(y,pred,zero_division=0),"predicted_positive_rate":pred.mean()})
    table=pd.DataFrame(rows); best=table.iloc[table.f1.argmax()]
    points=pd.DataFrame([best,table.iloc[(table.recall-.75).abs().argmin()],table.iloc[(table.precision-.80).abs().argmin()],table.iloc[(table.threshold-.5).abs().argmin()]],index=["maximum_f1","recall_focused","precision_focused","balanced_default"]).reset_index(names="operating_point")
    return table,points

def run(mode="ranking-sample"):
    # Training-only native dependency; never import it during UI/test discovery.
    from xgboost import XGBRanker
    ensure_directories(V2_OUT,V2_MODELS,V2_REPORTS); data,sample=load_complete_groups(mode); train,val,test,split=split_groups(data); write_json(V2_REPORTS/"group_split.json",{**sample,**split})
    dense=DenseFeatures().fit(train); xa,names=dense.transform(train); xv,_=dense.transform(val); xt,_=dense.transform(test)
    sa,sv,st,score_names=oof_scores(train,val,test,xa,xv,xt); xtrain=np.c_[xa,sa]; xval=np.c_[xv,sv]; xtest=np.c_[xt,st]; feature_names=names+score_names
    pd.DataFrame({"feature":feature_names}).to_csv(V2_OUT/"feature_dictionary.csv",index=False)
    models={"tuned_logistic":LogisticRegression(C=.5,max_iter=500,solver="liblinear"),"linear_svc":LinearSVC(C=.5),"sgd_log_loss":SGDClassifier(loss="log_loss",alpha=1e-4,max_iter=1000,random_state=RANDOM_SEED),"sgd_modified_huber":SGDClassifier(loss="modified_huber",alpha=1e-4,max_iter=1000,random_state=RANDOM_SEED),"decision_tree":DecisionTreeClassifier(max_depth=8,min_samples_leaf=20,random_state=RANDOM_SEED),"random_forest":RandomForestClassifier(n_estimators=60,max_depth=12,min_samples_leaf=5,n_jobs=1,random_state=RANDOM_SEED),"extra_trees":ExtraTreesClassifier(n_estimators=60,max_depth=14,min_samples_leaf=5,n_jobs=1,random_state=RANDOM_SEED),"hist_gradient_boosting":HistGradientBoostingClassifier(max_iter=60,max_leaf_nodes=31,learning_rate=.08,random_state=RANDOM_SEED)}
    leaderboard=[]; fitted={}; val_scores={}; candidate_dir=V2_MODELS/"candidates"; candidate_dir.mkdir(parents=True,exist_ok=True)
    for name,model in models.items():
        before=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss; started=time.perf_counter(); model.fit(xtrain,train.label,sample_weight=train.sample_weight); train_sec=time.perf_counter()-started
        started=time.perf_counter(); pred=model.predict(xval); latency=(time.perf_counter()-started)*1000/len(val)
        probability=hasattr(model,"predict_proba"); score=model.predict_proba(xval)[:,1] if probability else model.decision_function(xval); artifact=candidate_dir/f"classifier_{name}.pkl"; joblib.dump(model,artifact); row={"model":name,**classification_metrics(val.label,pred,score,probability),"latency_ms_per_row":latency,"train_seconds":train_sec,"peak_memory_mb":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024/1024,"artifact_size_bytes":artifact.stat().st_size,"status":"challenger"}; leaderboard.append(row); fitted[name]=model; val_scores[name]=score
    board=pd.DataFrame(leaderboard).sort_values("f1",ascending=False); board.to_csv(V2_OUT/"classification_leaderboard.csv",index=False); best_name=board.iloc[0].model; best=fitted[best_name]
    if hasattr(best,"feature_importances_"):
        pd.DataFrame({"feature":feature_names,"importance":best.feature_importances_}).sort_values("importance",ascending=False).to_csv(V2_OUT/"tree_feature_importance.csv",index=False)
    probability=hasattr(best,"predict_proba"); test_score=best.predict_proba(xtest)[:,1] if probability else best.decision_function(xtest); test_pred=best.predict(xtest); test_metrics=classification_metrics(test.label,test_pred,test_score,probability)
    joblib.dump(best,V2_MODELS/"classification_challenger.pkl"); write_json(V2_MODELS/"classification_challenger_metadata.json",{"model":best_name,"feature_names":feature_names,"input_contract":"precomputed dense V2 features including group-safe first-stage scores"})
    threshold,points=threshold_table(val.label,val_scores[best_name] if probability else 1/(1+np.exp(-val_scores[best_name]))); threshold.to_csv(V2_OUT/"threshold_analysis.csv",index=False); points.to_csv(V2_OUT/"operating_points.csv",index=False)
    # Calibrate LinearSVC exclusively inside training folds.
    raw_svc=LinearSVC(C=.5).fit(xtrain,train.label,sample_weight=train.sample_weight); raw_score=raw_svc.decision_function(xval); cal=[{"method":"uncalibrated","precision":precision_score(val.label,raw_score>=0,zero_division=0),"recall":recall_score(val.label,raw_score>=0,zero_division=0),"f1":f1_score(val.label,raw_score>=0,zero_division=0),"pr_auc":average_precision_score(val.label,raw_score),"roc_auc":roc_auc_score(val.label,raw_score),"log_loss":None,"brier":None,"ece":None}]
    for method in ["sigmoid","isotonic"]:
        model=CalibratedClassifierCV(LinearSVC(C=.5),method=method,cv=3,n_jobs=1).fit(xtrain,train.label,sample_weight=train.sample_weight); p=model.predict_proba(xval)[:,1]; cal.append({"method":method,**classification_metrics(val.label,(p>=.5).astype(int),p,True)})
    pd.DataFrame(cal).to_csv(V2_OUT/"calibration_results.csv",index=False)
    # Ranking candidates; qid must be nondecreasing.
    def sorted_group(frame,x):
        order=np.argsort(frame.term_id.astype(str).to_numpy(),kind="stable"); sorted_frame=frame.iloc[order].reset_index(drop=True); codes=pd.factorize(sorted_frame.term_id,sort=False)[0]; return sorted_frame,x[order],codes
    tr,xtr,qtr=sorted_group(train,xtrain); va,xva,qva=sorted_group(val,xval); te,xte,qte=sorted_group(test,xtest)
    rank_rows=[]; rank_models={}
    rank_specs=[("rank_ndcg_mean","rank:ndcg",{"lambdarank_pair_method":"mean","lambdarank_num_pair_per_sample":4}),("rank_ndcg_topk","rank:ndcg",{"lambdarank_pair_method":"topk","lambdarank_num_pair_per_sample":4}),("rank_map","rank:map",{}),("rank_pairwise","rank:pairwise",{})]
    for name,objective,extra in rank_specs:
        model=XGBRanker(objective=objective,n_estimators=60,max_depth=5,learning_rate=.08,min_child_weight=2,subsample=.85,colsample_bytree=.9,n_jobs=2,random_state=RANDOM_SEED,**extra)
        started=time.perf_counter(); model.fit(xtr,tr.label,qid=qtr); train_sec=time.perf_counter()-started; started=time.perf_counter(); score=model.predict(xva); latency=(time.perf_counter()-started)*1000/len(va); metrics,_=ranking_by_group(va,score); artifact=candidate_dir/f"ranker_{name}.pkl"; joblib.dump(model,artifact); rank_rows.append({"model":name,**metrics,"train_seconds":train_sec,"latency_ms_per_row":latency,"artifact_size_bytes":artifact.stat().st_size,"sample_weight_used":False}); rank_models[name]=model
    rank_board=pd.DataFrame(rank_rows).sort_values("ndcg@10",ascending=False); rank_board.to_csv(V2_OUT/"ranking_leaderboard.csv",index=False); rank_name=rank_board.iloc[0].model; ranker=rank_models[rank_name]; test_rank_score=ranker.predict(xte); rank_test,rank_detail=ranking_by_group(te,test_rank_score); baseline_rank,baseline_detail=ranking_by_group(te,st[:,0][np.argsort(test.term_id.astype(str).to_numpy(),kind="stable")]); joblib.dump(ranker,V2_MODELS/"search_ranker.pkl")
    # Hard-negative weighting on dense logistic.
    hard=(train.label.eq(0)&(xa[:,names.index("jaccard")]>=.2)); hard_rows=[]
    for label,weight in [("original",train.sample_weight.to_numpy()),("weighted_hard_negative",train.sample_weight.to_numpy()*np.where(hard,2,1))]:
        model=LogisticRegression(C=.5,max_iter=500,solver="liblinear").fit(xtrain,train.label,sample_weight=weight); p=model.predict_proba(xval)[:,1]; hard_rows.append({"experiment":label,"hard_negative_rows":int(hard.sum()),**classification_metrics(val.label,(p>=.5).astype(int),p,True)})
    enriched_x=np.r_[xtrain,xtrain[hard]]; enriched_y=np.r_[train.label.to_numpy(),train.label.to_numpy()[hard]]; enriched_w=np.r_[train.sample_weight.to_numpy(),train.sample_weight.to_numpy()[hard]]; enriched=LogisticRegression(C=.5,max_iter=500,solver="liblinear").fit(enriched_x,enriched_y,sample_weight=enriched_w); p=enriched.predict_proba(xval)[:,1]; hard_rows.append({"experiment":"enriched_hard_negative","hard_negative_rows":int(hard.sum()),**classification_metrics(val.label,(p>=.5).astype(int),p,True)})
    pd.DataFrame(hard_rows).to_csv(V2_OUT/"hard_negative_experiments.csv",index=False)
    # Query bootstrap for ranking delta.
    merged=rank_detail.merge(baseline_detail,on="term_id",suffixes=("_challenger","_baseline")); deltas=merged["ndcg@10_challenger"]-merged["ndcg@10_baseline"]; rng=np.random.default_rng(RANDOM_SEED); boot=[rng.choice(deltas.to_numpy(),len(deltas),replace=True).mean() for _ in range(1000)]
    statistical={"ndcg10_delta":float(deltas.mean()),"bootstrap_ci95":[float(np.percentile(boot,2.5)),float(np.percentile(boot,97.5))],"improved_groups":int((deltas>1e-12).sum()),"unchanged_groups":int((abs(deltas)<=1e-12).sum()),"worsened_groups":int((deltas< -1e-12).sum())}
    # Persist a bounded evaluation playground with both first-stage and final scores.
    playground=te[["term_id","item_id","query","title","category","brand","label"]].copy(); playground["first_stage_score"]=st[:,0][np.argsort(test.term_id.astype(str).to_numpy(),kind="stable")]; playground["final_ranking_score"]=test_rank_score; playground["rank_before"]=playground.groupby("term_id").first_stage_score.rank(ascending=False,method="first").astype(int); playground["rank_after"]=playground.groupby("term_id").final_ranking_score.rank(ascending=False,method="first").astype(int); playground.head(20_000).to_csv(V2_OUT/"ranking_playground.csv",index=False)
    metadata={"mode":mode,"sample":sample,"split":split,"classification_validation_champion":best_name,"classification_holdout":test_metrics,"ranking_champion":rank_name,"ranking_holdout":rank_test,"first_stage_holdout":baseline_rank,"statistical":statistical,"v1_unchanged":True,"python":platform.python_version()}; write_json(V2_OUT/"v2_results.json",metadata); write_json(V2_MODELS/"v2_metadata.json",metadata)
    return metadata

if __name__=="__main__":
    parser=argparse.ArgumentParser(); parser.add_argument("--mode",choices=["ranking-smoke","ranking-sample","ranking-full"],default="ranking-sample"); args=parser.parse_args(); print(json.dumps(run(args.mode),indent=2,default=str))
