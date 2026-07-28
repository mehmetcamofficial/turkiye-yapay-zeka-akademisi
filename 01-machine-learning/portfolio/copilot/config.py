from __future__ import annotations

from pathlib import Path

_COPILOT_DIR = Path(__file__).resolve().parent
_PORTFOLIO_DIR = _COPILOT_DIR.parent
_ML_ROOT = _PORTFOLIO_DIR.parent
_REPO_ROOT = _ML_ROOT.parent

REPO_ROOT = _REPO_ROOT
ML_ROOT = _ML_ROOT
COPILOT_DIR = _COPILOT_DIR
INDEX_DIR = COPILOT_DIR / "index"
ACCEPTANCE_DIR = ML_ROOT / "acceptance_project_copilot"
GOLDEN_DATASET = ML_ROOT / "evaluation" / "search" / "copilot_golden.json"
PERFORMANCE_JSON = ACCEPTANCE_DIR / "performance_summary.json"
DOCS_DIR = ML_ROOT / "docs" / "project-copilot.md"
MAX_FILE_SIZE = 512 * 1024
MAX_CHUNK_SIZE = 8192
MIN_CHUNK_SIZE = 120
MAX_CITATIONS = 5
MAX_MEMORY_TURNS = 6