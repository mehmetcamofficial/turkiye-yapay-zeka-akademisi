"""Dataset discovery, safe extraction and one-time inventory generation."""

from __future__ import annotations

import csv
import hashlib
import json
import zipfile
from pathlib import Path

import pandas as pd

SUPPORTED = {".csv", ".parquet", ".xlsx", ".json", ".zip"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def extract_archives(data_dir: Path) -> list[str]:
    """Extract ZIP members once to data/trendyol, preventing path traversal."""
    extracted = []
    destination = data_dir / "trendyol"
    for archive_path in sorted(data_dir.rglob("*.zip")):
        if destination.is_relative_to(archive_path.parent) and archive_path.parent == destination:
            continue
        destination.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(archive_path) as archive:
            for member in archive.infolist():
                target = (destination / member.filename).resolve()
                if not target.is_relative_to(destination.resolve()):
                    raise ValueError(f"Güvensiz ZIP üyesi: {member.filename}")
                if member.is_dir() or target.exists():
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(member) as source, target.open("wb") as output:
                    while chunk := source.read(4 * 1024 * 1024):
                        output.write(chunk)
                extracted.append(str(target.relative_to(data_dir)))
    return extracted


def _csv_metadata(path: Path) -> tuple[bool, int | None, list[str], str | None]:
    encoding = None
    columns: list[str] = []
    for candidate in ["utf-8-sig", "utf-8", "latin-1"]:
        try:
            with path.open("r", encoding=candidate, newline="") as handle:
                sample = handle.read(65536)
                delimiter = csv.Sniffer().sniff(sample, delimiters=",;\t|").delimiter
            columns = list(pd.read_csv(path, nrows=0, encoding=candidate, sep=delimiter).columns.astype(str))
            encoding = candidate
            break
        except (UnicodeError, csv.Error, pd.errors.ParserError):
            continue
    if not columns or encoding is None:
        return False, None, [], encoding
    row_count = 0
    try:
        for chunk in pd.read_csv(path, usecols=[columns[0]], chunksize=250_000, encoding=encoding, sep=delimiter):
            row_count += len(chunk)
        return True, row_count, columns, encoding
    except (OSError, UnicodeError, pd.errors.ParserError, ValueError):
        return True, None, columns, encoding


def inspect_file(path: Path, root: Path) -> dict:
    record = {"relative_path":str(path.relative_to(root)), "extension":path.suffix.lower(),
              "size_bytes":path.stat().st_size, "sha256":sha256(path), "readable":False,
              "row_count":None, "column_count":None, "columns":[], "encoding":None}
    try:
        if path.suffix.lower() == ".csv":
            readable, rows, columns, encoding = _csv_metadata(path)
            record.update(readable=readable, row_count=rows, column_count=len(columns), columns=columns, encoding=encoding)
        elif path.suffix.lower() == ".parquet":
            import pyarrow.parquet as pq
            metadata = pq.ParquetFile(path).metadata
            columns = pq.ParquetFile(path).schema_arrow.names
            record.update(readable=True, row_count=metadata.num_rows, column_count=len(columns), columns=columns)
        elif path.suffix.lower() == ".xlsx":
            frame = pd.read_excel(path, nrows=0); columns=list(frame.columns.astype(str))
            record.update(readable=True, column_count=len(columns), columns=columns)
        elif path.suffix.lower() == ".json":
            with path.open(encoding="utf-8") as handle: json.load(handle)
            record.update(readable=True, encoding="utf-8")
        elif path.suffix.lower() == ".zip":
            with zipfile.ZipFile(path) as archive: archive.testzip()
            record.update(readable=True)
    except Exception:
        record["readable"] = False
    return record


def build_inventory(data_dir: Path, output_path: Path) -> list[dict]:
    """Build and persist an expensive inventory explicitly, never at import."""
    records = [inspect_file(path, data_dir) for path in sorted(data_dir.rglob("*"))
               if path.is_file() and path.suffix.lower() in SUPPORTED]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    return records
