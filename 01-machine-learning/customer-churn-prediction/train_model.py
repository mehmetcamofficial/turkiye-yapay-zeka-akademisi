"""
Türkiye Yapay Zeka Akademisi
Customer Churn Prediction

Final training workflow:
1. Load and clean the dataset
2. Prevent target leakage
3. Engineer additional features
4. Split data into train, validation and test sets
5. Compare multiple classification models
6. Select the best model using validation ROC AUC
7. Retrain the selected model using train + validation data
8. Evaluate once on the untouched test set
9. Save the trained pipeline, metrics and visual outputs

Run:
python 01-machine-learning/customer-churn-prediction/train_model.py
"""

from pathlib import Path
from time import perf_counter

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import (
    GradientBoostingClassifier,
    RandomForestClassifier,
)
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
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.tree import DecisionTreeClassifier


BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "data" / "telco_customer_churn.csv"

MODELS_DIR = BASE_DIR / "models"
OUTPUTS_DIR = BASE_DIR / "outputs"

MODEL_PATH = MODELS_DIR / "churn_model.pkl"
VALIDATION_RESULTS_PATH = OUTPUTS_DIR / "validation_results.csv"
TEST_METRICS_PATH = OUTPUTS_DIR / "test_metrics.csv"
CLASSIFICATION_REPORT_PATH = (
    OUTPUTS_DIR / "classification_report.txt"
)
CONFUSION_MATRIX_PATH = OUTPUTS_DIR / "confusion_matrix.png"
ROC_CURVE_PATH = OUTPUTS_DIR / "roc_curve.png"

TARGET_COLUMN = "Churn Value"
RANDOM_STATE = 42


def create_output_directories() -> None:
    """Create model and output directories when necessary."""

    MODELS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )


def load_data() -> pd.DataFrame:
    """Load the customer churn dataset."""

    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"Veri dosyası bulunamadı: {DATA_PATH}"
        )

    return pd.read_csv(
        DATA_PATH,
        sep=";",
    )


def convert_numeric_columns(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """Convert text-based numeric columns into numeric values."""

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
            .str.replace(
                ",",
                ".",
                regex=False,
            )
            .str.strip()
        )

        df[column] = pd.to_numeric(
            df[column],
            errors="coerce",
        )

    return df


def create_features(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """Create additional customer behavior features."""

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
        df["Monthly Charges"]
        > df["Monthly Charges"].median()
    ).astype(int)

    return df


def remove_unnecessary_columns(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """Remove identifiers, location data and leakage columns."""

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

    return df.drop(
        columns=columns_to_drop,
        errors="ignore",
    )


def clean_data(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """Apply the complete cleaning and feature engineering workflow."""

    df = convert_numeric_columns(df)
    df = create_features(df)
    df = remove_unnecessary_columns(df)

    return df


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
    """
    Split the dataset into:
    - 60% training
    - 20% validation
    - 20% test
    """

    if TARGET_COLUMN not in df.columns:
        raise KeyError(
            f"Hedef sütun bulunamadı: {TARGET_COLUMN}"
        )

    X = df.drop(
        columns=[TARGET_COLUMN]
    )

    y = df[TARGET_COLUMN]

    X_train, X_temp, y_train, y_temp = train_test_split(
        X,
        y,
        test_size=0.40,
        random_state=RANDOM_STATE,
        stratify=y,
    )

    (
        X_validation,
        X_test,
        y_validation,
        y_test,
    ) = train_test_split(
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


def build_preprocessor(
    X: pd.DataFrame,
) -> ColumnTransformer:
    """Build numeric and categorical preprocessing pipelines."""

    numeric_columns = (
        X.select_dtypes(
            include=["number"]
        )
        .columns
        .tolist()
    )

    categorical_columns = (
        X.select_dtypes(
            exclude=["number"]
        )
        .columns
        .tolist()
    )

    numeric_pipeline = Pipeline(
        steps=[
            (
                "imputer",
                SimpleImputer(
                    strategy="median"
                ),
            ),
            (
                "scaler",
                StandardScaler(),
            ),
        ]
    )

    categorical_pipeline = Pipeline(
        steps=[
            (
                "imputer",
                SimpleImputer(
                    strategy="most_frequent"
                ),
            ),
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
            (
                "numeric",
                numeric_pipeline,
                numeric_columns,
            ),
            (
                "categorical",
                categorical_pipeline,
                categorical_columns,
            ),
        ],
        remainder="drop",
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
    """Create a complete preprocessing and model pipeline."""

    return Pipeline(
        steps=[
            (
                "preprocessor",
                build_preprocessor(X),
            ),
            (
                "model",
                model,
            ),
        ]
    )


def calculate_metrics(
    y_true: pd.Series,
    y_prediction: np.ndarray,
    y_probability: np.ndarray,
) -> dict[str, float]:
    """Calculate binary classification metrics."""

    return {
        "Accuracy": accuracy_score(
            y_true,
            y_prediction,
        ),
        "Precision": precision_score(
            y_true,
            y_prediction,
            zero_division=0,
        ),
        "Recall": recall_score(
            y_true,
            y_prediction,
            zero_division=0,
        ),
        "F1 Score": f1_score(
            y_true,
            y_prediction,
            zero_division=0,
        ),
        "ROC AUC": roc_auc_score(
            y_true,
            y_probability,
        ),
    }


def train_and_compare_models(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_validation: pd.DataFrame,
    y_validation: pd.Series,
) -> pd.DataFrame:
    """Train candidate models and compare validation performance."""

    results: list[dict[str, object]] = []

    for model_name, model in create_models().items():
        print(f"\n{model_name} eğitiliyor...")

        pipeline = create_model_pipeline(
            X=X_train,
            model=model,
        )

        start_time = perf_counter()

        pipeline.fit(
            X_train,
            y_train,
        )

        training_time = (
            perf_counter() - start_time
        )

        validation_prediction = pipeline.predict(
            X_validation
        )

        validation_probability = (
            pipeline.predict_proba(
                X_validation
            )[:, 1]
        )

        metrics = calculate_metrics(
            y_true=y_validation,
            y_prediction=validation_prediction,
            y_probability=validation_probability,
        )

        results.append(
            {
                "Model": model_name,
                **metrics,
                "Training Time": training_time,
            }
        )

        print(
            f"{model_name} tamamlandı. "
            f"F1: {metrics['F1 Score']:.4f} | "
            f"ROC AUC: {metrics['ROC AUC']:.4f}"
        )

    results_df = pd.DataFrame(
        results
    ).sort_values(
        by=[
            "ROC AUC",
            "F1 Score",
        ],
        ascending=False,
    ).reset_index(
        drop=True
    )

    return results_df


def get_model_by_name(
    model_name: str,
) -> object:
    """Return a new model instance by model name."""

    models = create_models()

    if model_name not in models:
        raise KeyError(
            f"Model bulunamadı: {model_name}"
        )

    return models[model_name]


def retrain_best_model(
    best_model_name: str,
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_validation: pd.DataFrame,
    y_validation: pd.Series,
) -> Pipeline:
    """Retrain the selected model using train and validation data."""

    X_combined = pd.concat(
        [
            X_train,
            X_validation,
        ],
        axis=0,
    )

    y_combined = pd.concat(
        [
            y_train,
            y_validation,
        ],
        axis=0,
    )

    best_model = get_model_by_name(
        best_model_name
    )

    final_pipeline = create_model_pipeline(
        X=X_combined,
        model=best_model,
    )

    final_pipeline.fit(
        X_combined,
        y_combined,
    )

    return final_pipeline


def save_confusion_matrix(
    y_test: pd.Series,
    y_prediction: np.ndarray,
) -> None:
    """Save the test confusion matrix."""

    matrix = confusion_matrix(
        y_test,
        y_prediction,
    )

    display = ConfusionMatrixDisplay(
        confusion_matrix=matrix,
        display_labels=[
            "No Churn",
            "Churn",
        ],
    )

    display.plot(
        values_format="d"
    )

    plt.title(
        "Test Set Confusion Matrix"
    )

    plt.tight_layout()

    plt.savefig(
        CONFUSION_MATRIX_PATH,
        dpi=300,
        bbox_inches="tight",
    )

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

    plt.title(
        "Test Set ROC Curve"
    )

    plt.tight_layout()

    plt.savefig(
        ROC_CURVE_PATH,
        dpi=300,
        bbox_inches="tight",
    )

    plt.close()


def save_classification_report(
    y_test: pd.Series,
    y_prediction: np.ndarray,
) -> None:
    """Save a detailed classification report."""

    report = classification_report(
        y_test,
        y_prediction,
        target_names=[
            "No Churn",
            "Churn",
        ],
        digits=4,
        zero_division=0,
    )

    CLASSIFICATION_REPORT_PATH.write_text(
        report,
        encoding="utf-8",
    )


def evaluate_final_model(
    final_pipeline: Pipeline,
    X_test: pd.DataFrame,
    y_test: pd.Series,
) -> dict[str, float]:
    """Evaluate the final model on the untouched test set."""

    test_prediction = final_pipeline.predict(
        X_test
    )

    test_probability = (
        final_pipeline.predict_proba(
            X_test
        )[:, 1]
    )

    metrics = calculate_metrics(
        y_true=y_test,
        y_prediction=test_prediction,
        y_probability=test_probability,
    )

    save_confusion_matrix(
        y_test=y_test,
        y_prediction=test_prediction,
    )

    save_roc_curve(
        y_test=y_test,
        y_probability=test_probability,
    )

    save_classification_report(
        y_test=y_test,
        y_prediction=test_prediction,
    )

    return metrics


def print_validation_results(
    results_df: pd.DataFrame,
) -> None:
    """Print the validation comparison table."""

    display_df = results_df.copy()

    numeric_columns = [
        "Accuracy",
        "Precision",
        "Recall",
        "F1 Score",
        "ROC AUC",
        "Training Time",
    ]

    display_df[numeric_columns] = (
        display_df[numeric_columns]
        .round(4)
    )

    print("\n" + "=" * 100)
    print("DOĞRULAMA KÜMESİ MODEL KARŞILAŞTIRMASI")
    print("=" * 100)

    print(
        display_df.to_string(
            index=False
        )
    )


def print_test_results(
    best_model_name: str,
    test_metrics: dict[str, float],
) -> None:
    """Print final test performance."""

    print("\n" + "=" * 70)
    print("SON TEST SONUÇLARI")
    print("=" * 70)

    print(
        f"Seçilen model : {best_model_name}"
    )

    for metric_name, metric_value in test_metrics.items():
        print(
            f"{metric_name:<12}: "
            f"{metric_value:.4f}"
        )


def main() -> None:
    """Run the complete final training workflow."""

    create_output_directories()

    original_df = load_data()
    cleaned_df = clean_data(
        original_df
    )

    (
        X_train,
        X_validation,
        X_test,
        y_train,
        y_validation,
        y_test,
    ) = split_data(
        cleaned_df
    )

    print("=" * 70)
    print("VERİ KÜMESİ BÖLÜMLERİ")
    print("=" * 70)

    print(
        f"Eğitim kümesi    : {len(X_train)} satır"
    )

    print(
        f"Doğrulama kümesi : {len(X_validation)} satır"
    )

    print(
        f"Test kümesi      : {len(X_test)} satır"
    )

    validation_results = train_and_compare_models(
        X_train=X_train,
        y_train=y_train,
        X_validation=X_validation,
        y_validation=y_validation,
    )

    validation_results.to_csv(
        VALIDATION_RESULTS_PATH,
        index=False,
    )

    print_validation_results(
        validation_results
    )

    best_model_name = str(
        validation_results.iloc[0]["Model"]
    )

    print("\n" + "=" * 70)
    print("SEÇİLEN MODEL")
    print("=" * 70)

    print(
        f"{best_model_name}, eğitim ve doğrulama "
        "verileri birleştirilerek yeniden eğitiliyor..."
    )

    final_pipeline = retrain_best_model(
        best_model_name=best_model_name,
        X_train=X_train,
        y_train=y_train,
        X_validation=X_validation,
        y_validation=y_validation,
    )

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

    test_metrics_df.to_csv(
        TEST_METRICS_PATH,
        index=False,
    )

    joblib.dump(
        final_pipeline,
        MODEL_PATH,
    )

    print_test_results(
        best_model_name=best_model_name,
        test_metrics=test_metrics,
    )

    print("\n" + "=" * 70)
    print("KAYDEDİLEN DOSYALAR")
    print("=" * 70)

    print(f"Model                 : {MODEL_PATH}")
    print(f"Doğrulama sonuçları   : {VALIDATION_RESULTS_PATH}")
    print(f"Test metrikleri       : {TEST_METRICS_PATH}")
    print(f"Sınıflandırma raporu  : {CLASSIFICATION_REPORT_PATH}")
    print(f"Confusion matrix      : {CONFUSION_MATRIX_PATH}")
    print(f"ROC curve             : {ROC_CURVE_PATH}")

    print("\nModel eğitimi başarıyla tamamlandı.")


if __name__ == "__main__":
    main()