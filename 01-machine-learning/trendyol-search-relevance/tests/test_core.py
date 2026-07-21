"""Lightweight assertions runnable without pytest-specific fixtures."""
import pandas as pd
from feature_engineering import normalize_text,similarity_features
from validation import make_split

def test_normalization():
    assert normalize_text("  İPHONE  15/PRO  ")=="iphone 15 pro"
    assert normalize_text(None)==""

def test_features():
    frame=pd.DataFrame([{"query":"samsung s24","title":"Samsung Galaxy S24","category":"Telefon","brand":None,"attributes":"256 GB"}])
    values,names=similarity_features(frame); assert values.shape==(1,len(names))

def test_group_split():
    frame=pd.DataFrame({"term_id":[1,1,2,2,3,3,4,4,5,5],"item_id":range(10),"label":[0,1]*5})
    train,val,report=make_split(frame,"term_group",42,.4); assert report["term_overlap"]==0
