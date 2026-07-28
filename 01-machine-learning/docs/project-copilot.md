# AI Project Copilot

## Purpose

The AI Project Copilot is a read-only repository assistant that answers questions about the `turkiye-yapay-zeka-akademisi` project using only verified repository evidence. It is designed for visitors, hiring managers, and developers who need to understand the portfolio's projects, models, notebooks, datasets, evaluation metrics, architecture, and implementation decisions.

## Architecture

```
User Question
    ↓
Intent Classification
    ↓
Repository Retrieval (hybrid: lexical + symbol + path + heading + project area + source priority)
    ↓
Evidence Filtering
    ↓
Answer Composer (extractive mode)
    ↓
Citation Validator
    ↓
Copilot UI (Streamlit page: project_copilot)
```

## Indexing

The indexer walks the repository from `REPO_ROOT`, skipping:
- `.git`, `__pycache__`, `.venv`, `venv`, `env`
- Model binaries (`*.pkl`, `*.faiss`, `*.npy`)
- Generated artifacts (`acceptance_*`, `validation_screenshots`, `performance_summary.json`)
- Hidden configuration and secret files (`.env`, `*.pem`, `*.key`)
- Cache directories and IDE files

Each indexed file is chunked structure-aware:
- **Python**: function/class boundaries preserved
- **Markdown**: heading hierarchy respected
- **Notebooks**: cell-level chunks with cell index tracking
- **Config/data**: logical object groups

## Retrieval

Hybrid retrieval combines six weighted signals:

```
combined_score =
  lexical_score
  + symbol_boost
  + path_boost
  + heading_boost
  + project_area_boost
  + source_priority_boost
```

Intent classification influences retrieval weighting across 8 categories:
`find_file`, `explain_code`, `explain_metric`, `compare_projects`,
`summarize_project`, `locate_symbol`, `architecture_question`, `test_question`,
`general_repository_question`.

## Answer Generation

### Extractive Mode (default)
No external model required. Deterministic and fast. Returns relevant snippets from indexed chunks with inline citations.

### Generative Mode (optional)
Requires external provider configuration. Uses only retrieved evidence and never answers beyond supplied context. Disabled by default.

### Answer Contract (every answer)
- direct answer
- evidence summary
- source citations (`relative/path/file.py:L10-L38`)
- confidence (High / Medium / Low / No evidence)
- limitations (when applicable)

## Citations

Every factual answer includes at least one source citation in format:
`relative/path/to/file.py:L12-L38`

For notebooks: `relative/path/notebook.ipynb:cell-7`

Citation validation rejects:
- Missing files
- Invalid line ranges
- Citations outside retrieved evidence

Maximum 5 primary citations by default.

## Privacy

- No absolute local filesystem paths exposed
- No shell command execution
- No Python code execution
- No git operations
- No file writes
- No network requests
- Session-local memory only (no persistent chat history)
- Secret files (.env, keys, tokens) excluded from indexing
- Content-level secret detection for potential credentials

## Configuration

Key settings in `portfolio/copilot/config.py`:
| Setting | Default | Description |
|---------|---------|-------------|
| `max_file_size_bytes` | 512 KB | Maximum file size to index |
| `max_chunk_bytes` | 8 KB | Maximum chunk size |
| `min_chunk_bytes` | 120 | Minimum chunk size |
| `max_citations` | 5 | Maximum primary citations |
| `max_memory_turns` | 6 | Conversation memory depth |

## Evaluation

30 golden questions across 9 categories in `evaluation/search/copilot_golden.json`. Quality gates (see Copilot Metrics section).

### Release scopes

The public release contains the production Copilot, UI integration, canonical
evaluation, golden dataset, release gates, and five public test files. Its
fresh-checkout contract is 274 passing tests with no failures.

The development workspace additionally retains 102 research-only tests for
embedding experiments, graph experiments, and forensic tooling. Those tests
and their generated acceptance evidence are intentionally outside the first
public release; the full development/research contract is 376 passing tests
with no failures.

## Limitations

- Read-only: cannot modify code, execute commands, or write files
- Index may miss binary files and generated artifacts (by design)
- Retrieval quality depends on lexical overlap; semantic retrieval is not yet implemented
- No persistent memory across sessions
- No external model access by default
- Confidence scores are heuristic, not calibrated probabilities
