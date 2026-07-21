"""Sparse TF-IDF and bounded BM25 retrieval implementations."""
from __future__ import annotations
import time
import numpy as np
from sklearn.feature_extraction.text import CountVectorizer,TfidfVectorizer

def top_indices(score,k):
    score=np.asarray(score).ravel(); k=min(k,len(score)); idx=np.argpartition(-score,k-1)[:k] if k else np.array([],dtype=int); return idx[np.lexsort((idx,-score[idx]))]

class TfidfRetriever:
    def __init__(self,analyzer="word",ngram_range=(1,2),max_features=120000):self.vectorizer=TfidfVectorizer(analyzer=analyzer,ngram_range=ngram_range,min_df=2,max_features=max_features,sublinear_tf=True); self.matrix=None
    def fit(self,documents):self.matrix=self.vectorizer.fit_transform(documents); return self
    def search(self,query,k=100):
        score=np.asarray((self.matrix@self.vectorizer.transform([query]).T).toarray()).ravel(); return top_indices(score,k),score
    @property
    def index_bytes(self):return self.matrix.data.nbytes+self.matrix.indices.nbytes+self.matrix.indptr.nbytes

class BM25Retriever:
    def __init__(self,k1=1.5,b=.75,max_features=120000):self.k1=k1;self.b=b;self.vectorizer=CountVectorizer(ngram_range=(1,1),min_df=2,max_features=max_features);self.matrix=None
    def fit(self,documents):
        x=self.vectorizer.fit_transform(documents).astype(np.float32); self.doc_len=np.asarray(x.sum(axis=1)).ravel(); self.avgdl=max(self.doc_len.mean(),1); df=np.asarray((x>0).sum(axis=0)).ravel(); self.idf=np.log(1+(len(documents)-df+.5)/(df+.5)); self.matrix=x.tocsc(); return self
    def search(self,query,k=100):
        q=self.vectorizer.transform([query]); score=np.zeros(self.matrix.shape[0],dtype=np.float32)
        for term in q.indices:
            column=self.matrix.getcol(term).tocoo(); tf=column.data; denom=tf+self.k1*(1-self.b+self.b*self.doc_len[column.row]/self.avgdl); score[column.row]+=self.idf[term]*(tf*(self.k1+1)/denom)
        return top_indices(score,k),score
    @property
    def index_bytes(self):return self.matrix.data.nbytes+self.matrix.indices.nbytes+self.matrix.indptr.nbytes+self.doc_len.nbytes+self.idf.nbytes
