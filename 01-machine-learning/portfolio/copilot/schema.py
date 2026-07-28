from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class RepoDocument:
    document_id: str
    file_path: str
    file_type: str
    language: str
    project_area: str
    symbol_name: str | None
    heading: str | None
    start_line: int
    end_line: int
    content: str
    content_hash: str
    last_modified: str
    tags: list[str] = field(default_factory=list)
    source_priority: float = 1.0


@dataclass
class CopilotChunk:
    chunk_id: str
    document_id: str
    file_path: str
    file_type: str
    project_area: str
    text: str
    start_line: int | None
    end_line: int | None
    cell_index: int | None
    cell_type: str | None
    heading: str | None = None
    symbol_name: str | None = None
    tags: list[str] = field(default_factory=list)
    score: float = 0.0
    source_priority: float = 1.0


@dataclass
class CopilotCitation:
    file_path: str
    start_line: int | None
    end_line: int | None
    cell_index: int | None
    snippet: str
    source_type: str
    project_area: str
    retrieval_score: float = 0.0


@dataclass
class CopilotAnswer:
    direct_answer: str
    evidence_summary: str
    citations: list[CopilotCitation]
    confidence: str
    limitations: str | None
    intent: str | None
    retrieval_count: int = 0
    unsupported: bool = False


@dataclass
class CopilotConfig:
    max_file_size_bytes: int = 512 * 1024
    max_chunk_bytes: int = 8192
    min_chunk_bytes: int = 120
    max_citations: int = 5
    repo_root: str = "."
    ml_root: str = "01-machine-learning"
    exclude_patterns: list[str] = field(default_factory=lambda: [
        ".git", "__pycache__", ".venv", "venv", "env", ".env",
        "*.pkl", "*.faiss", "*.npy", "*.jsonl",
        "acceptance_screenshots", "acceptance_search_experience_v2",
        "acceptance_sprint*", "acceptance_suggestion_ui",
        "validation_screenshots", "performance_summary.json",
        ".streamlit", ".vscode", ".idea", "*.log", "*.tmp",
        "copilot/index", "copilot/__pycache__",
        "acceptance_project_copilot",
        "evaluation/search/copilot_golden.json",
        "evaluation/search/audit_copilot.py",
        "evaluation/search/real_evaluation.py",
        "evaluation/search/*_result.json",
        "evaluation/search/*_results.json",
        "evaluation/search/embedding_pilot.py",
        "evaluation/search/hybrid_upper_bound.py",
        "evaluation/search/rc11_analyzer.py",
        "evaluation/search/reconciliation_tool.py",
        "evaluation/search/repair_golden.py",
        "evaluation/search/run_all_phases.py",
        "evaluation/search/run_phases_3_to_11.py",
        "evaluation/search/golden_dataset_audit.json",
        "evaluation/search/retrieval_failure_taxonomy.json",
        "evaluation/search/golden_dataset_snapshot.json",
        "evaluation/search/current_alias_map.json",
        "evaluation/search/baseline_*",
    ])
    source_extensions: list[str] = field(default_factory=lambda: [
        ".py", ".md", ".yaml", ".yml", ".json", ".toml",
        ".txt", ".csv", ".rst", ".cfg", ".ini", ".ipynb",
    ])
    ignored_directories: set[str] = field(default_factory=lambda: {
        ".git", "__pycache__", ".venv", "venv", "env", ".idea", ".vscode",
        "node_modules", ".streamlit", "artifacts", "outputs", "models",
        "data", ".pytest_cache", ".ruff_cache", "mypy_cache", "index",
        "acceptance_project_copilot",
    })
