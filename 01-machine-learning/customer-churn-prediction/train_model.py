"""
Türkiye Yapay Zeka Akademisi — Makine Öğrenmesi Final Ödevi
Customer Churn Prediction (Müşteri Kaybı Tahmini)

Proje amacı
-----------
Telekomünikasyon müşterilerinin hizmetten ayrılma (churn) olasılığını
tahmin eden uçtan uca bir ikili sınıflandırma (binary classification)
pipeline'ı oluşturmak. Model; retention ekiplerinin yüksek riskli
müşterileri erken tespit etmesine yardımcı olacak şekilde tasarlanmıştır.

Problem tipi
------------
İkili sınıflandırma (binary classification):
  - Hedef sütun: "Churn Value"
  - 0 = müşteri kalır
  - 1 = müşteri churn eder

Kullanılan başlıca kütüphaneler
-------------------------------
  - pandas, numpy          : veri işleme
  - scikit-learn           : ön işleme, modelleme, CV, hiperparametre arama
  - matplotlib             : confusion matrix ve ROC eğrisi
  - joblib                 : model kaydetme / yükleme

Eğitim nasıl çalıştırılır
-------------------------
Proje kökünden:

    python 01-machine-learning/customer-churn-prediction/train_model.py

veya proje dizininden:

    python train_model.py

Çıktılar
--------
  models/churn_model.pkl
  outputs/data_profile.txt
  outputs/outlier_analysis.csv
  outputs/selected_features.csv
  outputs/cross_validation_results.csv
  outputs/validation_results.csv
  outputs/hyperparameter_search_results.csv
  outputs/best_hyperparameters.json
  outputs/test_metrics.csv
  outputs/classification_report.txt
  outputs/confusion_matrix.png
  outputs/roc_curve.png
  outputs/feature_importance.csv
  outputs/final_summary.txt

Ön işleme notu
--------------
Eksik değerler sklearn pipeline içinde doldurulur:
  - Sayısal sütunlar  : SimpleImputer(strategy="median")
  - Kategorik sütunlar: SimpleImputer(strategy="most_frequent")
Kategorik kodlama: OneHotEncoder(handle_unknown="ignore")
Tüm adımlar sızıntıyı önlemek için yalnızca eğitim verisine fit edilir.
"""

from __future__ import annotations

import json
from pathlib import Path
from time import perf_counter
from typing import Any

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import (
    GradientBoostingClassifier,
    RandomForestClassifier,
)
from sklearn.feature_selection import SelectFromModel
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    ConfusionMatrixDisplay,
    RocCurveDisplay,
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import (
    GridSearchCV,
    StratifiedKFold,
    cross_validate,
    train_test_split,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.tree import DecisionTreeClassifier


# =============================================================================
# YOLLAR VE SABİTLER
# =============================================================================

BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "data" / "telco_customer_churn.csv"

MODELS_DIR = BASE_DIR / "models"
OUTPUTS_DIR = BASE_DIR / "outputs"

MODEL_PATH = MODELS_DIR / "churn_model.pkl"

DATA_PROFILE_PATH = OUTPUTS_DIR / "data_profile.txt"
OUTLIER_ANALYSIS_PATH = OUTPUTS_DIR / "outlier_analysis.csv"
SELECTED_FEATURES_PATH = OUTPUTS_DIR / "selected_features.csv"
CROSS_VALIDATION_RESULTS_PATH = (
    OUTPUTS_DIR / "cross_validation_results.csv"
)
VALIDATION_RESULTS_PATH = OUTPUTS_DIR / "validation_results.csv"
HYPERPARAMETER_SEARCH_PATH = (
    OUTPUTS_DIR / "hyperparameter_search_results.csv"
)
BEST_HYPERPARAMETERS_PATH = (
    OUTPUTS_DIR / "best_hyperparameters.json"
)
TEST_METRICS_PATH = OUTPUTS_DIR / "test_metrics.csv"
CLASSIFICATION_REPORT_PATH = (
    OUTPUTS_DIR / "classification_report.txt"
)
CONFUSION_MATRIX_PATH = OUTPUTS_DIR / "confusion_matrix.png"
ROC_CURVE_PATH = OUTPUTS_DIR / "roc_curve.png"
FEATURE_IMPORTANCE_PATH = OUTPUTS_DIR / "feature_importance.csv"
FINAL_SUMMARY_PATH = OUTPUTS_DIR / "final_summary.txt"

TARGET_COLUMN = "Churn Value"
RANDOM_STATE = 42
CV_FOLDS = 5

# Domain-based fixed threshold for High Monthly Charge.
# Matches Streamlit inference (app.py). Avoids train/test leakage
# that would occur if the threshold were learned from the full dataset.
HIGH_MONTHLY_CHARGE_THRESHOLD = 70.0

# Outlier analysis focuses on these numeric billing/tenure fields.
OUTLIER_COLUMNS = [
    "Tenure Months",
    "Monthly Charges",
    "Total Charges",
    "Average Monthly Spend",
]


# =============================================================================
# DİZİN VE VERİ YÜKLEME
# =============================================================================

def create_output_directories() -> None:
    """Create model and output directories when necessary."""

    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)


def load_data() -> pd.DataFrame:
    """Load the customer churn dataset."""

    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"Veri dosyası bulunamadı: {DATA_PATH}"
        )

    return pd.read_csv(DATA_PATH, sep=";")


def convert_numeric_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Convert text-based numeric columns into numeric values.

    European-style decimals (comma) are converted to dots before
    coercing to float. Invalid values become NaN and are later
    imputed inside the sklearn pipeline (median for numeric columns).
    """

    df = df.copy()

    numeric_text_columns = [
        "Monthly Charges",
        "Total Charges",
        "Latitude",
        "Longitude",
    ]

    for column in numeric_text_columns:
        if column not in df.columns:
            continue

        df[column] = (
            df[column]
            .astype(str)
            .str.replace(",", ".", regex=False)
            .str.strip()
        )
        df[column] = pd.to_numeric(df[column], errors="coerce")

    return df


# =============================================================================
# EDA
# =============================================================================

def run_exploratory_data_analysis(
    raw_df: pd.DataFrame,
    cleaned_df: pd.DataFrame,
) -> dict[str, Any]:
    """Produce a human-readable EDA report and return key stats.

    Saved to outputs/data_profile.txt:
      - first five rows
      - dataset shape
      - column names
      - data types
      - descriptive statistics
      - missing-value counts
      - target distribution
    """

    profile_df = convert_numeric_columns(raw_df)

    target_counts = cleaned_df[TARGET_COLUMN].value_counts().sort_index()
    target_ratio = cleaned_df[TARGET_COLUMN].value_counts(
        normalize=True
    ).sort_index()

    missing_counts = profile_df.isna().sum().sort_values(ascending=False)
    missing_after_clean = cleaned_df.isna().sum().sort_values(
        ascending=False
    )

    lines: list[str] = []
    lines.append("=" * 72)
    lines.append("CUSTOMER CHURN — EXPLORATORY DATA ANALYSIS")
    lines.append("=" * 72)
    lines.append("")
    lines.append("1. FIRST FIVE ROWS (raw, after numeric conversion)")
    lines.append("-" * 72)
    lines.append(profile_df.head(5).to_string())
    lines.append("")
    lines.append("2. DATASET SHAPE")
    lines.append("-" * 72)
    lines.append(
        f"Raw shape     : {raw_df.shape[0]} rows x {raw_df.shape[1]} columns"
    )
    lines.append(
        f"Cleaned shape : {cleaned_df.shape[0]} rows x "
        f"{cleaned_df.shape[1]} columns"
    )
    lines.append("")
    lines.append("3. COLUMN NAMES (raw)")
    lines.append("-" * 72)
    for name in raw_df.columns.tolist():
        lines.append(f"  - {name}")
    lines.append("")
    lines.append("4. DATA TYPES (raw, after numeric conversion)")
    lines.append("-" * 72)
    lines.append(profile_df.dtypes.astype(str).to_string())
    lines.append("")
    lines.append("5. DESCRIPTIVE STATISTICS (numeric columns)")
    lines.append("-" * 72)
    lines.append(profile_df.describe(include="all").to_string())
    lines.append("")
    lines.append("6. MISSING-VALUE COUNTS (raw / after numeric conversion)")
    lines.append("-" * 72)
    lines.append(missing_counts.to_string())
    lines.append("")
    lines.append(
        "   Missing values after cleaning / feature engineering "
        "(before pipeline imputation):"
    )
    lines.append(missing_after_clean.to_string())
    lines.append("")
    lines.append(
        "   Imputation strategy (applied inside sklearn pipeline, "
        "fit on training data only):"
    )
    lines.append("     - Numeric columns     : median")
    lines.append("     - Categorical columns : most frequent")
    lines.append("")
    lines.append("7. TARGET DISTRIBUTION (Churn Value)")
    lines.append("-" * 72)
    for label in target_counts.index:
        count = int(target_counts.loc[label])
        ratio = float(target_ratio.loc[label])
        label_name = "No Churn" if int(label) == 0 else "Churn"
        lines.append(
            f"  {label} ({label_name}): {count} "
            f"({ratio * 100:.2f}%)"
        )
    lines.append("")
    lines.append(
        "Note: Class imbalance is present; class_weight='balanced' "
        "is used where supported."
    )
    lines.append("")
    lines.append("=" * 72)
    lines.append("END OF DATA PROFILE")
    lines.append("=" * 72)

    report_text = "\n".join(lines)
    DATA_PROFILE_PATH.write_text(report_text, encoding="utf-8")

    return {
        "raw_shape": raw_df.shape,
        "cleaned_shape": cleaned_df.shape,
        "target_counts": target_counts.to_dict(),
        "target_ratio": {
            int(k): float(v) for k, v in target_ratio.items()
        },
        "missing_counts": missing_counts.to_dict(),
    }


# =============================================================================
# ÖZELLİK MÜHENDİSLİĞİ VE TEMİZLEME
# =============================================================================

def create_features(df: pd.DataFrame) -> pd.DataFrame:
    """Create additional customer behavior features.

    Engineered features (no target used):
      - Average Monthly Spend
      - Is Long Term Customer
      - Has Support Services
      - High Monthly Charge  (fixed domain threshold = 70)

    High Monthly Charge uses a fixed threshold rather than a
    dataset-wide median so that train/validation/test and Streamlit
    inference apply exactly the same rule without leakage.
    """

    df = df.copy()

    df["Average Monthly Spend"] = np.where(
        df["Tenure Months"] > 0,
        df["Total Charges"] / df["Tenure Months"],
        df["Monthly Charges"],
    )

    df["Is Long Term Customer"] = (
        df["Tenure Months"] >= 24
    ).astype(int)

    df["Has Support Services"] = (
        (df["Tech Support"] == "Yes")
        | (df["Online Security"] == "Yes")
    ).astype(int)

    df["High Monthly Charge"] = (
        df["Monthly Charges"] > HIGH_MONTHLY_CHARGE_THRESHOLD
    ).astype(int)

    return df


def remove_unnecessary_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Remove identifiers, location data and leakage columns.

    Leakage columns removed:
      - Churn Label  (text form of the target)
      - Churn Score  (post-hoc score correlated with churn)
      - Churn Reason (only available after churn occurs)
    """

    columns_to_drop = [
        # Identifiers
        "CustomerID",
        "Count",
        # Location fields
        "Country",
        "State",
        "City",
        "Zip Code",
        "Lat Long",
        "Latitude",
        "Longitude",
        # Target leakage
        "Churn Label",
        "Churn Score",
        "Churn Reason",
    ]

    return df.drop(columns=columns_to_drop, errors="ignore")


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """Apply the complete cleaning and feature engineering workflow."""

    df = convert_numeric_columns(df)
    df = create_features(df)
    df = remove_unnecessary_columns(df)
    return df


# =============================================================================
# AYKIRI DEĞER ANALİZİ
# =============================================================================

def analyze_outliers(df: pd.DataFrame) -> pd.DataFrame:
    """IQR-based outlier analysis for key numeric columns.

    Outliers are NOT deleted. Legitimate extreme values (e.g. long
    tenure, high total charges) can represent valid customer behaviour.
    Results are saved for transparency; no automatic row removal is
    applied. Pipeline uses median imputation + scaling, which is robust
    to moderate outliers without discarding customers.
    """

    rows: list[dict[str, Any]] = []

    for column in OUTLIER_COLUMNS:
        if column not in df.columns:
            continue

        series = pd.to_numeric(df[column], errors="coerce").dropna()
        if series.empty:
            continue

        q1 = float(series.quantile(0.25))
        q3 = float(series.quantile(0.75))
        iqr = q3 - q1
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr

        outlier_mask = (series < lower) | (series > upper)
        outlier_count = int(outlier_mask.sum())
        total_count = int(len(series))
        outlier_ratio = (
            outlier_count / total_count if total_count else 0.0
        )

        rows.append(
            {
                "column": column,
                "count": total_count,
                "mean": float(series.mean()),
                "std": float(series.std(ddof=1)) if total_count > 1 else 0.0,
                "min": float(series.min()),
                "q1": q1,
                "median": float(series.median()),
                "q3": q3,
                "max": float(series.max()),
                "iqr": iqr,
                "lower_bound": lower,
                "upper_bound": upper,
                "outlier_count": outlier_count,
                "outlier_ratio": outlier_ratio,
                "treatment": (
                    "retained — valid customer behaviour; "
                    "no automatic deletion; "
                    "median imputation + scaling in pipeline"
                ),
            }
        )

    outlier_df = pd.DataFrame(rows)
    outlier_df.to_csv(OUTLIER_ANALYSIS_PATH, index=False)
    return outlier_df


# =============================================================================
# VERİ BÖLME
# =============================================================================

def split_data(
    df: pd.DataFrame,
) -> tuple[
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
    pd.Series,
    pd.Series,
    pd.Series,
]:
    """Split the dataset into 60% train / 20% validation / 20% test.

    Stratified on the target. random_state=42.
    The test set remains untouched until final evaluation.
    """

    if TARGET_COLUMN not in df.columns:
        raise KeyError(f"Hedef sütun bulunamadı: {TARGET_COLUMN}")

    X = df.drop(columns=[TARGET_COLUMN])
    y = df[TARGET_COLUMN]

    X_train, X_temp, y_train, y_temp = train_test_split(
        X,
        y,
        test_size=0.40,
        random_state=RANDOM_STATE,
        stratify=y,
    )

    X_validation, X_test, y_validation, y_test = train_test_split(
        X_temp,
        y_temp,
        test_size=0.50,
        random_state=RANDOM_STATE,
        stratify=y_temp,
    )

    return (
        X_train,
        X_validation,
        X_test,
        y_train,
        y_validation,
        y_test,
    )


# =============================================================================
# PREPROCESSING + FEATURE SELECTION PIPELINE
# =============================================================================

def build_preprocessor(X: pd.DataFrame) -> ColumnTransformer:
    """Build numeric and categorical preprocessing pipelines.

    Missing-value handling (fit only on training folds):
      - Numeric     : SimpleImputer(strategy="median")
      - Categorical : SimpleImputer(strategy="most_frequent")

    Encoding:
      - OneHotEncoder(handle_unknown="ignore", sparse_output=False)

    Scaling:
      - StandardScaler for numeric features (helps linear models).
    """

    numeric_columns = (
        X.select_dtypes(include=["number"]).columns.tolist()
    )
    categorical_columns = (
        X.select_dtypes(exclude=["number"]).columns.tolist()
    )

    numeric_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )

    categorical_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            (
                "encoder",
                OneHotEncoder(
                    handle_unknown="ignore",
                    sparse_output=False,
                ),
            ),
        ]
    )

    return ColumnTransformer(
        transformers=[
            ("numeric", numeric_pipeline, numeric_columns),
            ("categorical", categorical_pipeline, categorical_columns),
        ],
        remainder="drop",
    )


def build_feature_selector() -> SelectFromModel:
    """L1-regularized Logistic Regression feature selector.

    Placed after preprocessing so it operates on the fully encoded
    feature matrix. Fitted only on training data / CV folds to avoid
    leakage.
    """

    selector_estimator = LogisticRegression(
        penalty="l1",
        solver="liblinear",
        C=0.5,
        class_weight="balanced",
        max_iter=2000,
        random_state=RANDOM_STATE,
    )

    return SelectFromModel(
        estimator=selector_estimator,
        threshold="median",
        prefit=False,
    )


def create_models() -> dict[str, object]:
    """Create candidate classification models."""

    return {
        "Logistic Regression": LogisticRegression(
            max_iter=2000,
            class_weight="balanced",
            random_state=RANDOM_STATE,
        ),
        "Decision Tree": DecisionTreeClassifier(
            max_depth=8,
            min_samples_split=20,
            min_samples_leaf=10,
            class_weight="balanced",
            random_state=RANDOM_STATE,
        ),
        "Random Forest": RandomForestClassifier(
            n_estimators=300,
            max_depth=12,
            min_samples_split=10,
            min_samples_leaf=4,
            class_weight="balanced",
            random_state=RANDOM_STATE,
            n_jobs=-1,
        ),
        "Gradient Boosting": GradientBoostingClassifier(
            n_estimators=150,
            learning_rate=0.05,
            max_depth=3,
            random_state=RANDOM_STATE,
        ),
    }


def create_model_pipeline(
    X: pd.DataFrame,
    model: object,
) -> Pipeline:
    """Create preprocessing + feature selection + model pipeline."""

    return Pipeline(
        steps=[
            ("preprocessor", build_preprocessor(X)),
            ("feature_selection", build_feature_selector()),
            ("model", model),
        ]
    )


def get_model_by_name(model_name: str) -> object:
    """Return a new model instance by model name."""

    models = create_models()
    if model_name not in models:
        raise KeyError(f"Model bulunamadı: {model_name}")
    return models[model_name]


# =============================================================================
# METRİKLER
# =============================================================================

def calculate_metrics(
    y_true: pd.Series,
    y_prediction: np.ndarray,
    y_probability: np.ndarray,
) -> dict[str, float]:
    """Calculate binary classification metrics."""

    return {
        "Accuracy": accuracy_score(y_true, y_prediction),
        "Precision": precision_score(
            y_true, y_prediction, zero_division=0
        ),
        "Recall": recall_score(
            y_true, y_prediction, zero_division=0
        ),
        "F1 Score": f1_score(
            y_true, y_prediction, zero_division=0
        ),
        "ROC AUC": roc_auc_score(y_true, y_probability),
    }


# =============================================================================
# ÇAPRAZ DOĞRULAMA
# =============================================================================

def run_cross_validation(
    X_train: pd.DataFrame,
    y_train: pd.Series,
) -> pd.DataFrame:
    """5-fold stratified CV on the training set for each candidate model.

    Reports mean/std of ROC AUC and F1. The test set is never used here.
    """

    cv = StratifiedKFold(
        n_splits=CV_FOLDS,
        shuffle=True,
        random_state=RANDOM_STATE,
    )

    scoring = {
        "roc_auc": "roc_auc",
        "f1": "f1",
    }

    rows: list[dict[str, Any]] = []

    for model_name, model in create_models().items():
        print(f"\n[CV] {model_name} — {CV_FOLDS}-fold StratifiedKFold...")

        pipeline = create_model_pipeline(X=X_train, model=model)

        cv_results = cross_validate(
            pipeline,
            X_train,
            y_train,
            cv=cv,
            scoring=scoring,
            n_jobs=-1,
            return_train_score=False,
        )

        row = {
            "Model": model_name,
            "CV ROC AUC Mean": float(np.mean(cv_results["test_roc_auc"])),
            "CV ROC AUC Std": float(np.std(cv_results["test_roc_auc"])),
            "CV F1 Mean": float(np.mean(cv_results["test_f1"])),
            "CV F1 Std": float(np.std(cv_results["test_f1"])),
        }
        rows.append(row)

        print(
            f"  ROC AUC: {row['CV ROC AUC Mean']:.4f} "
            f"(±{row['CV ROC AUC Std']:.4f}) | "
            f"F1: {row['CV F1 Mean']:.4f} "
            f"(±{row['CV F1 Std']:.4f})"
        )

    cv_df = (
        pd.DataFrame(rows)
        .sort_values(
            by=["CV ROC AUC Mean", "CV F1 Mean"],
            ascending=False,
        )
        .reset_index(drop=True)
    )
    cv_df.to_csv(CROSS_VALIDATION_RESULTS_PATH, index=False)
    return cv_df


# =============================================================================
# DOĞRULAMA KARŞILAŞTIRMASI
# =============================================================================

def train_and_compare_models(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_validation: pd.DataFrame,
    y_validation: pd.Series,
    cv_results: pd.DataFrame,
) -> pd.DataFrame:
    """Train candidate models, evaluate on validation, merge CV metrics.

    Model selection uses training CV + validation performance.
    The test set is not touched.
    """

    results: list[dict[str, Any]] = []
    cv_lookup = cv_results.set_index("Model")

    for model_name, model in create_models().items():
        print(f"\n[Validation] {model_name} eğitiliyor...")

        pipeline = create_model_pipeline(X=X_train, model=model)

        start_time = perf_counter()
        pipeline.fit(X_train, y_train)
        training_time = perf_counter() - start_time

        validation_prediction = pipeline.predict(X_validation)
        validation_probability = pipeline.predict_proba(X_validation)[:, 1]

        metrics = calculate_metrics(
            y_true=y_validation,
            y_prediction=validation_prediction,
            y_probability=validation_probability,
        )

        cv_roc_mean = float(cv_lookup.loc[model_name, "CV ROC AUC Mean"])
        cv_roc_std = float(cv_lookup.loc[model_name, "CV ROC AUC Std"])
        cv_f1_mean = float(cv_lookup.loc[model_name, "CV F1 Mean"])
        cv_f1_std = float(cv_lookup.loc[model_name, "CV F1 Std"])

        results.append(
            {
                "Model": model_name,
                **metrics,
                "Training Time": training_time,
                "CV ROC AUC Mean": cv_roc_mean,
                "CV ROC AUC Std": cv_roc_std,
                "CV F1 Mean": cv_f1_mean,
                "CV F1 Std": cv_f1_std,
            }
        )

        print(
            f"{model_name} tamamlandı. "
            f"Val F1: {metrics['F1 Score']:.4f} | "
            f"Val ROC AUC: {metrics['ROC AUC']:.4f} | "
            f"CV ROC AUC: {cv_roc_mean:.4f}"
        )

    results_df = (
        pd.DataFrame(results)
        .sort_values(
            by=["ROC AUC", "CV ROC AUC Mean", "F1 Score"],
            ascending=False,
        )
        .reset_index(drop=True)
    )
    results_df.to_csv(VALIDATION_RESULTS_PATH, index=False)
    return results_df


# =============================================================================
# HİPERPARAMETRE AYARI
# =============================================================================

def get_param_grid(model_name: str) -> dict[str, list[Any]]:
    """Return a meaningful but compact parameter grid for the selected model."""

    if model_name == "Logistic Regression":
        return {
            "model__C": [0.1, 0.5, 1.0, 2.0],
            "model__class_weight": ["balanced", None],
            "model__solver": ["lbfgs", "liblinear"],
        }

    if model_name == "Random Forest":
        return {
            "model__n_estimators": [200, 300],
            "model__max_depth": [8, 12, None],
            "model__min_samples_split": [5, 10],
            "model__min_samples_leaf": [2, 4],
            "model__class_weight": ["balanced", "balanced_subsample"],
        }

    if model_name == "Decision Tree":
        return {
            "model__max_depth": [4, 6, 8, 12],
            "model__min_samples_split": [10, 20, 40],
            "model__min_samples_leaf": [5, 10, 20],
            "model__class_weight": ["balanced", None],
        }

    if model_name == "Gradient Boosting":
        return {
            "model__n_estimators": [100, 150, 200],
            "model__learning_rate": [0.05, 0.1],
            "model__max_depth": [2, 3, 4],
        }

    raise KeyError(f"Parametre ızgarası tanımlı değil: {model_name}")


def tune_hyperparameters(
    model_name: str,
    X_train: pd.DataFrame,
    y_train: pd.Series,
) -> tuple[Pipeline, dict[str, Any], pd.DataFrame]:
    """GridSearchCV on the training set for the selected best model.

    - StratifiedKFold with 5 folds
    - scoring="roc_auc"
    - n_jobs=-1
    - refit=True
    - Test set is never used during tuning
    """

    base_model = get_model_by_name(model_name)
    pipeline = create_model_pipeline(X=X_train, model=base_model)
    param_grid = get_param_grid(model_name)

    cv = StratifiedKFold(
        n_splits=CV_FOLDS,
        shuffle=True,
        random_state=RANDOM_STATE,
    )

    print(f"\n[Tuning] {model_name} — GridSearchCV (scoring=roc_auc)...")

    search = GridSearchCV(
        estimator=pipeline,
        param_grid=param_grid,
        scoring="roc_auc",
        cv=cv,
        n_jobs=-1,
        refit=True,
        return_train_score=False,
        verbose=1,
    )
    search.fit(X_train, y_train)

    results_df = pd.DataFrame(search.cv_results_)
    # Keep a readable subset of columns
    keep_cols = [
        col
        for col in results_df.columns
        if col.startswith("param_")
        or col
        in {
            "mean_test_score",
            "std_test_score",
            "rank_test_score",
            "mean_fit_time",
            "std_fit_time",
        }
    ]
    results_df = results_df[keep_cols].sort_values(
        by="rank_test_score"
    ).reset_index(drop=True)
    results_df.to_csv(HYPERPARAMETER_SEARCH_PATH, index=False)

    best_params = {
        key: (
            value
            if not isinstance(value, (np.integer, np.floating))
            else value.item()
        )
        for key, value in search.best_params_.items()
    }
    best_payload = {
        "model_name": model_name,
        "best_score_roc_auc": float(search.best_score_),
        "best_params": best_params,
        "cv_folds": CV_FOLDS,
        "scoring": "roc_auc",
        "search_method": "GridSearchCV",
    }
    BEST_HYPERPARAMETERS_PATH.write_text(
        json.dumps(best_payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(
        f"  En iyi CV ROC AUC: {search.best_score_:.4f}\n"
        f"  En iyi parametreler: {best_params}"
    )

    return search.best_estimator_, best_payload, results_df


# =============================================================================
# FİNAL EĞİTİM
# =============================================================================

def retrain_final_pipeline(
    model_name: str,
    best_params: dict[str, Any],
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_validation: pd.DataFrame,
    y_validation: pd.Series,
) -> Pipeline:
    """Build a fresh pipeline with best params and fit on train + validation.

    Hyperparameters come from GridSearchCV on training data only.
    The test set is not used during tuning or this retrain step.
    """

    X_combined = pd.concat([X_train, X_validation], axis=0)
    y_combined = pd.concat([y_train, y_validation], axis=0)

    base_model = get_model_by_name(model_name)
    pipeline = create_model_pipeline(X=X_combined, model=base_model)
    pipeline.set_params(**best_params)
    pipeline.fit(X_combined, y_combined)
    return pipeline


# =============================================================================
# SEÇİLEN ÖZELLİKLER VE AÇIKLANABİLİRLİK
# =============================================================================

def extract_transformed_feature_names(pipeline: Pipeline) -> list[str]:
    """Return feature names after preprocessing (before selection)."""

    preprocessor: ColumnTransformer = pipeline.named_steps["preprocessor"]
    return list(preprocessor.get_feature_names_out())


def save_selected_features(pipeline: Pipeline) -> pd.DataFrame:
    """Save the features retained by SelectFromModel."""

    all_features = extract_transformed_feature_names(pipeline)
    selector: SelectFromModel = pipeline.named_steps["feature_selection"]
    support = selector.get_support()

    selected = [
        name for name, keep in zip(all_features, support) if keep
    ]
    rejected = [
        name for name, keep in zip(all_features, support) if not keep
    ]

    rows = (
        [{"feature": name, "selected": True} for name in selected]
        + [{"feature": name, "selected": False} for name in rejected]
    )
    selected_df = pd.DataFrame(rows)
    selected_df.to_csv(SELECTED_FEATURES_PATH, index=False)
    return selected_df


def save_feature_importance(
    pipeline: Pipeline,
    model_name: str,
) -> pd.DataFrame:
    """Extract coefficients or importances for model interpretation.

    For Logistic Regression: coefficients of selected features.
    Positive coefficients increase predicted churn log-odds;
    negative coefficients decrease them.
    Association is not causation.
    """

    all_features = extract_transformed_feature_names(pipeline)
    selector: SelectFromModel = pipeline.named_steps["feature_selection"]
    support = selector.get_support()
    selected_features = [
        name for name, keep in zip(all_features, support) if keep
    ]

    model = pipeline.named_steps["model"]
    rows: list[dict[str, Any]] = []

    if hasattr(model, "coef_"):
        coefficients = np.asarray(model.coef_).ravel()
        for feature_name, coefficient in zip(
            selected_features, coefficients
        ):
            rows.append(
                {
                    "feature": feature_name,
                    "importance": float(coefficient),
                    "abs_importance": float(abs(coefficient)),
                    "direction": (
                        "increases_churn_risk"
                        if coefficient > 0
                        else (
                            "decreases_churn_risk"
                            if coefficient < 0
                            else "neutral"
                        )
                    ),
                    "method": "logistic_regression_coefficient",
                }
            )
    elif hasattr(model, "feature_importances_"):
        importances = np.asarray(model.feature_importances_).ravel()
        for feature_name, importance in zip(
            selected_features, importances
        ):
            rows.append(
                {
                    "feature": feature_name,
                    "importance": float(importance),
                    "abs_importance": float(abs(importance)),
                    "direction": "relative_contribution",
                    "method": "tree_feature_importance",
                }
            )
    else:
        rows.append(
            {
                "feature": "N/A",
                "importance": 0.0,
                "abs_importance": 0.0,
                "direction": "unavailable",
                "method": "unsupported_model",
            }
        )

    importance_df = (
        pd.DataFrame(rows)
        .sort_values(by="abs_importance", ascending=False)
        .reset_index(drop=True)
    )
    importance_df.to_csv(FEATURE_IMPORTANCE_PATH, index=False)
    return importance_df


# =============================================================================
# TEST DEĞERLENDİRMESİ
# =============================================================================

def save_confusion_matrix(
    y_test: pd.Series,
    y_prediction: np.ndarray,
) -> None:
    """Save the test confusion matrix plot."""

    matrix = confusion_matrix(y_test, y_prediction)
    display = ConfusionMatrixDisplay(
        confusion_matrix=matrix,
        display_labels=["No Churn", "Churn"],
    )
    display.plot(values_format="d")
    plt.title("Test Set Confusion Matrix")
    plt.tight_layout()
    plt.savefig(CONFUSION_MATRIX_PATH, dpi=300, bbox_inches="tight")
    plt.close()


def save_roc_curve(
    y_test: pd.Series,
    y_probability: np.ndarray,
) -> None:
    """Save the ROC curve for the final model."""

    RocCurveDisplay.from_predictions(
        y_test,
        y_probability,
        name="Final Model",
    )
    plt.title("Test Set ROC Curve")
    plt.tight_layout()
    plt.savefig(ROC_CURVE_PATH, dpi=300, bbox_inches="tight")
    plt.close()


def save_classification_report(
    y_test: pd.Series,
    y_prediction: np.ndarray,
) -> str:
    """Save a detailed classification report and return the text."""

    report = classification_report(
        y_test,
        y_prediction,
        target_names=["No Churn", "Churn"],
        digits=4,
        zero_division=0,
    )
    CLASSIFICATION_REPORT_PATH.write_text(report, encoding="utf-8")
    return report


def evaluate_final_model(
    final_pipeline: Pipeline,
    X_test: pd.DataFrame,
    y_test: pd.Series,
) -> dict[str, float]:
    """Evaluate the final model once on the untouched test set."""

    test_prediction = final_pipeline.predict(X_test)
    test_probability = final_pipeline.predict_proba(X_test)[:, 1]

    metrics = calculate_metrics(
        y_true=y_test,
        y_prediction=test_prediction,
        y_probability=test_probability,
    )

    save_confusion_matrix(y_test=y_test, y_prediction=test_prediction)
    save_roc_curve(y_test=y_test, y_probability=test_probability)
    save_classification_report(
        y_test=y_test, y_prediction=test_prediction
    )

    return metrics


# =============================================================================
# RAPORLAMA
# =============================================================================

def print_validation_results(results_df: pd.DataFrame) -> None:
    """Print the validation comparison table."""

    display_df = results_df.copy()
    numeric_columns = [
        col
        for col in display_df.columns
        if col != "Model" and pd.api.types.is_numeric_dtype(display_df[col])
    ]
    display_df[numeric_columns] = display_df[numeric_columns].round(4)

    print("\n" + "=" * 100)
    print("DOĞRULAMA KÜMESİ MODEL KARŞILAŞTIRMASI (+ CV ÖZETİ)")
    print("=" * 100)
    print(display_df.to_string(index=False))


def print_test_results(
    best_model_name: str,
    test_metrics: dict[str, float],
) -> None:
    """Print final test performance."""

    print("\n" + "=" * 70)
    print("SON TEST SONUÇLARI")
    print("=" * 70)
    print(f"Seçilen model : {best_model_name}")
    for metric_name, metric_value in test_metrics.items():
        print(f"{metric_name:<12}: {metric_value:.4f}")


def write_final_summary(
    *,
    raw_shape: tuple[int, int],
    cleaned_shape: tuple[int, int],
    target_counts: dict[Any, Any],
    target_ratio: dict[int, float],
    outlier_df: pd.DataFrame,
    cv_results: pd.DataFrame,
    validation_results: pd.DataFrame,
    best_model_name: str,
    best_hyperparameters: dict[str, Any],
    test_metrics: dict[str, float],
    importance_df: pd.DataFrame,
    selected_df: pd.DataFrame,
    train_size: int,
    validation_size: int,
    test_size: int,
) -> None:
    """Write the comprehensive final summary report."""

    selected_count = int(selected_df["selected"].sum()) if not selected_df.empty else 0
    total_encoded = int(len(selected_df)) if not selected_df.empty else 0

    top_positive = importance_df[
        importance_df["direction"] == "increases_churn_risk"
    ].head(5)
    top_negative = importance_df[
        importance_df["direction"] == "decreases_churn_risk"
    ].head(5)
    top_any = importance_df.head(10)

    lines: list[str] = []
    lines.append("=" * 72)
    lines.append("CUSTOMER CHURN PREDICTION — FINAL SUMMARY REPORT")
    lines.append("Türkiye Yapay Zeka Akademisi · Makine Öğrenmesi Final Ödevi")
    lines.append("=" * 72)
    lines.append("")
    lines.append("1. PROBLEM TYPE")
    lines.append("-" * 72)
    lines.append(
        "Binary classification (ikili sınıflandırma). "
        "Target: Churn Value (0 = No Churn, 1 = Churn)."
    )
    lines.append("")
    lines.append("2. DATASET DIMENSIONS")
    lines.append("-" * 72)
    lines.append(
        f"Raw dataset      : {raw_shape[0]} rows x {raw_shape[1]} columns"
    )
    lines.append(
        f"Cleaned dataset  : {cleaned_shape[0]} rows x "
        f"{cleaned_shape[1]} columns"
    )
    lines.append(
        f"Train / Val / Test sizes: "
        f"{train_size} / {validation_size} / {test_size} "
        f"(approx. 60% / 20% / 20%, stratified, random_state=42)"
    )
    lines.append("")
    lines.append("3. TARGET DISTRIBUTION")
    lines.append("-" * 72)
    for label, count in sorted(target_counts.items(), key=lambda x: int(x[0])):
        ratio = target_ratio.get(int(label), 0.0)
        name = "No Churn" if int(label) == 0 else "Churn"
        lines.append(
            f"  {label} ({name}): {int(count)} ({ratio * 100:.2f}%)"
        )
    lines.append("")
    lines.append("4. PREPROCESSING SUMMARY")
    lines.append("-" * 72)
    lines.append(
        "- Leakage columns removed: Churn Label, Churn Score, Churn Reason"
    )
    lines.append(
        "- Identifiers and location fields removed "
        "(CustomerID, City, Zip Code, Lat/Long, ...)"
    )
    lines.append(
        "- Missing values handled inside sklearn Pipeline "
        "(fit on training data only):"
    )
    lines.append("    * Numeric     : median imputation + StandardScaler")
    lines.append(
        "    * Categorical : most-frequent imputation + "
        "OneHotEncoder(handle_unknown='ignore')"
    )
    lines.append(
        "- Outliers (IQR analysis on Tenure Months, Monthly Charges, "
        "Total Charges, Average Monthly Spend) are RETAINED because "
        "they may represent valid customer behaviour. No automatic "
        "row deletion is applied."
    )
    if not outlier_df.empty:
        lines.append("  Outlier summary:")
        for _, row in outlier_df.iterrows():
            lines.append(
                f"    * {row['column']}: "
                f"{int(row['outlier_count'])} outliers "
                f"({float(row['outlier_ratio']) * 100:.2f}%)"
            )
    lines.append("")
    lines.append("5. ENGINEERED FEATURES")
    lines.append("-" * 72)
    lines.append("  - Average Monthly Spend = Total Charges / Tenure Months")
    lines.append("    (fallback: Monthly Charges when tenure is 0)")
    lines.append("  - Is Long Term Customer = 1 if Tenure Months >= 24")
    lines.append(
        "  - Has Support Services = 1 if Tech Support or Online Security is Yes"
    )
    lines.append(
        f"  - High Monthly Charge = 1 if Monthly Charges > "
        f"{HIGH_MONTHLY_CHARGE_THRESHOLD} "
        "(fixed domain threshold; no dataset-wide statistic leakage)"
    )
    lines.append("  No engineered feature uses the target variable.")
    lines.append("")
    lines.append("6. FEATURE SELECTION")
    lines.append("-" * 72)
    lines.append(
        "Method: SelectFromModel with L1-regularized LogisticRegression "
        "(penalty='l1', solver='liblinear', threshold='median')."
    )
    lines.append(
        "Placed inside the sklearn pipeline after preprocessing so that "
        "selection is fit only on training folds (no leakage)."
    )
    lines.append(
        f"Selected features after encoding: {selected_count} / {total_encoded}"
    )
    lines.append(f"Report: {SELECTED_FEATURES_PATH.name}")
    lines.append("")
    lines.append("7. CANDIDATE MODELS")
    lines.append("-" * 72)
    lines.append("  - Logistic Regression")
    lines.append("  - Decision Tree")
    lines.append("  - Random Forest")
    lines.append("  - Gradient Boosting")
    lines.append("")
    lines.append("8. CROSS-VALIDATION RESULTS (train set only)")
    lines.append("-" * 72)
    lines.append(
        cv_results.round(4).to_string(index=False)
        if not cv_results.empty
        else "  (no results)"
    )
    lines.append("")
    lines.append("9. SELECTED MODEL")
    lines.append("-" * 72)
    lines.append(
        f"Selected model: {best_model_name} "
        "(based on validation ROC AUC and CV ROC AUC; test set untouched)."
    )
    lines.append("")
    lines.append("10. BEST HYPERPARAMETERS")
    lines.append("-" * 72)
    lines.append(json.dumps(best_hyperparameters, indent=2, ensure_ascii=False))
    lines.append("")
    lines.append("11. VALIDATION PERFORMANCE")
    lines.append("-" * 72)
    lines.append(
        validation_results.round(4).to_string(index=False)
        if not validation_results.empty
        else "  (no results)"
    )
    lines.append("")
    lines.append("12. TEST PERFORMANCE (single final evaluation)")
    lines.append("-" * 72)
    for metric_name, metric_value in test_metrics.items():
        lines.append(f"  {metric_name:<12}: {metric_value:.4f}")
    lines.append("")
    lines.append("13. IMPORTANT FEATURES")
    lines.append("-" * 72)
    lines.append(
        "Note: These are statistical associations, NOT causal effects."
    )
    if not top_positive.empty:
        lines.append("  Features that increase churn risk (positive coef):")
        for _, row in top_positive.iterrows():
            lines.append(
                f"    + {row['feature']}: {row['importance']:.4f}"
            )
    if not top_negative.empty:
        lines.append("  Features that decrease churn risk (negative coef):")
        for _, row in top_negative.iterrows():
            lines.append(
                f"    - {row['feature']}: {row['importance']:.4f}"
            )
    if top_positive.empty and top_negative.empty and not top_any.empty:
        lines.append("  Top features by absolute importance:")
        for _, row in top_any.iterrows():
            lines.append(
                f"    * {row['feature']}: {row['importance']:.4f} "
                f"({row['direction']})"
            )
    lines.append("")
    lines.append("14. PROJECT LIMITATIONS")
    lines.append("-" * 72)
    lines.append(
        "- The dataset may represent a single telecom context and "
        "geography; generalisation to other markets is not guaranteed."
    )
    lines.append(
        "- Class imbalance exists; metrics such as Precision/Recall/F1 "
        "and class_weight handling should be interpreted carefully."
    )
    lines.append(
        "- Concept drift: customer behaviour and pricing can change over "
        "time; the model should be monitored and periodically retrained."
    )
    lines.append(
        "- Predictions are correlational associations, not causal "
        "conclusions. A high churn score does not prove why a customer leaves."
    )
    lines.append(
        "- The default decision threshold (0.5) may not be optimal for "
        "business costs; threshold tuning against FP/FN costs is recommended."
    )
    lines.append(
        "- False positives (unnecessary retention offers) and false "
        "negatives (missed churners) have different business costs."
    )
    lines.append(
        "- This project is for educational / portfolio use and should not "
        "be the sole basis for automated customer decisions."
    )
    lines.append("")
    lines.append("=" * 72)
    lines.append("END OF FINAL SUMMARY")
    lines.append("=" * 72)

    FINAL_SUMMARY_PATH.write_text("\n".join(lines), encoding="utf-8")


# =============================================================================
# ANA AKIŞ
# =============================================================================

def main() -> None:
    """Run the complete final-assignment training workflow."""

    create_output_directories()

    print("=" * 70)
    print("CUSTOMER CHURN — FINAL ASSIGNMENT TRAINING PIPELINE")
    print("=" * 70)

    # --- Load & clean ---
    original_df = load_data()
    cleaned_df = clean_data(original_df)

    # --- EDA ---
    print("\n[1/10] Exploratory data analysis...")
    eda_stats = run_exploratory_data_analysis(
        raw_df=original_df,
        cleaned_df=cleaned_df,
    )
    print(f"  Saved: {DATA_PROFILE_PATH}")

    # --- Outlier analysis (descriptive; no deletion) ---
    print("\n[2/10] Outlier analysis (IQR, retain all rows)...")
    outlier_df = analyze_outliers(cleaned_df)
    print(f"  Saved: {OUTLIER_ANALYSIS_PATH}")

    # --- Split ---
    print("\n[3/10] Train / validation / test split (60/20/20)...")
    (
        X_train,
        X_validation,
        X_test,
        y_train,
        y_validation,
        y_test,
    ) = split_data(cleaned_df)

    print(f"  Eğitim kümesi    : {len(X_train)} satır")
    print(f"  Doğrulama kümesi : {len(X_validation)} satır")
    print(f"  Test kümesi      : {len(X_test)} satır")

    # --- Cross-validation ---
    print("\n[4/10] 5-fold stratified cross-validation on training data...")
    cv_results = run_cross_validation(X_train=X_train, y_train=y_train)
    print(f"  Saved: {CROSS_VALIDATION_RESULTS_PATH}")

    # --- Validation comparison ---
    print("\n[5/10] Validation comparison...")
    validation_results = train_and_compare_models(
        X_train=X_train,
        y_train=y_train,
        X_validation=X_validation,
        y_validation=y_validation,
        cv_results=cv_results,
    )
    print_validation_results(validation_results)
    print(f"  Saved: {VALIDATION_RESULTS_PATH}")

    best_model_name = str(validation_results.iloc[0]["Model"])
    print("\n" + "=" * 70)
    print("SEÇİLEN MODEL (CV + validation, test dokunulmadı)")
    print("=" * 70)
    print(best_model_name)

    # --- Hyperparameter tuning ---
    print("\n[6/10] Hyperparameter tuning (GridSearchCV on train only)...")
    _tuned_pipeline, best_hyperparameters, _search_df = tune_hyperparameters(
        model_name=best_model_name,
        X_train=X_train,
        y_train=y_train,
    )
    print(f"  Saved: {HYPERPARAMETER_SEARCH_PATH}")
    print(f"  Saved: {BEST_HYPERPARAMETERS_PATH}")

    # --- Final retrain on train + validation ---
    print(
        "\n[7/10] Final training on train + validation "
        "with tuned hyperparameters..."
    )
    final_pipeline = retrain_final_pipeline(
        model_name=best_model_name,
        best_params=best_hyperparameters["best_params"],
        X_train=X_train,
        y_train=y_train,
        X_validation=X_validation,
        y_validation=y_validation,
    )

    # --- Feature selection report ---
    print("\n[8/10] Saving selected features and feature importance...")
    selected_df = save_selected_features(final_pipeline)
    importance_df = save_feature_importance(
        pipeline=final_pipeline,
        model_name=best_model_name,
    )
    print(f"  Saved: {SELECTED_FEATURES_PATH}")
    print(f"  Saved: {FEATURE_IMPORTANCE_PATH}")

    # --- Final test evaluation (once) ---
    print("\n[9/10] Final evaluation on untouched test set...")
    test_metrics = evaluate_final_model(
        final_pipeline=final_pipeline,
        X_test=X_test,
        y_test=y_test,
    )

    test_metrics_df = pd.DataFrame(
        [
            {
                "Model": best_model_name,
                **test_metrics,
            }
        ]
    )
    test_metrics_df.to_csv(TEST_METRICS_PATH, index=False)

    joblib.dump(final_pipeline, MODEL_PATH)

    print_test_results(
        best_model_name=best_model_name,
        test_metrics=test_metrics,
    )

    # --- Final summary ---
    print("\n[10/10] Writing final summary report...")
    write_final_summary(
        raw_shape=eda_stats["raw_shape"],
        cleaned_shape=eda_stats["cleaned_shape"],
        target_counts=eda_stats["target_counts"],
        target_ratio=eda_stats["target_ratio"],
        outlier_df=outlier_df,
        cv_results=cv_results,
        validation_results=validation_results,
        best_model_name=best_model_name,
        best_hyperparameters=best_hyperparameters,
        test_metrics=test_metrics,
        importance_df=importance_df,
        selected_df=selected_df,
        train_size=len(X_train),
        validation_size=len(X_validation),
        test_size=len(X_test),
    )

    print("\n" + "=" * 70)
    print("KAYDEDİLEN DOSYALAR")
    print("=" * 70)
    for path in [
        MODEL_PATH,
        DATA_PROFILE_PATH,
        OUTLIER_ANALYSIS_PATH,
        SELECTED_FEATURES_PATH,
        CROSS_VALIDATION_RESULTS_PATH,
        VALIDATION_RESULTS_PATH,
        HYPERPARAMETER_SEARCH_PATH,
        BEST_HYPERPARAMETERS_PATH,
        TEST_METRICS_PATH,
        CLASSIFICATION_REPORT_PATH,
        CONFUSION_MATRIX_PATH,
        ROC_CURVE_PATH,
        FEATURE_IMPORTANCE_PATH,
        FINAL_SUMMARY_PATH,
    ]:
        print(f"  {path}")

    print("\nModel eğitimi başarıyla tamamlandı.")


if __name__ == "__main__":
    main()
