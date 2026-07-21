"""Compose saved profile artifacts from bounded samples."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from src.profiler import profile_frame, sample_table
from src.quality import quality_summary
from src.schema import analyze, save_report


def generate_profiles(data_dir: Path, inventory: list[dict], output_dir: Path, max_rows: int = 20_000) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    table_rows=[]; collected={name:[] for name in ["missing_values","data_type_summary","cardinality_summary","numeric_summary","categorical_summary","text_length_summary"]}
    duplicates=[]; quality_reports=[]
    for record in inventory:
        if record["extension"] not in {".csv", ".parquet"} or not record["readable"]:
            continue
        path=data_dir/record["relative_path"]
        frame,scope=sample_table(path,max_rows=max_rows)
        table_rows.append({"table":record["relative_path"],"full_row_count":record["row_count"],"column_count":record["column_count"],"profiled_rows":len(frame),"metric_scope":scope})
        profiles=profile_frame(frame,record["relative_path"],scope)
        for name,value in profiles.items():
            if not value.empty: collected[name].append(value)
        quality,duplicate=quality_summary(frame,record["relative_path"],scope); quality_reports.append(quality); duplicates.append(duplicate)
    pd.DataFrame(table_rows).to_csv(output_dir/"table_summary.csv",index=False)
    for name,frames in collected.items(): pd.concat(frames,ignore_index=True).to_csv(output_dir/f"{name}.csv",index=False) if frames else pd.DataFrame().to_csv(output_dir/f"{name}.csv",index=False)
    pd.concat(duplicates,ignore_index=True).to_csv(output_dir/"duplicate_summary.csv",index=False)
    column_profile=pd.concat([pd.concat(collected["data_type_summary"],ignore_index=True),pd.concat(collected["cardinality_summary"],ignore_index=True).drop(columns=["metric_scope"])],axis=1)
    column_profile.loc[:,~column_profile.columns.duplicated()].to_csv(output_dir/"column_profile.csv",index=False)
    schema_report=analyze(inventory); save_report(schema_report,output_dir/"schema_report.json")
    (output_dir/"data_quality_report.json").write_text(json.dumps(quality_reports,ensure_ascii=False,indent=2),encoding="utf-8")
    (output_dir/"profile_summary.md").write_text(f"# Trendyol Veri Profili\n\n- Tablo: {len(table_rows)}\n- Profil kapsamı: tablo başına en fazla {max_rows} satır\n- Satır sayıları envanterde full-data; kalite/dağılım metrikleri açıkça sampled olarak etiketlidir.\n- Ara ödev şema uyumu: {schema_report['schema_compatible']}\n",encoding="utf-8")
