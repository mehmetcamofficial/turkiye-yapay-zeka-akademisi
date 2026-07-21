"""Actual Trendyol schema and academy-midterm compatibility analysis."""

from __future__ import annotations

import json
from pathlib import Path

REQUIRED = ["indirim_orani", "musteri_puani", "odeme_turu", "musteri_tipi", "siparis_tarihi",
            "sehir", "kategori", "birim_fiyat", "toplam_tutar", "teslimat_gunu"]


def analyze(inventory: list[dict]) -> dict:
    tables = [record for record in inventory if record["extension"] in {".csv", ".parquet", ".xlsx"} and record["readable"]]
    results = []
    for required in REQUIRED:
        matches = []
        for table in tables:
            columns = table.get("columns", [])
            if required in columns:
                matches.append((table["relative_path"], required, "Exact Match", "Yok", "Yüksek"))
            elif required == "kategori" and "category" in columns:
                matches.append((table["relative_path"], "category", "Safe Semantic Match", "Sütun adı Türkçeleştirilebilir; anlam ürün kategorisidir", "Yüksek"))
        if matches:
            source, actual, match_type, transformation, confidence = matches[0]
        else:
            source, actual, match_type, transformation, confidence = "—", "—", "Missing", "Akademi transactional dataset gerekli", "Yüksek"
        results.append({"required_field":required, "source_file":source, "actual_field":actual,
                        "match_type":match_type, "transformation":transformation, "confidence":confidence})
    supported = [1, 2, 3, 4, 5, 9, 11]
    blocked = [6, 7, 8, 10, 12, 13, 14, 15]
    return {"required_fields":results, "schema_compatible":all(row["match_type"] in {"Exact Match", "Safe Semantic Match"} for row in results),
            "supported_questions":supported, "blocked_questions":blocked,
            "conclusion":"Trendyol verisi ürün kataloğu ve arama uygunluğu verisidir; ara ödevin transactional müşteri/sipariş şemasına uyumlu değildir."}


def save_report(report: dict, path: Path) -> None:
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
