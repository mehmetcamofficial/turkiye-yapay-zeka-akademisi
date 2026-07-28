from __future__ import annotations

from pathlib import Path
from typing import Optional

from portfolio.copilot.schema import (
    CopilotCitation,
    CopilotChunk,
)


def validate_citation(citation: CopilotCitation, repo_root: Path) -> bool:
    file_path = repo_root / citation.file_path
    if not file_path.exists():
        return False
    if citation.start_line is not None and citation.end_line is not None:
        if citation.start_line < 1 or citation.end_line < citation.start_line:
            return False
    if not citation.file_path:
        return False
    return True


def validate_citations(
    citations: list[CopilotCitation],
    chunks: list[CopilotChunk],
    query: str,
) -> list[CopilotCitation]:
    repo_root = Path.cwd()
    valid: list[CopilotCitation] = []
    seen_paths: set[str] = set()

    for citation in citations:
        if not validate_citation(citation, repo_root):
            continue
        path_key = citation.file_path
        if path_key in seen_paths:
            continue
        seen_paths.add(path_key)

        supporting = any(
            c.file_path == citation.file_path
            and query.lower() in c.text.lower()[:200]
            for c in chunks
        )
        if supporting or citation.file_path.endswith((".md", ".py", ".yaml")):
            valid.append(citation)

    return valid[:10]