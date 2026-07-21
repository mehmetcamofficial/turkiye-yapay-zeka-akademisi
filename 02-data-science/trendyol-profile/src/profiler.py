"""Deterministic, bounded-memory table profiling."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

MAX_SAMPLE_ROWS = 20_000


def sample_table(path: Path, max_rows: int = MAX_SAMPLE_ROWS) -> tuple[pd.DataFrame, str]:
    """Read a deterministic head sample and label it explicitly as sampled."""
    if path.suffix.lower() == ".csv":
        return pd.read_csv(path, nrows=max_rows), f"sampled_first_{max_rows}_rows"
    if path.suffix.lower() == ".parquet":
        import pyarrow.parquet as pq
        table = pq.ParquetFile(path).read_row_group(0).slice(0, max_rows)
        return table.to_pandas(), f"sampled_first_{min(max_rows, table.num_rows)}_rows"
    raise ValueError(f"Desteklenmeyen profil formatı: {path.suffix}")


def profile_frame(frame: pd.DataFrame, table_name: str, scope: str) -> dict[str, pd.DataFrame]:
    missing = pd.DataFrame({"table":table_name, "column":frame.columns,
        "missing_count_sample":frame.isna().sum().values, "missing_percentage_sample":frame.isna().mean().mul(100).values,
        "metric_scope":scope})
    types = pd.DataFrame({"table":table_name, "column":frame.columns, "dtype":frame.dtypes.astype(str).values, "metric_scope":scope})
    cardinality = pd.DataFrame({"table":table_name, "column":frame.columns,
        "unique_count_sample":[frame[c].nunique(dropna=True) for c in frame], "metric_scope":scope})
    numeric = frame.select_dtypes(include=np.number).describe().T.reset_index(names="column") if len(frame.select_dtypes(include=np.number).columns) else pd.DataFrame()
    if not numeric.empty: numeric.insert(0,"table",table_name); numeric["metric_scope"]=scope
    categorical_rows=[]; text_rows=[]
    for column in frame.select_dtypes(exclude=np.number):
        series=frame[column].dropna().astype(str)
        for value,count in series.value_counts().head(10).items(): categorical_rows.append({"table":table_name,"column":column,"value":value,"count_sample":count,"metric_scope":scope})
        lengths=series.str.len()
        if len(lengths): text_rows.append({"table":table_name,"column":column,"mean_length_sample":lengths.mean(),"max_length_sample":lengths.max(),"metric_scope":scope})
    return {"missing_values":missing, "data_type_summary":types, "cardinality_summary":cardinality,
            "numeric_summary":numeric, "categorical_summary":pd.DataFrame(categorical_rows),
            "text_length_summary":pd.DataFrame(text_rows)}
