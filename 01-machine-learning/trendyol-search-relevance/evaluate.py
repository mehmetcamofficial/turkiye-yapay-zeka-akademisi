"""Evaluation, plots and bounded relevance error analysis."""
from __future__ import annotations
import time
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.metrics import (accuracy_score,average_precision_score,classification_report,confusion_matrix,
                             f1_score,precision_recall_curve,precision_score,recall_score,roc_auc_score,roc_curve)
from feature_engineering import similarity_features
from utils import write_json

def score_model(model,X,y) -> tuple[dict,np.ndarray,np.ndarray,str,float]:
    started=time.perf_counter(); prediction=model.predict(X); inference=time.perf_counter()-started
    if hasattr(model,"predict_proba"): score=model.predict_proba(X)[:,1]; score_type="probability"
    elif hasattr(model,"decision_function"): score=model.decision_function(X); score_type="decision_score"
    else: score=prediction.astype(float); score_type="prediction"
    metrics={"accuracy":accuracy_score(y,prediction),"precision":precision_score(y,prediction,zero_division=0),
             "recall":recall_score(y,prediction,zero_division=0),"f1":f1_score(y,prediction,zero_division=0),
             "support":len(y),"positive_rate":float(np.mean(y)),"pr_auc":None,"roc_auc":None}
    if score_type in {"probability","decision_score"} and len(np.unique(y))==2:
        metrics["pr_auc"]=average_precision_score(y,score); metrics["roc_auc"]=roc_auc_score(y,score)
    return metrics,prediction,score,score_type,inference

def save_evaluation(model,X,y,context,outputs):
    outputs.mkdir(parents=True,exist_ok=True)
    metrics,prediction,score,score_type,inference=score_model(model,X,y)
    pd.DataFrame(classification_report(y,prediction,output_dict=True,zero_division=0)).T.reset_index(names="class").to_csv(outputs/"classification_report.csv",index=False)
    pd.DataFrame(confusion_matrix(y,prediction),index=["actual_0","actual_1"],columns=["predicted_0","predicted_1"]).to_csv(outputs/"confusion_matrix.csv")
    write_json(outputs/"metrics.json",{**metrics,"score_type":score_type,"decision_threshold":.5 if score_type=="probability" else 0.0,"inference_duration_seconds":inference})
    if score_type=="probability":
        thresholds=np.linspace(.1,.9,33); rows=[]
        for threshold in thresholds:
            pred=(score>=threshold).astype(int); rows.append({"threshold":threshold,"precision":precision_score(y,pred,zero_division=0),"recall":recall_score(y,pred,zero_division=0),"f1":f1_score(y,pred,zero_division=0)})
        threshold_frame=pd.DataFrame(rows); threshold_frame.to_csv(outputs/"threshold_analysis.csv",index=False)
        plt.figure(); plt.plot(threshold_frame.threshold,threshold_frame.f1); plt.xlabel("Decision threshold"); plt.ylabel("F1"); plt.tight_layout(); plt.savefig(outputs/"threshold_f1_curve.png",dpi=140); plt.close()
    if score_type in {"probability","decision_score"}:
        precision,recall,_=precision_recall_curve(y,score); plt.figure(); plt.plot(recall,precision); plt.xlabel("Recall"); plt.ylabel("Precision"); plt.tight_layout(); plt.savefig(outputs/"precision_recall_curve.png",dpi=140); plt.close()
        fpr,tpr,_=roc_curve(y,score); plt.figure(); plt.plot(fpr,tpr); plt.plot([0,1],[0,1],linestyle="--"); plt.xlabel("False positive rate"); plt.ylabel("True positive rate"); plt.tight_layout(); plt.savefig(outputs/"roc_curve.png",dpi=140); plt.close()
    matrix=confusion_matrix(y,prediction); plt.figure(); plt.imshow(matrix); plt.xticks([0,1]); plt.yticks([0,1]); plt.xlabel("Predicted"); plt.ylabel("Actual")
    for i in range(2):
        for j in range(2): plt.text(j,i,str(matrix[i,j]),ha="center",va="center")
    plt.tight_layout(); plt.savefig(outputs/"confusion_matrix.png",dpi=140); plt.close()
    save_error_analysis(context,y,prediction,score,score_type,outputs)
    return metrics,inference

def save_error_analysis(context,y,prediction,score,score_type,outputs):
    explicit,names=similarity_features(context); overlap=explicit[:,names.index("jaccard")]
    result=context[["term_id","item_id","query","title","category","brand"]].copy()
    result["true_label"]=np.asarray(y); result["prediction"]=prediction; result["score"]=score; result["score_type"]=score_type; result["lexical_overlap"]=overlap
    result[(result.true_label==0)&(result.prediction==1)].sort_values("score",ascending=False).head(500).to_csv(outputs/"false_positives.csv",index=False)
    result[(result.true_label==1)&(result.prediction==0)].sort_values("score").head(500).to_csv(outputs/"false_negatives.csv",index=False)
    result.assign(hardness=np.abs(result.score-(.5 if score_type=="probability" else 0))).sort_values("hardness").head(500).to_csv(outputs/"hardest_examples.csv",index=False)
    result.groupby("category",dropna=False).apply(lambda g: pd.Series({"rows":len(g),"positive_rate":g.true_label.mean(),"precision":precision_score(g.true_label,g.prediction,zero_division=0),"recall":recall_score(g.true_label,g.prediction,zero_division=0),"f1":f1_score(g.true_label,g.prediction,zero_division=0)}),include_groups=False).reset_index().sort_values("rows",ascending=False).to_csv(outputs/"category_performance.csv",index=False)
    for source,name in [(result["query"].fillna("").str.split().str.len(),"query_length_performance.csv"),(result["title"].fillna("").str.split().str.len(),"title_length_performance.csv"),(pd.cut(result.lexical_overlap,[-.01,.0,.2,.5,1.0]),"lexical_overlap_performance.csv")]:
        temp=result.assign(bucket=source); temp.groupby("bucket",observed=True).apply(lambda g: pd.Series({"rows":len(g),"f1":f1_score(g.true_label,g.prediction,zero_division=0),"precision":precision_score(g.true_label,g.prediction,zero_division=0),"recall":recall_score(g.true_label,g.prediction,zero_division=0)}),include_groups=False).reset_index().to_csv(outputs/name,index=False)
