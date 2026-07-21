"""Bridge to the independent Trendyol relevance inference package."""
from __future__ import annotations
import importlib
import sys
import pandas as pd
import streamlit as st
from portfolio.config import TRENDYOL_RELEVANCE_DIR

@st.cache_resource(show_spinner=False)
def inference_module():
    root=str(TRENDYOL_RELEVANCE_DIR)
    if root not in sys.path: sys.path.insert(0,root)
    return importlib.import_module("inference")

def predict_single(**values):
    return inference_module().predict_relevance(**values)

def predict_batch(frame: pd.DataFrame, max_rows: int=10_000):
    return inference_module().predict_frame(frame,max_rows=max_rows)

def rank_sample(query: str, category: str="", top_k: int=10):
    return inference_module().rank_catalogue(query,category,top_k)
