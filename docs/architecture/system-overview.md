# System Overview

The repository has four interacting layers:

1. Project training/data pipelines persist models and evaluation artifacts.
2. Service modules load bounded artifacts and expose inference/search contracts.
3. `portfolio_app.py` renders a bilingual multi-page Streamlit interface.
4. Search evaluation and Copilot provide repository navigation and grounded
   answers with protected benchmarks.

The data-science tree is adjacent: the portfolio reads its tracked summaries,
inventory, notebook, and governance records without making it a model runtime.

