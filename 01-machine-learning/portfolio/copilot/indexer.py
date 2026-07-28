from __future__ import annotations

import hashlib
import json
import logging
import os
import re
from pathlib import Path
from datetime import datetime, timezone
from typing import Any

from portfolio.copilot.schema import (
    CopilotChunk,
    RepoDocument,
    CopilotConfig,
)
from portfolio.copilot.config import MAX_FILE_SIZE, MAX_CHUNK_SIZE, MIN_CHUNK_SIZE
from portfolio.copilot.fingerprint import build_fingerprint, fingerprint_hash, save_fingerprint, load_fingerprint, fingerprint_matches

LOGGER = logging.getLogger(__name__)

FILE_TYPE_MAP = {
    ".py": "python",
    ".md": "markdown",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".json": "json",
    ".toml": "toml",
    ".txt": "text",
    ".csv": "csv",
    ".rst": "markdown",
    ".cfg": "config",
    ".ini": "config",
    ".ipynb": "notebook",
}

PROJECT_AREA_MAP = {
    "customer-churn-prediction": "churn",
    "regression-project": "housing",
    "nlp-project": "sentiment",
    "trendyol-search-relevance": "search",
    "portfolio": "search",
    "evaluation": "evaluation",
    "docs": "documentation",
    ".github": "repository",
}


def _file_type(path: Path) -> str:
    return FILE_TYPE_MAP.get(path.suffix, "unknown")


def _project_area(path: Path, repo_root: Path) -> str:
    parts = path.relative_to(repo_root).parts
    for part in parts:
        if part in PROJECT_AREA_MAP:
            return PROJECT_AREA_MAP[part]
    if parts and parts[0] == "01-machine-learning":
        if len(parts) > 1:
            return PROJECT_AREA_MAP.get(parts[1], "ml")
        return "ml"
    if parts and parts[0] == "02-data-science":
        return "data-science"
    return "root"


def _compute_hash(content: str, path: str) -> str:
    return hashlib.sha256(f"{path}:{content}".encode()).hexdigest()[:16]


def _last_modified(path: Path) -> str:
    try:
        ts = path.stat().st_mtime
        return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()
    except Exception:
        return ""


def _should_exclude(path: Path, config: CopilotConfig) -> bool:
    name = path.name
    for pattern in config.exclude_patterns:
        if pattern.startswith("*"):
            if name.endswith(pattern[1:]):
                return True
        elif path.match(f"**/{pattern}") or name == pattern:
            return True

    for parent in path.parents:
        if parent.name in config.ignored_directories:
            return True
        if any(part.startswith(".") and part not in (".github",) for part in path.parts):
            if parent != config.repo_root and parent != config.ml_root and "01-machine-learning" not in str(parent):
                return True

    if path.suffix == ".env":
        return True

    if config.max_file_size_bytes > 0:
        try:
            fsize = path.stat().st_size
        except OSError:
            return True
        if fsize > config.max_file_size_bytes:
            return True

    return False


def _chunk_python(content: str, file_path: str, start_line: int) -> list[dict[str, Any]]:
    chunks: list[dict[str, Any]] = []
    current_class: str | None = None
    current_func: str | None = None
    current_lines: list[str] = []
    current_start: int = start_line

    class_re = re.compile(r"^class\s+(\w+)")
    func_re = re.compile(r"^def\s+(\w+)")
    mod_level_re = re.compile(r"^(?:from|import|__|@)\s")

    lines = content.split("\n")

    def _emit_chunk() -> None:
        nonlocal current_lines, current_func, current_class
        if not current_lines:
            return
        text = "\n".join(current_lines)
        chunks.append({
            "text": text,
            "start_line": current_start,
            "end_line": current_start + len(current_lines) - 1,
            "symbol": current_func or current_class,
        })
        current_lines = []
        current_func = None
        current_class = None

    for i, line in enumerate(lines):
        abs_line = start_line + i
        stripped = line.strip()

        if class_re.match(stripped):
            if current_lines and len("\n".join(current_lines)) >= MIN_CHUNK_SIZE:
                _emit_chunk()
            current_class = class_re.match(stripped).group(1)
            current_func = None
            current_lines = [line]
            current_start = abs_line
        elif func_re.match(stripped):
            if current_lines and len("\n".join(current_lines)) >= MIN_CHUNK_SIZE:
                _emit_chunk()
            current_func = func_re.match(stripped).group(1)
            current_class = None
            current_lines = [line]
            current_start = abs_line
        elif mod_level_re.match(stripped) or stripped == "":
            current_lines.append(line)
        else:
            current_lines.append(line)

    if current_lines and len("\n".join(current_lines)) >= MIN_CHUNK_SIZE:
        _emit_chunk()

    if not chunks and content.strip():
        chunks.append({
            "text": content,
            "start_line": start_line,
            "end_line": start_line + len(lines) - 1,
            "symbol": None,
        })

    return chunks


def _chunk_markdown(content: str, start_line: int) -> list[dict[str, Any]]:
    chunks: list[dict[str, Any]] = []
    lines = content.split("\n")
    heading_re = re.compile(r"^(#{1,6})\s+(.+)$")

    current_heading: str | None = None
    current_lines: list[str] = []
    current_start: int = start_line

    for i, line in enumerate(lines):
        abs_line = start_line + i
        m = heading_re.match(line)
        if m:
            if current_lines and len("\n".join(current_lines)) >= MIN_CHUNK_SIZE:
                chunks.append({
                    "text": "\n".join(current_lines),
                    "start_line": current_start,
                    "end_line": current_start + len(current_lines) - 1,
                    "heading": current_heading,
                })
            current_heading = m.group(2).strip()
            current_lines = [line]
            current_start = abs_line
        else:
            current_lines.append(line)

    if current_lines and len("\n".join(current_lines)) >= MIN_CHUNK_SIZE:
        chunks.append({
            "text": "\n".join(current_lines),
            "start_line": current_start,
            "end_line": current_start + len(current_lines) - 1,
            "heading": current_heading,
        })

    if not chunks and content.strip():
        chunks.append({
            "text": content,
            "start_line": start_line,
            "end_line": start_line + len(lines) - 1,
            "heading": None,
        })

    return chunks


def _chunk_notebook(content: str, start_line: int) -> list[dict[str, Any]]:
    chunks: list[dict[str, Any]] = []
    try:
        nb = json.loads(content)
    except (json.JSONDecodeError, ValueError):
        return chunks

    cells = nb.get("cells", [])
    for idx, cell in enumerate(cells):
        cell_type = cell.get("cell_type", "code")
        source = "".join(cell.get("source", []))
        if not source.strip():
            continue
        abs_line = start_line + idx
        chunks.append({
            "text": source,
            "start_line": abs_line,
            "end_line": abs_line,
            "cell_index": idx,
            "cell_type": cell_type,
            "heading": None,
            "symbol": None,
        })

    return chunks


def _chunk_generic(content: str, start_line: int) -> list[dict[str, Any]]:
    if not content.strip():
        return []
    return [{
        "text": content,
        "start_line": start_line,
        "end_line": start_line,
        "heading": None,
        "symbol": None,
    }]


def chunk_document(doc: CopilotDocument, config: CopilotConfig) -> list[CopilotChunk]:
    content = doc.content
    if not content.strip():
        return []

    if doc.file_type == "python":
        raw_chunks = _chunk_python(content, doc.file_path, doc.start_line)
    elif doc.file_type == "markdown":
        raw_chunks = _chunk_markdown(content, doc.start_line)
    elif doc.file_type == "notebook":
        raw_chunks = _chunk_notebook(content, doc.start_line)
    else:
        raw_chunks = _chunk_generic(content, doc.start_line)

    chunks: list[CopilotChunk] = []
    for raw in raw_chunks:
        text = raw.get("text", "")
        if len(text.encode("utf-8")) < config.min_chunk_bytes:
            if chunks:
                last = chunks[-1]
                merged_text = last.text + "\n" + text
                if len(merged_text.encode("utf-8")) <= config.max_chunk_bytes:
                    last.text = merged_text
                    last.end_line = raw.get("end_line", raw.get("start_line", last.end_line))
                    continue
            continue

        if len(text.encode("utf-8")) > config.max_chunk_bytes:
            continue

        chunk = CopilotChunk(
            chunk_id=f"{doc.document_id}:{raw.get('start_line', 0)}",
            document_id=doc.document_id,
            file_path=doc.file_path,
            file_type=doc.file_type,
            project_area=doc.project_area,
            text=text,
            start_line=raw.get("start_line"),
            end_line=raw.get("end_line"),
            cell_index=raw.get("cell_index"),
            cell_type=raw.get("cell_type"),
            heading=raw.get("heading"),
            symbol_name=raw.get("symbol"),
            tags=doc.tags,
            source_priority=doc.source_priority,
        )
        chunks.append(chunk)

    return chunks


def index_repository(repo_root: Path, config: CopilotConfig | None = None) -> list[CopilotChunk]:
    if config is None:
        config = CopilotConfig()

    repo_root = repo_root.resolve()
    chunks: list[CopilotChunk] = []
    documents: list[CopilotDocument] = []

    for dirpath, dirnames, filenames in os.walk(repo_root):
        dir_names_set = set(dirnames)
        dir_names_set.discard(".git")
        dir_names_set.discard("__pycache__")
        dir_names_set.discard(".venv")
        dir_names_set.discard("venv")
        dir_path = Path(dirpath)

        for fname in sorted(filenames):
            fpath = dir_path / fname
            if _should_exclude(fpath, config):
                continue

            ftype = _file_type(fpath)
            if ftype == "unknown":
                continue

            try:
                content = fpath.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue

            if not content.strip():
                continue

            rel = fpath.relative_to(repo_root)
            doc = RepoDocument(
                document_id=f"{rel}:{_compute_hash(content, str(rel))}",
                file_path=str(rel),
                file_type=ftype,
                language=("tr" if any(
                    c in content for c in "çğıöşüÇĞİÖŞÜ"
                ) and not fpath.suffix == ".py" else "en"),
                project_area=_project_area(fpath, repo_root),
                symbol_name=None,
                heading=None,
                start_line=1,
                end_line=len(content.split("\n")),
                content=content,
                content_hash=_compute_hash(content, str(rel)),
                last_modified=_last_modified(fpath),
                tags=[ftype, _project_area(fpath, repo_root)],
                source_priority=1.0 if ftype in ("python", "markdown") else 0.5,
            )
            documents.append(doc)

    for doc in documents:
        doc_chunks = chunk_document(doc, config)
        chunks.extend(doc_chunks)

    LOGGER.info("Indexed %d documents, %d chunks", len(documents), len(chunks))
    return chunks


def save_index(chunks: list[CopilotChunk], index_path: Path) -> None:
    index_path.parent.mkdir(parents=True, exist_ok=True)
    data = []
    for chunk in chunks:
        data.append({
            "chunk_id": chunk.chunk_id,
            "document_id": chunk.document_id,
            "file_path": chunk.file_path,
            "file_type": chunk.file_type,
            "project_area": chunk.project_area,
            "text": chunk.text,
            "start_line": chunk.start_line,
            "end_line": chunk.end_line,
            "cell_index": chunk.cell_index,
            "cell_type": chunk.cell_type,
            "heading": chunk.heading,
            "symbol_name": chunk.symbol_name,
            "tags": chunk.tags,
            "source_priority": chunk.source_priority,
            "score": chunk.score,
        })
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_index(index_path: Path) -> list[CopilotChunk]:
    if not index_path.exists():
        return []
    with open(index_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    chunks: list[CopilotChunk] = []
    for item in data:
        chunks.append(CopilotChunk(
            chunk_id=item["chunk_id"],
            document_id=item["document_id"],
            file_path=item["file_path"],
            file_type=item["file_type"],
            project_area=item["project_area"],
            text=item["text"],
            start_line=item.get("start_line"),
            end_line=item.get("end_line"),
            cell_index=item.get("cell_index"),
            cell_type=item.get("cell_type"),
            heading=item.get("heading"),
            symbol_name=item.get("symbol_name"),
            tags=item.get("tags", []),
            source_priority=item.get("source_priority", 1.0),
            score=item.get("score", 0.0),
        ))
    return chunks


def save_index_with_fingerprint(chunks: list[CopilotChunk], index_path: Path, fp_path: Path) -> str:
    save_index(chunks, index_path)
    fingerprint = build_fingerprint()
    save_fingerprint(fingerprint, fp_path)
    fp_hash = fingerprint_hash(fingerprint)
    LOGGER.info("Index saved with fingerprint %s (%d chunks)", fp_hash[:8], len(chunks))
    return fp_hash


def load_index_with_cache(index_path: Path, fp_path: Path) -> tuple[list[CopilotChunk], str]:
    if not index_path.exists():
        return [], "cold_build"
    fingerprint = build_fingerprint()
    if not fingerprint_matches(fingerprint, fp_path):
        return [], "invalidated"
    cached_fp = load_fingerprint(fp_path)
    if cached_fp is None or cached_fp.get("state") != "valid":
        return [], "corrupt_rebuild"
    LOGGER.info("Warm index load (fingerprint match)")
    return load_index(index_path), "warm_load"