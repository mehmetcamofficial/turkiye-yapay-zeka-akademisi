"""Search index module for portfolio repository — product-resource BM25 index."""

from __future__ import annotations

import json
import re
import hashlib
import pickle
import os
from pathlib import Path
from typing import Any
from dataclasses import dataclass, field, asdict
from datetime import datetime
from collections import defaultdict

import numpy as np

try:
    from rank_bm25 import BM25Okapi
    BM25_AVAILABLE = True
except ImportError:
    BM25_AVAILABLE = False

from portfolio.config import REPOSITORY_ROOT, ML_ROOT, ARTIFACTS_DIR
from portfolio.experiment_store import load_experiments
from portfolio.project_registry import get_project_registry
from portfolio.data_science_registry import evaluate_midterm, evaluate_final_project
from portfolio.pages.notebook_status import _discover_notebooks


RESOURCE_TYPES = [
    "experiment",
    "model",
    "notebook",
    "dataset",
    "document",
    "source_code",
    "configuration",
]


@dataclass
class SearchDocument:
    """Represents a searchable resource in the index."""
    resource_id: str
    title: str
    resource_type: str
    content: str
    tags: list[str] = field(default_factory=list)
    summary: str = ""
    repository_relative_path: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    actions: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SearchDocument":
        return cls(**data)


@dataclass
class SearchResult:
    """Represents a search result."""
    document: SearchDocument
    score: float
    snippet: str = ""
    match_reason: str = ""


class SearchIndex:
    """BM25-based search index for portfolio product resources."""

    INDEX_DIR = ARTIFACTS_DIR / "search_index"
    INDEX_FILE = INDEX_DIR / "search_index.pkl"
    FINGERPRINT_FILE = INDEX_DIR / "fingerprint.txt"
    METADATA_FILE = INDEX_DIR / "metadata.json"

    def __init__(self):
        self.documents: list[SearchDocument] = []
        self.bm25: Any = None
        self.tokenized_docs: list[list[str]] = []
        self._ready = False
        self._fingerprint = ""
        self._stats: dict[str, Any] = {}

    def _tokenize(self, text: str) -> list[str]:
        """Simple tokenization for BM25."""
        text = text.lower()
        text = re.sub(r'[^\w\s]', ' ', text)
        tokens = text.split()
        return [t for t in tokens if len(t) > 2]

    def _compute_fingerprint(self) -> str:
        """Compute repository fingerprint for cache invalidation."""
        hasher = hashlib.sha256()
        
        file_patterns = ['*.md', '*.py', '*.ipynb', '*.json', '*.yaml', '*.yml', '*.toml']
        exclude_dirs = {'.git', '__pycache__', '.venv', '.pytest_cache', 'node_modules', 
                       '.ipynb_checkpoints', 'artifacts', 'data', '.streamlit'}
        
        files_to_hash = []
        for pattern in file_patterns:
            for file_path in REPOSITORY_ROOT.rglob(pattern):
                if any(excl in file_path.parts for excl in exclude_dirs):
                    continue
                if file_path.is_file():
                    files_to_hash.append(file_path)
        
        files_to_hash.sort(key=lambda p: str(p.relative_to(REPOSITORY_ROOT)))
        
        for file_path in files_to_hash:
            try:
                stat = file_path.stat()
                hasher.update(str(file_path.relative_to(REPOSITORY_ROOT)).encode())
                hasher.update(str(stat.st_mtime_ns).encode())
                hasher.update(str(stat.st_size).encode())
            except (OSError, ValueError):
                pass
        
        for reg_file in [ARTIFACTS_DIR / "experiments" / "experiments.jsonl",
                        ML_ROOT / "portfolio" / "project_registry.py"]:
            if reg_file.is_file():
                stat = reg_file.stat()
                hasher.update(str(reg_file).encode())
                hasher.update(str(stat.st_mtime_ns).encode())
        
        return hasher.hexdigest()[:16]

    def _extract_notebook_text(self, content: str) -> str:
        """Extract text from notebook JSON."""
        try:
            nb = json.loads(content)
            texts = []
            for cell in nb.get('cells', []):
                if cell.get('cell_type') == 'markdown':
                    for line in cell.get('source', []):
                        texts.append(line)
                elif cell.get('cell_type') == 'code':
                    for line in cell.get('source', []):
                        if not line.strip().startswith('#'):
                            texts.append(line)
            return '\n'.join(texts)
        except Exception:
            return ''

    def _categorize_file(self, path: Path, content: str) -> tuple[str, str]:
        """Determine resource type and extract title."""
        rel = path.relative_to(REPOSITORY_ROOT)
        parts = rel.parts
        suffix = path.suffix
        
        if suffix == '.ipynb':
            return "notebook", path.stem.replace('_', ' ').replace('-', ' ').title()
        elif suffix == '.md':
            return "document", path.stem.replace('_', ' ').replace('-', ' ').title()
        elif suffix in ('.yaml', '.yml', '.toml', '.json'):
            if 'config' in str(rel).lower() or 'settings' in str(rel).lower():
                return "configuration", path.stem.replace('_', ' ').replace('-', ' ').title()
            return "configuration", path.stem.replace('_', ' ').replace('-', ' ').title()
        elif suffix == '.py':
            if 'test' in str(rel).lower():
                return "source_code", path.stem.replace('_', ' ').replace('-', ' ').title()
            if 'train' in str(rel).lower() or 'model' in str(rel).lower():
                return "source_code", path.stem.replace('_', ' ').replace('-', ' ').title()
            return "source_code", path.stem.replace('_', ' ').replace('-', ' ').title()
        else:
            return "other", path.stem.replace('_', ' ').replace('-', ' ').title()

    def _extract_title(self, path: Path, content: str, resource_type: str) -> str:
        """Extract a meaningful title from content."""
        if resource_type == "notebook":
            try:
                nb = json.loads(content)
                for cell in nb.get('cells', []):
                    if cell.get('cell_type') == 'markdown':
                        for line in cell.get('source', []):
                            line = line.strip()
                            if line.startswith('# '):
                                return line[2:].strip()
            except Exception:
                pass
        elif resource_type == "document":
            for line in content.split('\n'):
                line = line.strip()
                if line.startswith('# '):
                    return line[2:].strip()
        elif resource_type in ("source_code", "configuration"):
            for line in content.split('\n')[:30]:
                line = line.strip()
                if line.startswith(('"""', "'''")) and not line[0] in 'frbFRB':
                    if line.endswith(('"""', "'''")) and len(line) > 6:
                        title = line[3:-3].strip()
                        if title and not title[-1] in ',;)]':
                            return title
                    elif line in ('"""', "'''"):
                        continue
                    else:
                        title = line[3:].strip()
                        if title and not title[-1] in ',;)]':
                            return title
        return path.stem.replace('_', ' ').replace('-', ' ').title()

    def _generate_summary(self, content: str, max_len: int = 300) -> str:
        """Generate a short summary from content."""
        text = re.sub(r'[#*`_~\[\]()>]', '', content)
        text = re.sub(r'\s+', ' ', text).strip()
        if len(text) > max_len:
            return text[:max_len] + '...'
        return text

    def _discover_all_resources(self) -> list[SearchDocument]:
        """Discover and create documents for all indexable resources."""
        documents = []
        
        # English synonyms for Turkish capabilities
        CAPABILITY_SYNONYMS = {
            "duygu analizi": ["sentiment", "sentiment analysis"],
            "müşteri kaybı tahmini": ["churn", "churn prediction", "customer churn"],
            "konut tahmini": ["housing", "housing price", "housing prediction", "california housing"],
            "arama": ["search", "retrieval", "relevance"],
            "sınıflandırma": ["classification", "classifier"],
            "regresyon": ["regression", "regressor"],
            "kümeleme": ["clustering", "cluster"],
        }
        
        def _expand_tags(tags: list[str]) -> list[str]:
            """Add English synonyms to tags."""
            expanded = list(tags)
            for tag in tags:
                tag_lower = tag.lower()
                if tag_lower in CAPABILITY_SYNONYMS:
                    expanded.extend(CAPABILITY_SYNONYMS[tag_lower])
            return list(set(expanded))
        
        documents = []
        
        # 1. Experiments from JSONL store
        for exp in load_experiments():
            capability = exp.get('capability', '')
            tags = [exp.get('experiment_type', ''), capability, exp.get('model_name', '')]
            expanded_tags = []
            for tag in tags:
                expanded_tags.append(tag)
                tag_lower = tag.lower()
                if tag_lower in CAPABILITY_SYNONYMS:
                    expanded_tags.extend(CAPABILITY_SYNONYMS[tag_lower])
            expanded_tags = list(set(expanded_tags))
            
            doc = SearchDocument(
                resource_id=f"experiment:{exp.get('experiment_id', '')}",
                title=f"{exp.get('capability', 'Experiment')} — {exp.get('experiment_type', '')}",
                resource_type="experiment",
                content=f"{capability} {exp.get('model_name', '')} {exp.get('experiment_type', '')} "
                       f"{' '.join(exp.get('metrics', {}).keys())} {' '.join(exp.get('parameters', {}).keys())} "
                       f"{exp.get('notes', '')}",
                tags=expanded_tags,
                summary=f"Experiment: {exp.get('experiment_type', '')} on {capability} "
                       f"with {exp.get('model_name', '')}. Status: {exp.get('status', '')}.",
                repository_relative_path=exp.get('source', ''),
                metadata={
                    "experiment_id": exp.get('experiment_id', ''),
                    "experiment_type": exp.get('experiment_type', ''),
                    "capability": capability,
                    "model_name": exp.get('model_name', ''),
                    "status": exp.get('status', ''),
                    "started_at": exp.get('started_at', ''),
                    "completed_at": exp.get('completed_at', ''),
                    "duration_ms": exp.get('duration_ms', 0),
                    "metrics": exp.get('metrics', {}),
                    "parameters": exp.get('parameters', {}),
                    "artifact_paths": exp.get('artifact_paths', []),
                    "source": exp.get('source', ''),
                    "notes": exp.get('notes', ''),
                },
                actions=["open_details", "github", "copy_path"],
            )
            documents.append(doc)
        
        # 2. Models from registry
        for project in get_project_registry():
            if project.get('status') in ('verified', 'available', 'experimental'):
                eng_synonyms = []
                name = project.get('name', '')
                model_name = project.get('final_model', '')
                if 'churn' in name.lower() or 'müşteri' in name.lower():
                    eng_synonyms.extend(['churn', 'customer churn'])
                if 'housing' in name.lower() or 'konut' in name.lower() or 'california' in name.lower():
                    eng_synonyms.extend(['housing', 'california housing'])
                if 'sentiment' in name.lower() or 'duygu' in name.lower() or 'nlp' in name.lower():
                    eng_synonyms.extend(['sentiment', 'nlp', 'sentiment analysis'])
                if 'random forest' in name.lower():
                    eng_synonyms.append('random forest')
                if 'logistic' in name.lower():
                    eng_synonyms.append('logistic regression')
                if 'xgboost' in name.lower() or 'xgb' in name.lower():
                    eng_synonyms.append('xgboost')
                
                eng_synonyms = list(set(eng_synonyms))
                tags = [project.get('final_model', ''), project.get('status', ''), project.get('category', '')] + eng_synonyms
                
                doc = SearchDocument(
                    resource_id=f"model:{project.get('id', '')}",
                    title=project.get('name', ''),
                    resource_type="model",
                    content=f"{project.get('name', '')} {project.get('final_model', '')} "
                           f"{project.get('primary_metric_name', '')} {project.get('category', '')} "
                           f"{' '.join(project.get('limitations', []))} {' '.join(eng_synonyms)}",
                    tags=tags,
                    summary=f"Model: {project.get('name', '')} ({project.get('final_model', '')}). "
                           f"Status: {project.get('status', '')}. Primary metric: "
                           f"{project.get('primary_metric_name', '')}={project.get('primary_metric_value', 'N/A')}.",
                    repository_relative_path=project.get('model_path', ''),
                    metadata={
                        "model_id": project.get('id', ''),
                        "status": project.get('status', ''),
                        "final_model": project.get('final_model', ''),
                        "primary_metric_name": project.get('primary_metric_name', ''),
                        "primary_metric_value": project.get('primary_metric_value'),
                        "dataset": project.get('dataset', ''),
                        "dataset_size": project.get('dataset_size', ''),
                        "limitations": project.get('limitations', []),
                        "governance_decision": project.get('governance_decision', ''),
                    },
                    actions=["open_registry", "github", "copy_path"],
                )
                documents.append(doc)
        
        # 3. Datasets from data science registry
        midterm = evaluate_midterm()
        if midterm.get('dataset_path'):
            doc = SearchDocument(
                resource_id="dataset:midterm",
                title=midterm.get('name', 'Midterm Dataset'),
                resource_type="dataset",
                content=f"{midterm.get('name', '')} {midterm.get('dataset', '')} "
                       f"{' '.join(midterm.get('available_columns', []))} "
                       f"{midterm.get('source', '')}",
                tags=["dataset", "midterm", "trendyol"],
                summary=f"Dataset: {midterm.get('name', '')}. "
                       f"Status: {midterm.get('status', '')}. "
                       f"Columns: {len(midterm.get('available_columns', []))}/{len(midterm.get('required_columns', []))}. "
                       f"Schema compatible: {midterm.get('schema_compatible', False)}.",
                repository_relative_path=midterm.get('dataset_path', ''),
                metadata={
                    "dataset_id": midterm.get('id', ''),
                    "dataset": midterm.get('dataset', ''),
                    "source": midterm.get('source', ''),
                    "required_columns": midterm.get('required_columns', []),
                    "available_columns": midterm.get('available_columns', []),
                    "missing_columns": midterm.get('missing_columns', []),
                    "schema_compatible": midterm.get('schema_compatible', False),
                    "total_questions": midterm.get('total_questions', 0),
                    "completed_questions": midterm.get('completed_questions', 0),
                    "status": midterm.get('status', ''),
                },
                actions=["open_metadata", "github", "copy_path"],
            )
            documents.append(doc)
        
        final = evaluate_final_project()
        if final.get('notebook_ready'):
            doc = SearchDocument(
                resource_id="dataset:final",
                title=final.get('name', 'Final Dataset'),
                resource_type="dataset",
                content=f"{final.get('name', '')} {final.get('dataset', '')}",
                tags=["dataset", "final"],
                summary=f"Final Project Dataset: {final.get('name', '')}. Status: {final.get('status', '')}.",
                repository_relative_path="02-data-science/final-project",
                metadata={
                    "dataset_id": final.get('id', ''),
                    "dataset": final.get('dataset', ''),
                    "status": final.get('status', ''),
                    "notebook_ready": final.get('notebook_ready', False),
                    "outputs_ready": final.get('outputs_ready', False),
                },
                actions=["open_metadata", "github", "copy_path"],
            )
            documents.append(doc)
        
        # 4. Notebooks from discovery
        for nb in _discover_notebooks():
            doc = SearchDocument(
                resource_id=f"notebook:{nb['path']}",
                title=nb['name'],
                resource_type="notebook",
                content=nb.get('content_text', ''),
                tags=["notebook", nb['name']],
                summary=f"Notebook: {nb['name']}. "
                       f"Outputs: {'Yes' if nb.get('has_outputs') else 'No'}. "
                       f"Metadata: {'Yes' if nb.get('has_metadata') else 'No'}. "
                       f"Size: {nb.get('size_bytes', 0)} bytes.",
                repository_relative_path=nb['path'],
                metadata={
                    "notebook_name": nb['name'],
                    "github_url": nb['github_url'],
                    "colab_url": nb['colab_url'],
                    "has_outputs": nb.get('has_outputs', False),
                    "has_metadata": nb.get('has_metadata', False),
                    "size_bytes": nb.get('size_bytes', 0),
                    "colab_valid": nb.get('colab_valid', True),
                },
                actions=["open", "github", "colab", "download", "copy_path"],
            )
            documents.append(doc)
        
        # 5. Repository files (documents, source code, config)
        exclude_dirs = {'.git', '__pycache__', '.venv', '.pytest_cache', 'node_modules', 
                       '.ipynb_checkpoints', 'artifacts', 'data', '.streamlit', 
                       '01-machine-learning/trendyol-search-relevance/models',
                       '01-machine-learning/trendyol-search-relevance/search_pipeline/__pycache__',
                       '.github'}
        
        for pattern in ['*.md', '*.py', '*.json', '*.yaml', '*.yml', '*.toml']:
            for file_path in REPOSITORY_ROOT.rglob(pattern):
                if any(excl in file_path.parts for excl in exclude_dirs):
                    continue
                if file_path.is_file():
                    try:
                        content = file_path.read_text(encoding='utf-8', errors='ignore')
                        if not content.strip() or len(content) < 50:
                            continue
                        
                        resource_type, title = self._categorize_file(file_path, content)
                        if resource_type == "other":
                            continue
                        
                        rel = file_path.relative_to(REPOSITORY_ROOT)
                        extracted_title = self._extract_title(file_path, content, resource_type)
                        
                        doc = SearchDocument(
                            resource_id=f"{resource_type}:{rel}",
                            title=extracted_title,
                            resource_type=resource_type,
                            content=content,
                            tags=[resource_type, title],
                            summary=self._generate_summary(content),
                            repository_relative_path=str(rel),
                            metadata={
                                "extension": file_path.suffix,
                                "size": len(content),
                            },
                            actions=["view_source", "github", "copy_path"] if resource_type in ("document", "source_code", "configuration")
                                     else ["github", "copy_path"],
                        )
                        documents.append(doc)
                    except Exception as e:
                        print(f"Error indexing {file_path}: {e}")
        
        return documents

    def build_index(self, force_rebuild: bool = False) -> int:
        """Build search index from repository resources."""
        if not force_rebuild and self.load_index():
            return len(self.documents)

        print("Building search index...")
        self.documents = self._discover_all_resources()
        print(f"Discovered {len(self.documents)} resources")

        self.tokenized_docs = [self._tokenize(doc.content) for doc in self.documents]

        if BM25_AVAILABLE and self.tokenized_docs:
            self.bm25 = BM25Okapi(self.tokenized_docs)
        else:
            self.bm25 = None

        self._fingerprint = self._compute_fingerprint()
        self._ready = True
        self._update_stats()
        self.save_index()
        return len(self.documents)

    def save_index(self):
        """Save index to disk."""
        self.INDEX_DIR.mkdir(parents=True, exist_ok=True)
        data = {
            'documents': [doc.to_dict() for doc in self.documents],
            'tokenized_docs': self.tokenized_docs,
            'fingerprint': self._fingerprint,
            'timestamp': datetime.now().isoformat(),
        }
        with open(self.INDEX_FILE, 'wb') as f:
            pickle.dump(data, f)

        with open(self.FINGERPRINT_FILE, 'w') as f:
            f.write(self._fingerprint)

        self._update_stats()
        with open(self.METADATA_FILE, 'w') as f:
            json.dump(self._stats, f, indent=2, default=str)

    def load_index(self) -> bool:
        """Load index from disk if fingerprint matches."""
        if not self.INDEX_FILE.exists() or not self.FINGERPRINT_FILE.exists():
            return False
        try:
            with open(self.FINGERPRINT_FILE, 'r') as f:
                saved_fp = f.read().strip()
            current_fp = self._compute_fingerprint()
            if saved_fp != current_fp:
                print(f"Fingerprint mismatch: saved={saved_fp} current={current_fp}")
                return False

            with open(self.INDEX_FILE, 'rb') as f:
                data = pickle.load(f)

            self.documents = [SearchDocument.from_dict(d) for d in data['documents']]
            self.tokenized_docs = data.get('tokenized_docs', [])
            self._fingerprint = data['fingerprint']

            if BM25_AVAILABLE and self.tokenized_docs:
                self.bm25 = BM25Okapi(self.tokenized_docs)
            else:
                self.bm25 = None

            self._ready = True
            self._update_stats()
            print(f"Loaded index with {len(self.documents)} documents (fingerprint: {self._fingerprint})")
            return True
        except Exception as e:
            print(f"Error loading index: {e}")
            return False

    def ensure_ready(self) -> None:
        """Ensure index is built and valid."""
        if not self._ready:
            current_fp = self._compute_fingerprint()
            if self._fingerprint and self._fingerprint == current_fp:
                self.load_index()
            else:
                self.build_index()

    def _update_stats(self):
        """Update index statistics."""
        type_counts = {}
        for doc in self.documents:
            type_counts[doc.resource_type] = type_counts.get(doc.resource_type, 0) + 1
        
        self._stats = {
            'total_documents': len(self.documents),
            'resource_types': type_counts,
            'last_indexed': datetime.now().isoformat(),
            'index_status': 'ready' if self._ready else 'stale',
            'fingerprint': self._fingerprint,
        }

    def get_stats(self) -> dict[str, Any]:
        """Get index statistics."""
        if not self._stats:
            self._update_stats()
        return self._stats.copy()

    def search(self, query: str, top_k: int = 10, resource_type: str | None = None) -> list[SearchResult]:
        """Search the index with field-weighted scoring."""
        self.ensure_ready()
        
        if not self.documents:
            return []

        query_lower = query.lower()
        query_terms = set(self._tokenize(query))
        
        # Candidate selection: multi-stage to catch all relevant resources
        candidate_indices = set()
        
        # 1. BM25 top candidates (content-based)
        if BM25_AVAILABLE and self.bm25:
            tokens = self._tokenize(query)
            bm25_scores = self.bm25.get_scores(tokens)
            top_indices = np.argsort(bm25_scores)[::-1][:top_k * 20]
            candidate_indices.update(top_indices)
        else:
            tokens = self._tokenize(query)
            scores = []
            for i, doc in enumerate(self.documents):
                score = sum(doc.content.lower().count(t) for t in tokens)
                scores.append(score)
            scores = np.array(scores)
            top_indices = np.argsort(scores)[::-1][:top_k * 20]
            candidate_indices.update(top_indices)
        
        # 2. Title match candidates (exact or partial)
        query_lower = query.lower()
        for i, doc in enumerate(self.documents):
            if query_lower in doc.title.lower() or doc.title.lower() in query_lower:
                candidate_indices.add(i)
        
        # 3. Tag match candidates
        query_terms = set(self._tokenize(query))
        for i, doc in enumerate(self.documents):
            for tag in doc.tags:
                if query.lower() in tag.lower() or any(t in tag.lower() for t in query_terms if len(t) > 3):
                    candidate_indices.add(i)
                    break
        
        # 4. Product resource candidates for relevant queries
        product_query_terms = {"experiment", "model", "notebook", "dataset", "document", 
                               "churn", "sentiment", "housing", "architecture", "grid", "random", "forest", 
                               "duygu", "analizi", "churn", "müşteri", "kaybı", "konut", "tahmini"}
        if any(t in query.lower() for t in product_query_terms):
            for i, doc in enumerate(self.documents):
                if doc.resource_type in {"experiment", "model", "notebook", "dataset", "document"}:
                    candidate_indices.add(i)
        
        top_indices = list(candidate_indices)

        # Normalize scores for fair weighting - compute scores for all documents
        tokens = self._tokenize(query)
        scores = np.array([sum(doc.content.lower().count(t) for t in tokens) for doc in self.documents], dtype=float)
        
        min_score = float(np.min(scores[list(candidate_indices)])) if candidate_indices else 0.0
        max_score = float(np.max(scores[list(candidate_indices)])) if candidate_indices else 1.0
        score_range = max_score - min_score if max_score > min_score else 1.0

        query_lower = query.lower()
        query_terms = set(self._tokenize(query))

        results = []
        for idx in candidate_indices:
            doc = self.documents[idx]
            if resource_type and doc.resource_type != resource_type:
                continue

            # Normalize base score to 0-1
            raw_score = float(scores[idx]) if idx < len(scores) else 0.0
            base_score = (raw_score - min_score) / score_range if score_range > 0 else 0.0
            
            # Title similarity boost (0-1.0) - STRONG boost
            title_score = self._title_similarity(query, doc.title)
            
            # Tag match boost
            tag_score = 0.0
            query_lower = query.lower()
            query_terms = set(self._tokenize(query))
            for tag in doc.tags:
                if query_lower in tag.lower() or any(t in tag.lower() for t in query_terms if len(t) > 3):
                    tag_score = max(tag_score, 1.0)
                    break
            

            # Relevance gate: full type_boost only if there's a content/title/tag signal
            has_relevance = base_score > 0 or title_score > 0 or tag_score > 0 or (query_lower in doc.title.lower() or doc.title.lower() in query_lower)
            
            if has_relevance:
                if doc.resource_type in ("experiment", "model", "notebook", "dataset"):
                    type_boost = 2.0
                elif doc.resource_type == "document":
                    type_boost = 1.0
                elif doc.resource_type == "configuration":
                    type_boost = 0.5
                else:
                    type_boost = 0.0
            else:
                type_boost = 0.1  # minimal boost for catch-all inclusion
            
            # Penalty for I18N/translation files (source_code with i18n in path)
            i18n_penalty = 0.0
            if doc.resource_type == "source_code" and ("i18n" in doc.repository_relative_path.lower() or 
                                                      "translation" in doc.repository_relative_path.lower()):
                i18n_penalty = 1.5  # Stronger penalty
            
            # Source code penalty: infrastructure source_code should not outrank
            # actual product resources (experiments, models, notebooks, documents).
            # Penalty is larger (1.5) when source_code has relevance because
            # title+tag signals give it a higher baseline to overcome.
            # Penalty is smaller (0.8) when source_code has no relevance
            # (catch-all) because the baseline is near-zero.
            if doc.resource_type == "source_code":
                source_code_penalty = 0.8 if not has_relevance else 1.5
            else:
                source_code_penalty = 0.0
            
            # Title exact match gets massive boost
            title_exact = 1.0 if query_lower in doc.title.lower() or doc.title.lower() in query_lower else 0.0
            title_exact_boost = 1.0 if doc.resource_type == "source_code" else 5.0
            
            # Dynamic title weight: lower for source_code, higher for product resources
            if doc.resource_type == "source_code":
                title_weight = 1.5  # Reduced for source_code
            elif doc.resource_type in ("experiment", "model", "notebook", "dataset"):
                title_weight = 12.0  # Higher for product resources
            elif doc.resource_type in ("document", "configuration"):
                title_weight = 6.0
            else:
                title_weight = 6.0
            
            # Combined score: 
            # - base_score (0-1) * 0.5
            # - title_score (0-1) * dynamic title_weight (1.5 for source_code, 12.0 for product)
            # - tag_score (0-1) * 2.0
            # - type boost (full only if relevance signal exists)
            # - exact title match * dynamic title_exact_boost (1.0 for source_code, 5.0 for product)
            # - i18n penalty
            # - source_code penalty (only when no relevance signal)
            combined = (base_score * 0.5) + (title_score * title_weight) + (tag_score * 2.0) + type_boost + (title_exact * title_exact_boost) - i18n_penalty - source_code_penalty

            # Filter out negative scores
            if combined <= 0:
                continue

            snippet = self._generate_snippet(doc.content, query)
            match_reason = self._match_reason(query, doc)

            results.append(SearchResult(
                document=doc,
                score=combined,
                snippet=snippet,
                match_reason=match_reason,
            ))

        results.sort(key=lambda r: r.score, reverse=True)
        return results[:top_k]

    def _title_similarity(self, query: str, title: str) -> float:
        """Compute similarity between query and title (0-1)."""
        query_lower = query.lower()
        title_lower = title.lower()
        
        # Exact match or substring
        if query_lower in title_lower or title_lower in query_lower:
            return 1.0
        
        # Token overlap
        query_terms = set(self._tokenize(query))
        title_terms = set(self._tokenize(title))
        if not query_terms or not title_terms:
            return 0.0
        overlap = len(query_terms & title_terms)
        return overlap / max(len(query_terms), 1)

    def _match_reason(self, query: str, doc: SearchDocument) -> str:
        """Generate human-readable match reason."""
        query_lower = query.lower()
        title_lower = doc.title.lower()
        
        if query_lower in title_lower:
            return f"title:{query}"
        if any(t in doc.title.lower() for t in self._tokenize(query)):
            return f"title:{query}"
        if any(query_lower in tag.lower() for tag in doc.tags):
            return f"tag:{query}"
        if any(t in doc.title.lower() for t in self._tokenize(query)):
            return f"title:{query}"
        if doc.resource_type in ("experiment", "model", "notebook", "dataset"):
            return f"resource:{doc.resource_type}"
        return f"content:{query}"

    def _generate_snippet(self, content: str, query: str, max_len: int = 200) -> str:
        """Generate a snippet around query match."""
        query_terms = query.lower().split()
        content_lower = content.lower()

        best_pos = -1
        for term in query_terms:
            pos = content_lower.find(term)
            if pos != -1:
                best_pos = pos
                break

        if best_pos == -1:
            return content[:max_len] + '...'

        start = max(0, best_pos - max_len // 2)
        end = min(len(content), start + max_len)
        snippet = content[start:end]
        if start > 0:
            snippet = '...' + snippet
        if end < len(content):
            snippet = snippet + '...'
        return snippet

    def _update_stats(self):
        """Update index statistics."""
        type_counts = {}
        for doc in self.documents:
            type_counts[doc.resource_type] = type_counts.get(doc.resource_type, 0) + 1
        
        self._stats = {
            'total_documents': len(self.documents),
            'resource_types': type_counts,
            'last_indexed': datetime.now().isoformat(),
            'index_status': 'ready' if self._ready else 'stale',
            'fingerprint': self._fingerprint,
        }

    def get_stats(self) -> dict[str, Any]:
        """Get index statistics."""
        if not self._stats:
            self._update_stats()
        return self._stats.copy()


_search_index: SearchIndex | None = None


def get_search_index() -> SearchIndex:
    """Get or create global search index."""
    global _search_index
    if _search_index is None:
        _search_index = SearchIndex()
    return _search_index


def reset_search_index() -> None:
    """Reset global search index."""
    global _search_index
    _search_index = None