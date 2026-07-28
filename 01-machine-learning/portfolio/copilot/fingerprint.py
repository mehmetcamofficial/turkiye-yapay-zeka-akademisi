from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from datetime import datetime, timezone

from portfolio.copilot.config import REPO_ROOT, MAX_FILE_SIZE
from portfolio.copilot.schema import CopilotConfig


SCHEMA_VERSION = "1.0"
CHUNKING_VERSION = "1.0"
IGNORE_RULE_VERSION = "1.0"


def _file_fingerprint(path: Path) -> dict:
    try:
        stat = path.stat()
        return {
            "path": str(path.relative_to(REPO_ROOT)),
            "size": stat.st_size,
            "mtime": stat.st_mtime,
            "hash": hashlib.sha256(path.read_bytes()).hexdigest()[:16],
        }
    except Exception:
        return {}


def build_fingerprint(config: CopilotConfig | None = None) -> dict:
    if config is None:
        config = CopilotConfig()

    files: list[dict] = []
    for dirpath, dirnames, filenames in os.walk(REPO_ROOT):
        dir_path = Path(dirpath)
        dirnames[:] = sorted([d for d in dirnames if d not in config.ignored_directories])
        rel_dir = str(dir_path.relative_to(REPO_ROOT))
        if "copilot/index" in rel_dir or "acceptance_project_copilot" in rel_dir or rel_dir.startswith("copilot/index"):
            dirnames.clear()

        for fname in sorted(filenames):
            fpath = dir_path / fname
            try:
                fsize = fpath.stat().st_size
            except OSError:
                continue
            if fsize > config.max_file_size_bytes:
                continue
            if fpath.suffix not in {".py", ".md", ".yaml", ".yml", ".json", ".toml", ".txt", ".csv", ".rst", ".cfg", ".ini", ".ipynb"}:
                continue
            # Skip excluded patterns
            skip = False
            for pattern in config.exclude_patterns:
                if pattern.startswith("*"):
                    if fname.endswith(pattern[1:]):
                        skip = True
                        break
                elif fname == pattern:
                    skip = True
                    break
            if skip:
                continue
            for parent in fpath.parents:
                if parent.name in config.ignored_directories:
                    skip = True
                    break
            if skip:
                continue

            fp = _file_fingerprint(fpath)
            if fp:
                files.append(fp)

    return {
        "schema_version": SCHEMA_VERSION,
        "chunking_version": CHUNKING_VERSION,
        "ignore_rule_version": IGNORE_RULE_VERSION,
        "repo_root": str(REPO_ROOT),
        "file_count": len(files),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "files": files,
    }


def fingerprint_hash(fingerprint: dict) -> str:
    canonical = json.dumps({
        "schema_version": fingerprint["schema_version"],
        "chunking_version": fingerprint["chunking_version"],
        "ignore_rule_version": fingerprint["ignore_rule_version"],
        "file_count": fingerprint["file_count"],
        "files": sorted(
            [(f["path"], f["size"], f["hash"]) for f in fingerprint["files"]],
            key=lambda x: x[0],
        ),
    }, sort_keys=True)
    return hashlib.sha256(canonical.encode()).hexdigest()[:32]


def fingerprint_matches(fingerprint: dict, fp_path: Path) -> bool:
    if not fp_path.exists():
        return False
    try:
        stored = json.loads(fp_path.read_text())
        return fingerprint_hash(fingerprint) == stored.get("fingerprint_hash")
    except Exception:
        return False


def save_fingerprint(fingerprint: dict, fp_path: Path) -> None:
    fp_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "fingerprint_hash": fingerprint_hash(fingerprint),
        "schema_version": fingerprint["schema_version"],
        "chunking_version": fingerprint["chunking_version"],
        "ignore_rule_version": fingerprint["ignore_rule_version"],
        "file_count": fingerprint["file_count"],
        "generated_at": fingerprint["generated_at"],
        "state": "valid",
    }
    fp_path.write_text(json.dumps(payload, indent=2))


def load_fingerprint(fp_path: Path) -> dict | None:
    if not fp_path.exists():
        return None
    try:
        return json.loads(fp_path.read_text())
    except Exception:
        return None
