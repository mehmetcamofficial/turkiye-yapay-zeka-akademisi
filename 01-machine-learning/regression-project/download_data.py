"""Download California Housing once and persist a reproducible local CSV.

Run this setup utility only when ``data/california_housing.csv`` is absent.
If California Housing cannot be fetched, sklearn's bundled Diabetes dataset is
saved instead and the fallback is recorded in ``data/dataset_metadata.json``.
Normal model training never downloads data.
"""

from __future__ import annotations

import json
from pathlib import Path

from sklearn.datasets import fetch_california_housing, load_diabetes


BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "data" / "california_housing.csv"
METADATA_PATH = BASE_DIR / "data" / "dataset_metadata.json"


def main() -> None:
    """Create the local dataset without replacing an existing copy."""
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    if DATA_PATH.exists() and METADATA_PATH.exists():
        print(f"Local dataset already exists: {DATA_PATH}")
        return

    try:
        dataset = fetch_california_housing(as_frame=True)
        frame = dataset.frame.rename(columns={"MedHouseVal": "target"})
        metadata = {
            "dataset": "California Housing",
            "source": "https://scikit-learn.org/1.5/datasets/real_world.html#california-housing-dataset",
            "original_repository": "StatLib (derived from 1990 U.S. Census)",
            "license": "No standalone dataset license stated by scikit-learn; research dataset distributed via StatLib. Cite Pace & Barry (1997).",
            "fallback_used": False,
            "rows": int(frame.shape[0]),
            "columns": int(frame.shape[1]),
            "target": "target (median house value, units of USD 100,000)",
        }
    except Exception as error:  # explicit, documented offline fallback
        dataset = load_diabetes(as_frame=True)
        frame = dataset.frame.rename(columns={"target": "target"})
        metadata = {
            "dataset": "Diabetes (documented fallback)",
            "source": "https://scikit-learn.org/1.5/datasets/toy_dataset.html#diabetes-dataset",
            "license": "BSD-3-Clause as distributed with scikit-learn",
            "fallback_used": True,
            "fallback_reason": f"{type(error).__name__}: {error}",
            "rows": int(frame.shape[0]),
            "columns": int(frame.shape[1]),
            "target": "target (quantitative disease progression after one year)",
        }

    frame.to_csv(DATA_PATH, index=False)
    METADATA_PATH.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"Saved {metadata['dataset']}: {DATA_PATH} ({frame.shape})")


if __name__ == "__main__":
    main()
