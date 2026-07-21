"""Bounded deterministic access to the large source Parquet."""
from __future__ import annotations
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from config import DATA_PATH, LOAD_COLUMNS, MODE_ROWS, RANDOM_SEED

def validate_source(path=DATA_PATH) -> dict:
    parquet = pq.ParquetFile(path)
    available = parquet.schema.names
    missing = [column for column in LOAD_COLUMNS if column not in available]
    if missing: raise ValueError("Eksik kaynak sütunları: " + ", ".join(missing))
    return {"rows": parquet.metadata.num_rows, "columns": available, "mtime": path.stat().st_mtime, "size_bytes": path.stat().st_size}

def load_training_data(mode: str = "sample", seed: int = RANDOM_SEED, max_rows_override: int | None = None) -> tuple[pd.DataFrame, dict]:
    if mode not in MODE_ROWS: raise ValueError(f"Bilinmeyen veri modu: {mode}")
    source = validate_source(); total = source["rows"]; requested = max_rows_override if max_rows_override is not None else MODE_ROWS[mode]
    if requested is None:
        frame = pd.read_parquet(DATA_PATH, columns=LOAD_COLUMNS)
        strategy = "full_source"
    else:
        count = min(requested, total)
        indices = np.sort(np.random.default_rng(seed).choice(total, size=count, replace=False))
        pieces=[]; offset=0; cursor=0
        parquet=pq.ParquetFile(DATA_PATH)
        for batch in parquet.iter_batches(columns=LOAD_COLUMNS, batch_size=50_000):
            end=offset+batch.num_rows; stop=np.searchsorted(indices,end,side="left")
            local=indices[cursor:stop]-offset
            if len(local): pieces.append(batch.take(local).to_pandas())
            cursor=stop; offset=end
            if cursor==len(indices): break
        frame=pd.concat(pieces,ignore_index=True); strategy="uniform_without_replacement_streamed_indices"
    if frame["label"].isna().any() or not set(frame["label"].unique()).issubset({0,1}): raise ValueError("Geçersiz label")
    if frame["sample_weight"].isna().any() or (frame["sample_weight"] < 0).any(): raise ValueError("Geçersiz sample_weight")
    metadata={**source,"mode":mode,"row_count":len(frame),"random_seed":seed,"sample_strategy":strategy,
              "source_file":"02-data-science/midterm-assignment/data/train_with_negatives.parquet",
              "label_counts":{str(k):int(v) for k,v in frame["label"].value_counts().sort_index().items()}}
    return frame,metadata
