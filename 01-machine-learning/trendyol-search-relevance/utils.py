"""Small deterministic IO helpers."""
from __future__ import annotations
import json
from pathlib import Path
from typing import Any

def ensure_directories(*paths: Path) -> None:
    for path in paths: path.mkdir(parents=True, exist_ok=True)

def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

def relative_to_repo(path: Path, repository_root: Path) -> str:
    return path.resolve().relative_to(repository_root.resolve()).as_posix()
