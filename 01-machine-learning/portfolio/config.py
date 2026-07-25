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
PORTFOLIO_VERSION = "1.0.0"

NAVIGATION_GROUPS = {
    "OVERVIEW / GENEL BAKIŞ": ["Executive Overview"],
    "SEARCH INTELLIGENCE / ARAMA ZEKÂSI": [
        "Search Demo / Arama Demosu",
        "Cross-Encoder Reranking",
        "Evaluation Lab",
        "Architecture / Mimari",
    ],
    "MACHINE LEARNING": [
        "Customer Churn",
        "Housing Regression",
        "Sentiment Intelligence",
    ],
    "DATA & QUALITY / VERİ VE KALİTE": [
        "Trendyol Data Workspace",
    ],
    "MODEL OPERATIONS": [
        "Model Registry",
        "Artifact Health",
        "Deployment Readiness",
    ],
    "PORTFOLIO": [
        "Projects",
        "Documentation",
        "About Mehmet",
    ],
    "ACADEMIC ARCHIVE / AKADEMİK ARŞİV": [
        "Assignments",
        "Notebook Status",
    ],
}

ALL_NAV_PAGES = [p for pages in NAVIGATION_GROUPS.values() for p in pages]
