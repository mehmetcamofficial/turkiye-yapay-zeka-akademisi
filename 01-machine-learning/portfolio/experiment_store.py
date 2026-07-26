from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from portfolio.config import ARTIFACTS_DIR, REPOSITORY_ROOT

LOGGER = logging.getLogger(__name__)

EXPERIMENTS_FILE = ARTIFACTS_DIR / "experiments" / "experiments.jsonl"

EXPERIMENT_TYPES = {"training", "evaluation", "hyperparameter_search", "benchmark"}

REQUIRED_FIELDS = [
    "experiment_id",
    "experiment_type",
    "capability",
    "model_name",
    "status",
    "started_at",
    "completed_at",
    "duration_ms",
    "metrics",
    "parameters",
    "artifact_paths",
    "source",
    "notes",
]


def generate_experiment_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S") + "_" + uuid.uuid4().hex[:8]


def safe_json_value(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value)
    if isinstance(value, (np.bool_,)):
        return bool(value)
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, tuple):
        return str(value)
    if isinstance(value, dict):
        return {k: safe_json_value(v) for k, v in value.items()}
    if isinstance(value, list):
        return [safe_json_value(v) for v in value]
    return str(value)


def repository_relative_path(path: str | Path | None) -> str:
    if path is None:
        return ""
    try:
        p = Path(path).resolve()
        return str(p.relative_to(REPOSITORY_ROOT))
    except (ValueError, OSError):
        try:
            p = Path(path)
            return str(p.relative_to(REPOSITORY_ROOT))
        except (ValueError, OSError):
            return Path(path).name


def normalize_experiment(raw: dict[str, Any]) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    started = raw.get("started_at") or now
    completed = raw.get("completed_at") or now

    if isinstance(started, str):
        started = started
    elif isinstance(started, datetime):
        started = started.isoformat()
    else:
        started = now.isoformat()

    if isinstance(completed, str):
        completed = completed
    elif isinstance(completed, datetime):
        completed = completed.isoformat()
    else:
        completed = now.isoformat()

    duration = raw.get("duration_ms", 0)
    if duration is None:
        duration = 0
    duration = int(duration)

    experiment_type = raw.get("experiment_type", "")
    if experiment_type not in EXPERIMENT_TYPES:
        experiment_type = "evaluation"

    model_name = raw.get("model_name", "")
    if isinstance(model_name, (list, tuple)):
        model_name = ", ".join(str(m) for m in model_name)

    metrics = {}
    for k, v in (raw.get("metrics") or {}).items():
        metrics[str(k)] = safe_json_value(v)

    params = {}
    for k, v in (raw.get("parameters") or {}).items():
        params[str(k)] = safe_json_value(v)

    artifact_paths = []
    for p in (raw.get("artifact_paths") or []):
        artifact_paths.append(repository_relative_path(p))

    return {
        "experiment_id": raw.get("experiment_id") or generate_experiment_id(),
        "experiment_type": experiment_type,
        "capability": str(raw.get("capability", "")),
        "model_name": model_name,
        "status": str(raw.get("status", "completed")),
        "started_at": started,
        "completed_at": completed,
        "duration_ms": duration,
        "metrics": metrics,
        "parameters": params,
        "artifact_paths": artifact_paths,
        "source": str(raw.get("source", "")),
        "notes": str(raw.get("notes", "")),
    }


def load_experiments() -> list[dict[str, Any]]:
    if not EXPERIMENTS_FILE.is_file():
        return []
    records: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for line in EXPERIMENTS_FILE.read_text(encoding="utf-8").strip().split("\n"):
        line = line.strip()
        if not line:
            continue
        try:
            record = json.loads(line)
            eid = record.get("experiment_id", "")
            if eid and eid in seen_ids:
                continue
            if eid:
                seen_ids.add(eid)
            records.append(record)
        except (json.JSONDecodeError, ValueError):
            LOGGER.warning("Skipping malformed experiment line: %s", line[:80])
    return records


def append_experiment(record: dict[str, Any]) -> dict[str, Any]:
    normalized = normalize_experiment(record)

    if not normalized["experiment_id"]:
        normalized["experiment_id"] = generate_experiment_id()

    eid = normalized["experiment_id"]

    existing = load_experiments()
    if any(e.get("experiment_id") == eid for e in existing):
        LOGGER.warning("Duplicate experiment_id %s rejected", eid)
        return normalized

    EXPERIMENTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(EXPERIMENTS_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(normalized, ensure_ascii=False) + "\n")

    return normalized


def normalize_gridsearch_results(cv_results: Any) -> pd.DataFrame:
    if cv_results is None:
        return pd.DataFrame()
    try:
        if isinstance(cv_results, pd.DataFrame) and not cv_results.empty:
            df = cv_results.copy()
        elif isinstance(cv_results, dict):
            df = pd.DataFrame(cv_results)
        elif isinstance(cv_results, np.ndarray) and cv_results.ndim == 2:
            df = pd.DataFrame(cv_results)
        else:
            try:
                df = pd.DataFrame(cv_results)
            except (ValueError, TypeError):
                LOGGER.exception("Cannot convert cv_results to DataFrame")
                return pd.DataFrame()

        if df.empty:
            return pd.DataFrame()

        safe_cols = [c for c in df.columns if isinstance(c, str)]

        known_cols = {"mean_test_score", "std_test_score", "rank_test_score"}
        param_cols = sorted(c for c in safe_cols if c.startswith("param_"))
        display_cols = param_cols + [c for c in safe_cols if c in known_cols]

        if not display_cols:
            display_cols = safe_cols

        df = df[display_cols].copy()

        if "rank_test_score" in df.columns:
            df = df.sort_values("rank_test_score").reset_index(drop=True)

        for col in df.columns:
            if col.startswith("param_"):
                df[col] = df[col].apply(safe_json_value)

        return df

    except Exception:
        LOGGER.exception("normalize_gridsearch_results failed")
        return pd.DataFrame()


def record_gridsearch_experiment(
    capability: str,
    model_name: str,
    source_dir: str | Path,
    metrics: dict[str, Any] | None = None,
    params: dict[str, Any] | None = None,
    status: str = "completed",
    notes: str = "",
) -> dict[str, Any] | None:
    """Record a GridSearchCV / evaluation experiment from pre-computed results.
    
    Uses a session-state guard to record at most once per run.
    Returns the experiment dict, or None if already recorded.
    """
    import streamlit as st

    src = str(source_dir)
    guard_key = f"_exp_recorded_{src}"
    if st.session_state.get(guard_key):
        return None
    st.session_state[guard_key] = True

    # Auto-extract best score and params from CSV if available
    auto_metrics = {}
    auto_params = {}
    try:
        csv_path = Path(src)
        if csv_path.is_file():
            df = pd.read_csv(csv_path)
            if not df.empty and "rank_test_score" in df.columns:
                best_row = df.sort_values("rank_test_score").iloc[0]
                # Best score
                if "mean_test_score" in best_row:
                    auto_metrics["best_score"] = float(best_row["mean_test_score"])
                auto_metrics["candidate_count"] = int(len(df))
                # Best params
                for col in df.columns:
                    if col.startswith("param_"):
                        val = best_row[col]
                        auto_params[col.replace("param_", "")] = safe_json_value(val)
    except Exception:
        LOGGER.warning("Could not extract best params from %s", src)

    # Merge with provided
    if metrics:
        auto_metrics.update(metrics)
    if params:
        auto_params.update(params)

    record = {
        "experiment_type": "hyperparameter_search" if "hyperparameter" in src.lower() else "evaluation",
        "capability": capability,
        "model_name": model_name,
        "status": status,
        "started_at": datetime.now(timezone.utc),
        "completed_at": datetime.now(timezone.utc),
        "duration_ms": 0,
        "metrics": auto_metrics,
        "parameters": auto_params,
        "artifact_paths": [],
        "source": repository_relative_path(src),
        "notes": notes,
    }
    return append_experiment(record)
