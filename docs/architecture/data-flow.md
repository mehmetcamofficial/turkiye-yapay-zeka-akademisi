# Data Flow

```text
tracked/external source
  → download or loader
  → validation/cleaning/feature engineering
  → split and train/evaluate
  → persisted model + metadata + reports
  → service loader/cache
  → Streamlit page or offline evaluation
```

Trendyol search adds candidate retrieval → optional classification policy →
optional cross-encoder reranking. Copilot instead indexes allowed repository
files → classifies intent → scores chunks → generates extractive answers →
validates citations.

