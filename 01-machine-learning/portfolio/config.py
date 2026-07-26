from pathlib import Path

ML_ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = ML_ROOT.parent
DATA_SCIENCE_ROOT = REPOSITORY_ROOT / "02-data-science"
DATA_SCIENCE_MIDTERM_DIR = DATA_SCIENCE_ROOT / "midterm-assignment"
DATA_SCIENCE_FINAL_DIR = DATA_SCIENCE_ROOT / "final-project"
TRENDYOL_PROFILE_DIR = DATA_SCIENCE_ROOT / "trendyol-profile"
CHURN_DIR = ML_ROOT / "customer-churn-prediction"
REGRESSION_DIR = ML_ROOT / "regression-project"
NLP_DIR = ML_ROOT / "nlp-project"
TRENDYOL_RELEVANCE_DIR = ML_ROOT / "trendyol-search-relevance"
CLUSTERING_DIR = ML_ROOT / "clustering-project"
DEPLOYMENT_DIR = ML_ROOT / "model-deployment"
CHURN_MODEL_PATH = CHURN_DIR / "models" / "churn_model.pkl"
REGRESSION_MODEL_PATH = REGRESSION_DIR / "models" / "regression_model.pkl"
NLP_MODEL_PATH = NLP_DIR / "models" / "nlp_pipeline.pkl"
TRENDYOL_RELEVANCE_MODEL_PATH = TRENDYOL_RELEVANCE_DIR / "models" / "trendyol_relevance_pipeline.pkl"
TEST_METADATA_PATH = ML_ROOT / "test_metadata.json"
PORTFOLIO_VERSION = "1.0.0"

NAVIGATION_GROUPS = {
    "section_overview": ["nav_overview"],
    "section_search": [
        "nav_search_intelligence",
        "nav_relevance_classification",
        "nav_hybrid_retrieval",
        "nav_cross_encoder",
        "nav_policy_comparison",
        "nav_live_inference",
        "nav_runtime_diagnostics",
        "nav_model_governance",
    ],
    "section_ml": ["nav_churn", "nav_housing", "nav_sentiment"],
    "section_data_science": [
        "nav_data_workspace",
        "nav_data_science_midterm",
        "nav_data_science_final",
    ],
    "section_model_ops": ["nav_registry", "nav_artifact_health", "nav_deployment", "nav_enterprise_readiness"],
    "section_portfolio": ["nav_projects", "nav_docs", "nav_about", "nav_notebook_status"],
}

ALL_NAV_PAGES = [p for pages in NAVIGATION_GROUPS.values() for p in pages]
