# Streamlit Architecture

The canonical entry point is `01-machine-learning/portfolio_app.py`. It owns
language and navigation session state and dispatches to modules under
`portfolio/pages/`. Shared loaders use `st.cache_data` and `st.cache_resource`;
services isolate model and search loading from rendering.

Evolution evidence:

- `12a2115e`: modular churn analytics dashboard.
- `7c2c8fd9`: premium bilingual portfolio.
- `2f446237` and `73709a2e`: page separation and runtime fixes.
- `a5101023`: search workspace.
- `3e9be63d`: Project Copilot page.
- `1064814e`: Copilot page integration hotfix.

Limitations include dependence on tracked/ignored model assets and a large page
surface. The rationale for selecting Streamlit is not recorded; author
confirmation is required.

