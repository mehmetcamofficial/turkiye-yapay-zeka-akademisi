"""Configuration for the Trendyol relevance baseline."""
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent
REPOSITORY_ROOT = PROJECT_DIR.parents[1]
DATA_PATH = REPOSITORY_ROOT / "02-data-science/midterm-assignment/data/train_with_negatives.parquet"
ITEMS_PATH = REPOSITORY_ROOT / "02-data-science/midterm-assignment/data/items.csv"
MODELS_DIR = PROJECT_DIR / "models"
OUTPUTS_DIR = PROJECT_DIR / "outputs"
REPORTS_DIR = PROJECT_DIR / "reports"
RANDOM_SEED = 42
MODE_ROWS = {"smoke": 5_000, "sample": 100_000, "full": None}
FEATURE_COLUMNS = ["query", "title", "category", "brand", "gender", "age_group", "attributes"]
LOAD_COLUMNS = ["id", "term_id", "item_id", "label", *FEATURE_COLUMNS, "sample_weight"]
VERSION = "1.0.0"
