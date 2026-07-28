from __future__ import annotations

from pathlib import Path

SECRET_PATTERNS = [
    "api_key", "apikey", "secret_key", "secretkey", "private_key",
    "privatekey", "token", "bearer", "password", "passwd", "credential",
    "database_url", "db_url", "connection_string", "aws_access_key",
    "aws_secret_key", "google_api_key", "openai_api_key",
]
SENSITIVE_EXTENSIONS = {".env", ".pem", ".key", ".p12", ".pfx", ".secret"}
LOCAL_USER_DIRS = ["/home/", "/Users/", "/root/", "/tmp/"]


def is_secret_file(path: Path) -> bool:
    name_lower = path.name.lower()
    for pattern in SECRET_PATTERNS:
        if pattern in name_lower:
            return True
    if path.suffix.lower() in SENSITIVE_EXTENSIONS:
        return True
    if path.name == ".env" or path.name.startswith(".env."):
        return True
    return False


def is_sensitive_content(text: str, max_check_bytes: int = 2048) -> bool:
    check_text = text[:max_check_bytes]
    for pattern in SECRET_PATTERNS:
        if pattern in check_text.lower():
            return True
    for local_dir in LOCAL_USER_DIRS:
        if local_dir in check_text:
            return True
    return False


def normalize_path(repo_root: Path, file_path: str) -> Path:
    resolved = (repo_root / file_path).resolve()
    repo_resolved = repo_root.resolve()
    try:
        resolved.relative_to(repo_resolved)
    except ValueError:
        return repo_resolved
    return resolved


def is_within_repo(path: Path, repo_root: Path) -> bool:
    try:
        path.resolve().relative_to(repo_root.resolve())
        return True
    except ValueError:
        return False


def sanitize_path_display(file_path: str) -> str:
    if file_path.startswith("/"):
        parts = file_path.split("/")
        return "/".join(parts[-3:]) if len(parts) > 3 else file_path
    return file_path