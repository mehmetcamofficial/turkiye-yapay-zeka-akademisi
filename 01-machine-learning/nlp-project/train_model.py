"""Offline English sentiment-classification training workflow.

Uses the local UCI Sentiment Labelled Sentences CSV, compares TF-IDF
pipelines, performs stratified CV and tuning without touching the test set,
then saves evaluation, explainability, error-analysis, and model artifacts.
Run: ``python train_model.py``.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from time import perf_counter

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (ConfusionMatrixDisplay, accuracy_score,
                             classification_report, confusion_matrix,
                             f1_score, precision_score, recall_score)
from sklearn.model_selection import GridSearchCV, StratifiedKFold, cross_validate, train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC


BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "data" / "sentiment_dataset.csv"
MODEL_PATH = BASE_DIR / "models" / "nlp_pipeline.pkl"
OUTPUTS_DIR = BASE_DIR / "outputs"
RANDOM_STATE = 42


def clean_text(text: str) -> str:
    """Apply conservative, deterministic cleaning without semantic stemming."""
    value = re.sub(r"<[^>]+>", " ", str(text))
    value = re.sub(r"https?://\S+|www\.\S+", " URL ", value)
    return re.sub(r"\s+", " ", value).strip().lower()


def load_data() -> pd.DataFrame:
    """Read the required local CSV only; no API or runtime download."""
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Missing {DATA_PATH}; run download_data.py once")
    frame = pd.read_csv(DATA_PATH)
    required = {"text", "label", "source"}
    if not required.issubset(frame.columns) or set(frame["label"].dropna()) != {0, 1}:
        raise ValueError("Local sentiment CSV schema or labels are invalid")
    frame = frame.dropna(subset=["text", "label"]).drop_duplicates(subset=["text", "label"]).copy()
    frame["clean_text"] = frame["text"].map(clean_text)
    return frame[frame["clean_text"].str.len() > 0].reset_index(drop=True)


def candidates() -> dict[str, object]:
    return {
        "Logistic Regression": LogisticRegression(max_iter=2000, class_weight="balanced", random_state=RANDOM_STATE),
        "LinearSVC": LinearSVC(class_weight="balanced", random_state=RANDOM_STATE),
        "MultinomialNB": MultinomialNB(),
    }


def make_pipeline(model: object) -> Pipeline:
    return Pipeline([("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=2, max_df=.98,
                                                sublinear_tf=True, max_features=20000)),
                     ("model", model)])


def score_metrics(y_true: pd.Series, prediction: np.ndarray) -> dict[str, float]:
    return {"Accuracy": accuracy_score(y_true, prediction),
            "Precision": precision_score(y_true, prediction, zero_division=0),
            "Recall": recall_score(y_true, prediction, zero_division=0),
            "F1": f1_score(y_true, prediction, zero_division=0)}


def param_grid(name: str) -> dict[str, list]:
    grids = {
        "Logistic Regression": {"tfidf__ngram_range": [(1, 1), (1, 2)], "model__C": [.5, 1, 2]},
        "LinearSVC": {"tfidf__ngram_range": [(1, 1), (1, 2)], "model__C": [.25, .5, 1, 2]},
        "MultinomialNB": {"tfidf__ngram_range": [(1, 1), (1, 2)], "model__alpha": [.25, .5, 1]},
    }
    return grids[name]


def main() -> None:
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True); MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    frame = load_data()
    profile = "\n".join(["UCI SENTIMENT LABELLED SENTENCES DATA PROFILE", "=" * 60,
        f"Shape after exact duplicate removal: {frame.shape[0]} rows x {frame.shape[1]} columns",
        "Language: English", "Sources: Amazon, IMDb, Yelp", "Target: label (0 negative, 1 positive)",
        "License: Creative Commons Attribution 4.0 International (CC BY 4.0)",
        "Original source: https://archive.ics.uci.edu/dataset/331/sentiment+labelled+sentences",
        "\nFirst five rows:\n" + frame[["text", "label", "source"]].head().to_string(index=False),
        "\nMissing values:\n" + frame.isna().sum().to_string(),
        "\nText length statistics:\n" + frame["clean_text"].str.len().describe().to_string(),
        "\nPreprocessing: HTML/URL handling, lowercase and whitespace normalization; TF-IDF is fit inside CV folds."])
    (OUTPUTS_DIR / "data_profile.txt").write_text(profile, encoding="utf-8")
    frame.groupby(["source", "label"]).size().rename("count").reset_index().to_csv(OUTPUTS_DIR / "class_distribution.csv", index=False)

    X_train, X_temp, y_train, y_temp = train_test_split(frame["clean_text"], frame["label"], test_size=.4,
                                                         stratify=frame["label"], random_state=RANDOM_STATE)
    X_val, X_test, y_val, y_test = train_test_split(X_temp, y_temp, test_size=.5,
                                                     stratify=y_temp, random_state=RANDOM_STATE)
    cv = StratifiedKFold(5, shuffle=True, random_state=RANDOM_STATE)
    cv_rows, val_rows = [], []
    for name, estimator in candidates().items():
        pipeline = make_pipeline(estimator)
        result = cross_validate(pipeline, X_train, y_train, cv=cv,
                                scoring={"accuracy": "accuracy", "precision": "precision", "recall": "recall", "f1": "f1"}, n_jobs=-1)
        cv_rows.append({"Model": name, **{f"CV {metric.title()} Mean": result[f"test_{metric}"].mean()
                                             for metric in ("accuracy", "precision", "recall", "f1")},
                        **{f"CV {metric.title()} Std": result[f"test_{metric}"].std()
                           for metric in ("accuracy", "precision", "recall", "f1")}})
        start = perf_counter(); pipeline.fit(X_train, y_train); elapsed = perf_counter() - start
        val_rows.append({"Model": name, **score_metrics(y_val, pipeline.predict(X_val)), "Training Time": elapsed})
    cv_df = pd.DataFrame(cv_rows).sort_values("CV F1 Mean", ascending=False)
    val_df = pd.DataFrame(val_rows).merge(cv_df, on="Model").sort_values(["F1", "CV F1 Mean"], ascending=False)
    cv_df.to_csv(OUTPUTS_DIR / "cross_validation_results.csv", index=False)
    val_df.to_csv(OUTPUTS_DIR / "validation_results.csv", index=False)
    best_name = str(val_df.iloc[0]["Model"])

    search = GridSearchCV(make_pipeline(candidates()[best_name]), param_grid(best_name), scoring="f1", cv=cv,
                          n_jobs=-1, refit=True)
    search.fit(X_train, y_train)
    search_results = pd.DataFrame(search.cv_results_)
    keep = [c for c in search_results if c.startswith("param_") or c in {"mean_test_score", "std_test_score", "rank_test_score"}]
    search_results[keep].to_csv(OUTPUTS_DIR / "hyperparameter_search_results.csv", index=False)
    payload = {"model_name": best_name, "best_cv_f1": search.best_score_, "best_params": search.best_params_,
               "cv_folds": 5, "scoring": "f1"}
    (OUTPUTS_DIR / "best_hyperparameters.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")

    final = make_pipeline(candidates()[best_name]); final.set_params(**search.best_params_)
    final.fit(pd.concat([X_train, X_val]), pd.concat([y_train, y_val]))
    prediction = final.predict(X_test); test = score_metrics(y_test, prediction)
    pd.DataFrame([{"Model": best_name, **test}]).to_csv(OUTPUTS_DIR / "test_metrics.csv", index=False)
    report = classification_report(y_test, prediction, target_names=["Negative", "Positive"], digits=4)
    (OUTPUTS_DIR / "classification_report.txt").write_text(report, encoding="utf-8")
    display = ConfusionMatrixDisplay(confusion_matrix(y_test, prediction), display_labels=["Negative", "Positive"])
    display.plot(values_format="d"); plt.title("Sentiment Test Confusion Matrix"); plt.tight_layout();
    plt.savefig(OUTPUTS_DIR / "confusion_matrix.png", dpi=200); plt.close()
    joblib.dump(final, MODEL_PATH, compress=3)

    vectorizer = final.named_steps["tfidf"]; model = final.named_steps["model"]
    terms = vectorizer.get_feature_names_out()
    if hasattr(model, "coef_"):
        weights = np.asarray(model.coef_).ravel()
    else:
        weights = np.asarray(model.feature_log_prob_[1] - model.feature_log_prob_[0]).ravel()
    top = pd.concat([pd.DataFrame({"term": terms[np.argsort(weights)[-30:][::-1]], "weight": np.sort(weights)[-30:][::-1], "sentiment": "positive"}),
                     pd.DataFrame({"term": terms[np.argsort(weights)[:30]], "weight": np.sort(weights)[:30], "sentiment": "negative"})])
    top.to_csv(OUTPUTS_DIR / "top_terms.csv", index=False)

    errors = frame.loc[X_test.index, ["text", "source"]].copy(); errors["actual"] = y_test; errors["predicted"] = prediction
    errors = errors[errors["actual"] != errors["predicted"]]
    errors["error_type"] = np.where((errors["actual"] == 0) & (errors["predicted"] == 1), "false_positive", "false_negative")
    errors.to_csv(OUTPUTS_DIR / "error_analysis.csv", index=False)
    summary = f"""NLP PROJECT FINAL SUMMARY
Dataset: UCI Sentiment Labelled Sentences; English; CC BY 4.0
Local records used after exact duplicate removal: {len(frame)}
Target: 0 negative, 1 positive; sources: Amazon, IMDb, Yelp
Split: 60% train / 20% validation / 20% untouched test, stratified, random_state=42
Preprocessing: deterministic text cleaning + leakage-safe TF-IDF inside pipeline
Models: {', '.join(candidates())}
Selected model: {best_name}; best parameters: {search.best_params_}
Test metrics: {test}
Limitations: short English review sentences, deliberately no neutral class, domain/source bias, sarcasm/context difficulty, and labels are not causal or production guarantees.
"""
    (OUTPUTS_DIR / "final_summary.txt").write_text(summary, encoding="utf-8")
    print(summary)


if __name__ == "__main__":
    main()
