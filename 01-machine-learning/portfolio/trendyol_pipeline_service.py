"""Single Streamlit boundary for the bounded V4 search pipeline."""
from __future__ import annotations
import sys
import streamlit as st
from portfolio.config import TRENDYOL_RELEVANCE_DIR

@st.cache_resource(show_spinner=False)
def pipeline_runtime():
    root=str(TRENDYOL_RELEVANCE_DIR)
    if root not in sys.path:sys.path.insert(0,root)
    from search_pipeline.orchestrator import SearchPipeline
    return SearchPipeline()

def pipeline_search(**values):
    root=str(TRENDYOL_RELEVANCE_DIR)
    if root not in sys.path:sys.path.insert(0,root)
    from search_pipeline.contracts import SearchRequest
    return pipeline_runtime().search(SearchRequest(**values))
