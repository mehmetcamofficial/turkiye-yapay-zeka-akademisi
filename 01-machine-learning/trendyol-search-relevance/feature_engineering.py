"""Turkish-aware text normalization and sparse relevance features."""
from __future__ import annotations
import re
import numpy as np
import pandas as pd
from scipy import sparse
from sklearn.base import BaseEstimator,TransformerMixin
from sklearn.feature_extraction.text import TfidfVectorizer

FIELDS=["query","title","category","brand","gender","age_group","attributes"]

def normalize_text(value) -> str:
    if value is None or (isinstance(value,float) and np.isnan(value)): return ""
    text=str(value).translate(str.maketrans({"İ":"i","I":"ı"})).lower().strip()
    text=re.sub(r"[/|>\\]+"," ",text)
    return re.sub(r"\s+"," ",text)

def normalized_frame(frame: pd.DataFrame) -> pd.DataFrame:
    result=pd.DataFrame(index=frame.index)
    for field in FIELDS: result[field+"_text"]=frame.get(field,pd.Series("",index=frame.index)).map(normalize_text)
    result["product_document"]=(result["title_text"]+" "+result["category_text"]+" "+result["brand_text"]+" "+result["attributes_text"]).str.strip()
    result["pair_document"]=(result["query_text"]+" [ürün] "+result["product_document"]).str.strip()
    return result

def similarity_features(frame: pd.DataFrame) -> tuple[np.ndarray,list[str]]:
    norm=normalized_frame(frame); rows=[]
    names=["exact_match","query_in_title","title_in_query","query_words","title_words","length_difference","intersection","union","jaccard","query_coverage","title_coverage","brand_mention","category_overlap","char_length_ratio","attributes_overlap"]
    for _,r in norm.iterrows():
        q,t=r.query_text,r.title_text; qs=set(q.split()); ts=set(t.split()); cs=set(r.category_text.split()); ats=set(r.attributes_text.split())
        inter=len(qs&ts); union=len(qs|ts); qn=len(qs); tn=len(ts)
        rows.append([q==t and bool(q),bool(q and q in t),bool(t and t in q),qn,tn,abs(qn-tn),inter,union,inter/union if union else 0,
                     inter/qn if qn else 0,inter/tn if tn else 0,bool(r.brand_text and r.brand_text in q),len(qs&cs),min(len(q),len(t))/max(len(q),len(t)) if q and t else 0,len(qs&ats)])
    return np.asarray(rows,dtype=np.float64),names

class RelevanceFeatureTransformer(BaseEstimator,TransformerMixin):
    def __init__(self,feature_set="combined"):
        self.feature_set=feature_set
        self.query_vectorizer=TfidfVectorizer(ngram_range=(1,2),min_df=2,max_features=12_000,sublinear_tf=True)
        self.product_vectorizer=TfidfVectorizer(ngram_range=(1,2),min_df=2,max_features=30_000,sublinear_tf=True)
        self.pair_vectorizer=TfidfVectorizer(ngram_range=(1,2),min_df=2,max_features=30_000,sublinear_tf=True)
        self.char_vectorizer=TfidfVectorizer(analyzer="char_wb",ngram_range=(3,5),min_df=2,max_features=20_000,sublinear_tf=True)
    def fit(self,X,y=None):
        n=normalized_frame(X)
        if self.feature_set in {"word","combined"}:
            self.query_vectorizer.fit(n.query_text); self.product_vectorizer.fit(n.product_document); self.pair_vectorizer.fit(n.pair_document)
        if self.feature_set in {"char","combined"}: self.char_vectorizer.fit(n.pair_document)
        return self
    def transform(self,X):
        n=normalized_frame(X); parts=[]
        if self.feature_set in {"word","combined"}:
            parts += [self.query_vectorizer.transform(n.query_text),self.product_vectorizer.transform(n.product_document),self.pair_vectorizer.transform(n.pair_document)]
        if self.feature_set in {"char","combined"}: parts.append(self.char_vectorizer.transform(n.pair_document))
        explicit,_=similarity_features(X); parts.append(sparse.csr_matrix(explicit))
        return sparse.hstack(parts,format="csr")
