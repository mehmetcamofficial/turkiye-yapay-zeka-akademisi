"""Cached, failure-tolerant artifact loaders."""

from pathlib import Path
from typing import Any
from dataclasses import dataclass
import logging
import sys

import joblib
import pandas as pd
import streamlit as st

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class ModelLoadResult:
    """Structured model-loader result safe for public UI consumption."""

    model: Any | None
    ok: bool
    supports_predict: bool
    supports_predict_proba: bool
    error_code: str | None = None

    @property
    def public_message(self) -> str:
        messages = {
            "missing": "Model artifact’ı doğrulanamadı.",
            "invalid": "Model artifact’ı geçerli bir tahmin pipeline’ı değil.",
            "load_error": "Model yüklenemedi. Uygulamayı proje sanal ortamıyla başlatın.",
        }
        return messages.get(self.error_code, "Model kullanıma hazır.")


@st.cache_data(show_spinner=False)
def load_csv_safe(path: str) -> pd.DataFrame:
    try:
        file_path = Path(path)
        return pd.read_csv(file_path) if file_path.is_file() else pd.DataFrame()
    except (OSError, UnicodeError, pd.errors.ParserError):
        return pd.DataFrame()


@st.cache_data(show_spinner=False)
def load_json_safe(path: str) -> dict[str, Any]:
    import json
    try:
        file_path = Path(path)
        return json.loads(file_path.read_text(encoding="utf-8")) if file_path.is_file() else {}
    except (OSError, UnicodeError, json.JSONDecodeError):
        return {}


@st.cache_data(show_spinner=False)
def load_text_safe(path: str) -> str:
    try:
        file_path = Path(path)
        return file_path.read_text(encoding="utf-8") if file_path.is_file() else ""
    except (OSError, UnicodeError):
        return ""


@st.cache_resource(show_spinner=False)
def load_model_safe(path: Path) -> ModelLoadResult:
    """Load and validate a model without exposing filesystem details in UI."""
    try:
        if not path.exists() or not path.is_file():
            LOGGER.error("Model artifact missing or not a file: %s", path)
            return ModelLoadResult(None, False, False, False, "missing")
        project_root = path.parent.parent
        add_project_root = (project_root / "feature_engineering.py").is_file() and str(project_root) not in sys.path
        if add_project_root:
            sys.path.insert(0, str(project_root))
        try:
            model = joblib.load(path)
        finally:
            if add_project_root and str(project_root) in sys.path:
                sys.path.remove(str(project_root))
        supports_predict = hasattr(model, "predict")
        if not supports_predict:
            LOGGER.error("Loaded object has no predict method: %s", path)
            return ModelLoadResult(None, False, False, False, "invalid")
        return ModelLoadResult(model, True, True, hasattr(model, "predict_proba"))
    except Exception:
        LOGGER.exception("Model loading failed: %s", path)
        return ModelLoadResult(None, False, False, False, "load_error")


def load_image_path_safe(path: str) -> str | None:
    file_path = Path(path)
    return str(file_path) if file_path.is_file() else None


@st.cache_data(show_spinner=False)
def get_trendyol_test_results() -> dict[str, int]:
    import re
    import subprocess
    from portfolio.config import TRENDYOL_RELEVANCE_DIR
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/", "--tb=no", "-q"],
            capture_output=True, text=True, timeout=120,
            cwd=str(TRENDYOL_RELEVANCE_DIR),
        )
        stdout = result.stdout + result.stderr
        passed = len(re.findall(r'^\.', stdout, re.MULTILINE))
        m_failed = re.search(r'(\d+)\s+failed', stdout)
        m_passed = re.search(r'(\d+)\s+passed', stdout)
        failed = int(m_failed.group(1)) if m_failed else 0
        total = int(m_passed.group(1)) + failed if m_passed else passed
        return {"passed": int(m_passed.group(1)) if m_passed else passed, "failed": failed, "total": total}
    except Exception:
        return {"passed": 0, "failed": 0, "total": 0}
