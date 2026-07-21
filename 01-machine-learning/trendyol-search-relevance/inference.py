"""Stable single, batch and bounded-catalogue inference API."""
from __future__ import annotations
import json
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from config import FEATURE_COLUMNS,ITEMS_PATH,MODELS_DIR,OUTPUTS_DIR
from feature_engineering import similarity_features

REQUIRED=["query","title"]

def load_artifacts():
    model=joblib.load(MODELS_DIR/"trendyol_relevance_pipeline.pkl")
    metadata=json.loads((MODELS_DIR/"model_metadata.json").read_text(encoding="utf-8"))
    return model,metadata

def prepare_frame(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty: raise ValueError("En az bir kayıt gereklidir.")
    missing=[column for column in REQUIRED if column not in frame]
    if missing: raise ValueError("Eksik sütunlar: "+", ".join(missing))
    result=frame.copy()
    for column in FEATURE_COLUMNS:
        if column not in result: result[column]=""
        result[column]=result[column].fillna("").astype(str)
    if result["query"].str.strip().eq("").any() or result["title"].str.strip().eq("").any(): raise ValueError("Query ve title boş olamaz.")
    return result[FEATURE_COLUMNS]

def predict_frame(frame: pd.DataFrame,model=None,metadata=None,max_rows: int=10_000) -> pd.DataFrame:
    if len(frame)>max_rows: raise ValueError(f"En fazla {max_rows} kayıt işlenebilir.")
    if model is None or metadata is None: model,metadata=load_artifacts()
    prepared=prepare_frame(frame); prediction=model.predict(prepared)
    if hasattr(model,"predict_proba"): score=model.predict_proba(prepared)[:,1]; score_type="probability"
    elif hasattr(model,"decision_function"): score=model.decision_function(prepared); score_type="decision_score"
    else: score=prediction.astype(float); score_type="prediction"
    result=frame.copy(); result["prediction"]=prediction; result["relevance_status"]=pd.Series(prediction).map({0:"Alakasız",1:"Alakalı"}).to_numpy(); result["score"]=score; result["score_type"]=score_type; result["model_version"]=metadata["version"]
    return result

def predict_relevance(query: str,title: str,category: str="",brand: str="",gender: str="",age_group: str="",attributes: str="",model=None,metadata=None) -> dict:
    source=pd.DataFrame([{ "query":query,"title":title,"category":category,"brand":brand,"gender":gender,"age_group":age_group,"attributes":attributes}])
    result=predict_frame(source,model,metadata).iloc[0]; explicit,names=similarity_features(source)
    signals={name:float(value) for name,value in zip(names,explicit[0]) if name in {"exact_match","query_in_title","jaccard","query_coverage","brand_mention","category_overlap"}}
    return {"predicted_label":int(result.prediction),"relevance_status":result.relevance_status,"score":float(result.score),"score_type":result.score_type,"model_version":result.model_version,"key_matching_signals":signals}

def create_catalogue_sample(rows: int=5_000) -> Path:
    OUTPUTS_DIR.mkdir(parents=True,exist_ok=True); destination=OUTPUTS_DIR/"catalogue_sample.csv"
    frame=pd.read_csv(ITEMS_PATH,usecols=["item_id","title","category","brand","gender","age_group","attributes"],nrows=rows,encoding="utf-8-sig")
    text_columns=frame.select_dtypes(include="object").columns
    frame[text_columns]=frame[text_columns].apply(lambda column: column.fillna("").astype(str).str.replace(r"\s+"," ",regex=True).str.strip())
    frame.to_csv(destination,index=False); return destination

def rank_catalogue(query: str,category: str="",top_k: int=10,model=None,metadata=None) -> pd.DataFrame:
    path=OUTPUTS_DIR/"catalogue_sample.csv"
    if not path.is_file(): create_catalogue_sample()
    candidates=pd.read_csv(path).fillna("")
    if category: candidates=candidates[candidates.category.astype(str)==category]
    candidates=candidates.head(5_000).copy(); candidates["query"]=query
    result=predict_frame(candidates,model,metadata,max_rows=5_000).sort_values("score",ascending=False).head(top_k).reset_index(drop=True)
    result.insert(0,"rank",np.arange(1,len(result)+1)); return result

if __name__=="__main__":
    print(predict_relevance("kablosuz kulaklık","Bluetooth kablosuz kulaklık"))
