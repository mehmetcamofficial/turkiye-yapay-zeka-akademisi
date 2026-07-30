# UCI Sentiment NLP

- Status: implemented English binary sentiment classifier.
- Origin: `5ed3f3a1` (2026-07-21).
- Entry points: `nlp-project/train_model.py`, `app.py`, portfolio NLP page.
- Data: UCI Sentiment Labelled Sentences, 3,000 rows across Amazon, IMDb, and
  Yelp; CC BY 4.0 is documented in the project files.
- Models: TF-IDF with Logistic Regression, LinearSVC, and MultinomialNB;
  MultinomialNB selected.
- Result: accuracy 0.8191 and F1 0.8212.
- UI: text/batch inference, visual analysis, downloadable results.
- Limitations: English-only, small balanced benchmark, domain transfer unknown.
- Evidence: README, DATA_SOURCE, training code, pipeline artifact, outputs.

