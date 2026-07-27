# Contributing to Türkiye Yapay Zeka Akademisi

Thank you for considering a contribution! This is a personal portfolio repository demonstrating engineering rigor in ML and IR systems. While primarily a showcase, improvements are welcome.

---

## 🚀 Getting Started

### Prerequisites
- Python 3.12+
- Git
- 4 GB RAM (8 GB recommended for cross-encoder inference)

### Development Setup
```bash
# Fork and clone
git clone https://github.com/YOUR_USERNAME/turkiye-yapay-zeka-akademisi.git
cd turkiye-yapay-zeka-akademisi

# Virtual environment
python3.12 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r 01-machine-learning/requirements.txt

# Install pre-commit hooks (optional)
pip install pre-commit
pre-commit install
```

### Verify Setup
```bash
# Run full test suite (247 tests)
python -m pytest 01-machine-learning/tests -v

# Launch Streamlit app
python -m streamlit run 01-machine-learning/portfolio_app.py \
  --server.fileWatcherType none --server.headless true
```

---

## 🎯 What Can Be Contributed

### Welcome Contributions
- **Bug fixes** in evaluation metrics (NDCG, MRR, Precision, Recall)
- **Documentation** improvements (README, docstrings, diagrams)
- **Accessibility** enhancements (ARIA, keyboard nav, color contrast)
- **Type hints** and static analysis improvements
- **Test coverage** for edge cases

### Not Accepting
- New ML models or ranking algorithms (research direction is fixed)
- Major architecture redesigns
- Dependency additions without strong justification
- Features that change the "Not Production Promoted" governance model

---

## 📝 Code Style

### Python
- **Formatter**: `black` (line length 100)
- **Linter**: `ruff` (or `flake8` + `isort`)
- **Type hints**: Required for all new functions
- **Imports**: `from __future__ import annotations` at top of every file

```bash
# Format
black 01-machine-learning/

# Lint
ruff check 01-machine-learning/

# Type check (if mypy configured)
mypy 01-machine-learning/
```

### CSS (in `styles.py`)
- Design tokens in `:root` — never hardcode colors/spacing
- Use spacing scale: `--space-1` (4px) through `--space-12` (48px)
- Typography scale: `--font-display` through `--font-xs`
- Respect `prefers-reduced-motion` for all animations
- Test both light and dark modes

### Commit Messages
Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <subject>

<body>

<footer>
```

| Type | Use For |
|------|---------|
| `feat` | New feature |
| `fix` | Bug fix |
| `docs` | Documentation only |
| `style` | Formatting, no logic change |
| `refactor` | Code restructure |
| `perf` | Performance improvement |
| `test` | Adding tests |
| `chore` | Maintenance |

**Examples:**
```
feat(search): add timing indicator to result cards
fix(eval): correct NDCG@10 tie-breaking
docs(readme): add quickstart section
chore(deps): update transformers to 4.48
```

---

## 🧪 Testing Expectations

### Before Submitting
```bash
# Full suite
python -m pytest 01-machine-learning/tests -v

# Specific areas
python -m pytest 01-machine-learning/tests/test_search_evaluation.py -v
python -m pytest 01-machine-learning/tests/test_quality_gate_mutations.py -v
```

### If You Modify Search Logic
```bash
# Start Streamlit on port 8766
python -m streamlit run 01-machine-learning/portfolio_app.py \
  --server.port 8766 --server.headless true

# Run click test
python 01-machine-learning/scripts/test_suggestion_clicks.py
```

### Coverage
- Target: ≥ 90% for new code
- All new public functions must have tests
- Integration tests preferred for UI logic

---

## 🔍 Pull Request Checklist

- [ ] **Tests pass** — `pytest 01-machine-learning/tests -v` shows 247+ passing
- [ ] **Code formatted** — `black` and `ruff` clean
- [ ] **Type hints** — All new functions annotated
- [ ] **Documentation updated** — README, docstrings, or diagrams as needed
- [ ] **No breaking changes** — Or clearly marked in PR description
- [ ] **Screenshots included** — For UI changes (run `scripts/capture_screenshots.py`)
- [ ] **Accessibility verified** — Keyboard nav, color contrast, ARIA labels
- [ ] **Commit messages** — Follow Conventional Commits

---

## 🐛 Issue Reporting

Use the appropriate template:
- **Bug Report** — Incorrect metric calculation, UI glitch, test failure
- **Feature Request** — Documentation enhancement, accessibility, DX improvement
- **Documentation** — Unclear docs, missing diagrams, outdated screenshots

---

## 📜 License

By contributing, you agree that your contributions will be licensed under the [MIT License](LICENSE).

---

## 📞 Questions?

Open a [Discussion](https://github.com/mehmetcamofficial/turkiye-yapay-zeka-akademisi/discussions) or email: mehmet@mehmetcamofficial.com.tr