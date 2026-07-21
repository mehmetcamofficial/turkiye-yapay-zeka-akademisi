"""Explicit V3 catalogue and judgment contracts."""
from __future__ import annotations
import hashlib,json
import pandas as pd
from .text_normalization import build_searchable_text,normalize_retrieval_text

CATALOGUE_COLUMNS=["item_id","title","category","brand","gender","age_group","attributes"]

def prepare_catalogue(frame:pd.DataFrame,variant="enriched_product_text"):
    data=frame.copy(); data=data.dropna(subset=["item_id"]).drop_duplicates("item_id",keep="first")
    for c in CATALOGUE_COLUMNS:data[c]=data[c].fillna("").astype(str)
    data["normalized_title"]=data.title.map(normalize_retrieval_text); data["searchable_text"]=data.apply(lambda r:build_searchable_text(r,variant),axis=1)
    data["title_missing"]=data.normalized_title.eq(""); data["brand_missing"]=data.brand.str.strip().eq(""); data["category_missing"]=data.category.str.strip().eq("")
    data=data[data.searchable_text.ne("")].sort_values("item_id",kind="stable").reset_index(drop=True); assert data.item_id.is_unique and data.item_id.notna().all(); return data

def validate_judgments(frame,catalogue_ids):
    required={"term_id","query","item_id","relevance_label"}; assert required.issubset(frame)
    assert not frame.duplicated(["term_id","item_id"]).any(); positive=frame[frame.relevance_label.eq(1)]; return {"rows":len(frame),"groups":frame.term_id.nunique(),"positive_rows":len(positive),"relevant_item_coverage":float(positive.item_id.isin(catalogue_ids).mean()) if len(positive) else 0.0}

def fingerprint(frame,columns=("item_id","searchable_text")):
    digest=hashlib.sha256();
    for row in frame[list(columns)].itertuples(index=False,name=None):digest.update(json.dumps(row,ensure_ascii=False).encode())
    return digest.hexdigest()
