"""Train focused classical relevance baselines and persist the selected pipeline."""
from __future__ import annotations
import argparse,csv,json,platform,time
from datetime import datetime,timezone
import joblib
import matplotlib.pyplot as plt
import pandas as pd
import sklearn,numpy,scipy
from sklearn.dummy import DummyClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC
from config import *
from data_loader import load_training_data
from evaluate import save_evaluation,score_model
from feature_engineering import RelevanceFeatureTransformer
from utils import ensure_directories,relative_to_repo,write_json
from validation import make_split

def candidates(mode):
    matrix=[
      ("dummy_word","word",DummyClassifier(strategy="prior"),False),
      ("logistic_word","word",LogisticRegression(C=1.0,max_iter=500,solver="liblinear"),True),
      ("linear_svc_char","char",LinearSVC(C=1.0),True),
      ("multinomial_nb_word","word",MultinomialNB(alpha=1.0),True),
      ("logistic_combined","combined",LogisticRegression(C=1.0,max_iter=500,solver="liblinear"),True),
    ]
    return matrix

def run(mode="sample", sample_rows=None):
    ensure_directories(MODELS_DIR,OUTPUTS_DIR,REPORTS_DIR)
    frame,data_meta=load_training_data(mode,max_rows_override=sample_rows); train,val,split=make_split(frame,"term_group",RANDOM_SEED)
    _,_,random_report=make_split(frame,"random_stratified",RANDOM_SEED); _,_,item_report=make_split(frame,"item_group",RANDOM_SEED)
    split["comparison"]={"random_stratified":random_report,"item_group":item_report}; write_json(REPORTS_DIR/"split_report.json",split)
    feature_columns=FEATURE_COLUMNS; experiments=[]; trained={}
    for experiment_id,feature_set,estimator,use_weight in candidates(mode):
        pipeline=Pipeline([("features",RelevanceFeatureTransformer(feature_set)),("model",estimator)])
        started=time.perf_counter(); kwargs={"model__sample_weight":train.sample_weight.to_numpy()} if use_weight else {}
        try:
            pipeline.fit(train[feature_columns],train.label,**kwargs); duration=time.perf_counter()-started
            metrics,_,_,score_type,inference=score_model(pipeline,val[feature_columns],val.label)
            row={"experiment_id":experiment_id,"timestamp":datetime.now(timezone.utc).isoformat(),"data_mode":mode,"row_count":len(frame),"split_type":"term_group","random_seed":RANDOM_SEED,"model":type(estimator).__name__,"feature_set":feature_set,"hyperparameters":json.dumps(estimator.get_params(),default=str,sort_keys=True),"sample_weight_used":use_weight,"train_duration_seconds":duration,"inference_duration_seconds":inference,**metrics,"score_type":score_type,"artifact_path":"","status":"evaluated"}
            experiments.append(row); trained[experiment_id]=pipeline; print(experiment_id,round(metrics["f1"],4),round(metrics["precision"],4),round(metrics["recall"],4),round(duration,2),flush=True)
        except Exception as exc:
            experiments.append({"experiment_id":experiment_id,"timestamp":datetime.now(timezone.utc).isoformat(),"data_mode":mode,"row_count":len(frame),"split_type":"term_group","random_seed":RANDOM_SEED,"model":type(estimator).__name__,"feature_set":feature_set,"hyperparameters":json.dumps(estimator.get_params(),default=str,sort_keys=True),"sample_weight_used":use_weight,"status":"failed","error":type(exc).__name__})
    successful=[r for r in experiments if r["status"]=="evaluated" and r["experiment_id"]!="dummy_word"]
    selected=max(successful,key=lambda r:(r["f1"],r.get("pr_auc") or -1,-r["inference_duration_seconds"])); model=trained[selected["experiment_id"]]
    artifact=MODELS_DIR/"trendyol_relevance_pipeline.pkl"; joblib.dump(model,artifact); selected["artifact_path"]="models/trendyol_relevance_pipeline.pkl"
    metrics,inference=save_evaluation(model,val[feature_columns],val.label,val,OUTPUTS_DIR)
    current=pd.DataFrame(experiments); smoke_path=OUTPUTS_DIR/"experiments_smoke.csv"
    registry=pd.concat([pd.read_csv(smoke_path),current],ignore_index=True) if mode=="sample" and smoke_path.is_file() else current
    registry.to_csv(OUTPUTS_DIR/"experiments.csv",index=False); write_json(OUTPUTS_DIR/"experiments.json",registry.to_dict(orient="records")); registry.to_csv(OUTPUTS_DIR/"model_comparison.csv",index=False)
    plot=pd.DataFrame(successful); plt.figure(); plt.bar(plot.experiment_id,plot.f1); plt.ylabel("Group-term validation F1"); plt.xticks(rotation=25,ha="right"); plt.tight_layout(); plt.savefig(OUTPUTS_DIR/"model_comparison.png",dpi=140); plt.close()
    metadata={"project_name":"Trendyol Search Relevance Intelligence","version":VERSION,"training_date":datetime.now(timezone.utc).isoformat(),"data_mode":mode,"training_rows":len(train),"validation_rows":len(val),"validation_strategy":"GroupShuffleSplit by term_id","feature_set":selected["feature_set"],"model_type":selected["model"],"hyperparameters":json.loads(selected["hyperparameters"]),"primary_metric":"F1","metrics":metrics,"python_version":platform.python_version(),"package_versions":{"numpy":numpy.__version__,"scipy":scipy.__version__,"scikit_learn":sklearn.__version__,"pandas":pd.__version__},"source_dataset":data_meta["source_file"],"source_mtime":data_meta["mtime"],"random_seed":RANDOM_SEED,"sample_strategy":data_meta["sample_strategy"],"known_limitations":["Bounded public Datathon sample","Group split is not perfectly label-stratified","Classical sparse lexical baseline","Not production-scale search"]}
    write_json(MODELS_DIR/"model_metadata.json",metadata); write_json(MODELS_DIR/"feature_metadata.json",{"fields":feature_columns,"feature_set":selected["feature_set"],"explicit_features":["exact match","containment","lengths","token intersection/union","Jaccard","coverage","brand mention","category overlap","character length ratio","attributes overlap"]}); write_json(MODELS_DIR/"label_mapping.json",{"0":"Alakasız","1":"Alakalı"})
    (REPORTS_DIR/"model_selection.md").write_text(f"# Model Seçimi\n\nSeçilen: **{selected['experiment_id']}**. Group-term F1={metrics['f1']:.4f}, precision={metrics['precision']:.4f}, recall={metrics['recall']:.4f}, PR AUC={metrics['pr_auc']:.4f}. Seçim öncelikle F1, ardından PR AUC ve inference süresine dayanır. Accuracy tek başına kullanılmadı.\n",encoding="utf-8")
    return metadata,selected

if __name__=="__main__":
    parser=argparse.ArgumentParser(); parser.add_argument("--mode",choices=["smoke","sample","full"],default="sample"); parser.add_argument("--sample-rows",type=int); args=parser.parse_args(); run(args.mode,args.sample_rows)
