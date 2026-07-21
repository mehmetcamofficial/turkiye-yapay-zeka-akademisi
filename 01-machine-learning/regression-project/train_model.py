"""California Housing regression training workflow.

This offline-first project predicts median district house value (USD 100,000
units) from the local CSV. It performs EDA, leakage-safe preprocessing and
feature selection, compares four regressors with five-fold CV, tunes the best
candidate, evaluates one untouched test set, and persists the full sklearn
pipeline. Run: ``python train_model.py``.
"""

from __future__ import annotations

import json
from pathlib import Path
from time import perf_counter

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.feature_selection import SelectKBest, f_regression
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import GridSearchCV, KFold, cross_validate, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "data" / "california_housing.csv"
METADATA_PATH = BASE_DIR / "data" / "dataset_metadata.json"
MODEL_PATH = BASE_DIR / "models" / "regression_model.pkl"
OUTPUTS_DIR = BASE_DIR / "outputs"
TARGET = "target"
RANDOM_STATE = 42


def load_local_data() -> tuple[pd.DataFrame, dict]:
    """Load only the local reproducible copy; never download during training."""
    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"Local dataset missing: {DATA_PATH}. Run download_data.py once."
        )
    frame = pd.read_csv(DATA_PATH)
    metadata = json.loads(METADATA_PATH.read_text(encoding="utf-8"))
    if TARGET not in frame:
        raise ValueError(f"Target column '{TARGET}' is missing")
    return frame, metadata


def engineer_features(frame: pd.DataFrame) -> pd.DataFrame:
    """Create target-independent domain ratios consistently."""
    result = frame.copy()
    if {"AveRooms", "AveBedrms"}.issubset(result.columns):
        result["RoomsPerBedroom"] = result["AveRooms"] / result["AveBedrms"].replace(0, np.nan)
    if {"AveBedrms", "AveOccup"}.issubset(result.columns):
        result["BedroomsPerOccupant"] = result["AveBedrms"] / result["AveOccup"].replace(0, np.nan)
    return result


def save_data_reports(raw: pd.DataFrame, features: pd.DataFrame, metadata: dict) -> None:
    target_description = raw[TARGET].describe().to_string()
    report = "\n".join(
        [
            "CALIFORNIA HOUSING DATA PROFILE",
            "=" * 60,
            f"Dataset: {metadata['dataset']}",
            f"Shape: {raw.shape[0]} rows x {raw.shape[1]} columns",
            f"Columns: {list(raw.columns)}",
            "\nFirst five rows:\n" + raw.head().to_string(index=False),
            "\nData types:\n" + raw.dtypes.to_string(),
            "\nMissing values:\n" + raw.isna().sum().to_string(),
            "\nDescriptive statistics:\n" + raw.describe().to_string(),
            "\nTarget statistics:\n" + target_description,
            "\nEngineered features: RoomsPerBedroom, BedroomsPerOccupant",
        ]
    )
    (OUTPUTS_DIR / "data_profile.txt").write_text(report, encoding="utf-8")

    rows = []
    for column in features.select_dtypes(include="number").columns:
        series = features[column].dropna()
        q1, q3 = series.quantile([0.25, 0.75])
        iqr = q3 - q1
        lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        count = int(((series < lower) | (series > upper)).sum())
        rows.append({"column": column, "q1": q1, "q3": q3, "iqr": iqr,
                     "lower_bound": lower, "upper_bound": upper,
                     "outlier_count": count, "outlier_ratio": count / len(series),
                     "treatment": "retained; valid extremes, median imputation and scaling"})
    pd.DataFrame(rows).to_csv(OUTPUTS_DIR / "outlier_analysis.csv", index=False)


def metrics(y_true: pd.Series, prediction: np.ndarray) -> dict[str, float]:
    mse = mean_squared_error(y_true, prediction)
    return {"MAE": mean_absolute_error(y_true, prediction), "MSE": mse,
            "RMSE": float(np.sqrt(mse)), "R2": r2_score(y_true, prediction)}


def models() -> dict[str, object]:
    return {
        "Linear Regression": LinearRegression(),
        "Ridge": Ridge(alpha=1.0),
        "Random Forest": RandomForestRegressor(n_estimators=120, max_depth=18, n_jobs=-1, random_state=RANDOM_STATE),
        "Gradient Boosting": GradientBoostingRegressor(n_estimators=150, learning_rate=0.05, random_state=RANDOM_STATE),
    }


def make_pipeline(columns: list[str], estimator: object) -> Pipeline:
    preprocessing = ColumnTransformer([
        ("numeric", Pipeline([("imputer", SimpleImputer(strategy="median")),
                              ("scaler", StandardScaler())]), columns)
    ])
    return Pipeline([("preprocessor", preprocessing),
                     ("feature_selection", SelectKBest(f_regression, k=min(8, len(columns)))),
                     ("model", estimator)])


def parameter_grid(name: str) -> dict[str, list]:
    grids = {
        "Linear Regression": {"model__fit_intercept": [True, False]},
        "Ridge": {"model__alpha": [0.1, 1.0, 10.0, 50.0]},
        "Random Forest": {"model__n_estimators": [100, 180], "model__max_depth": [12, 18],
                          "model__min_samples_leaf": [1, 3]},
        "Gradient Boosting": {"model__n_estimators": [100, 180], "model__learning_rate": [0.03, 0.07],
                              "model__max_depth": [2, 3]},
    }
    return grids[name]


def main() -> None:
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    raw, metadata = load_local_data()
    featured = engineer_features(raw)
    save_data_reports(raw, featured.drop(columns=[TARGET]), metadata)
    X, y = featured.drop(columns=[TARGET]), featured[TARGET]
    X_train, X_temp, y_train, y_temp = train_test_split(X, y, test_size=0.4, random_state=RANDOM_STATE)
    X_val, X_test, y_val, y_test = train_test_split(X_temp, y_temp, test_size=0.5, random_state=RANDOM_STATE)
    cv = KFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)

    cv_rows, validation_rows = [], []
    for name, estimator in models().items():
        pipeline = make_pipeline(list(X.columns), estimator)
        scores = cross_validate(pipeline, X_train, y_train, cv=cv,
                                scoring={"mae": "neg_mean_absolute_error", "mse": "neg_mean_squared_error", "r2": "r2"},
                                n_jobs=-1)
        cv_rows.append({"Model": name, "CV MAE Mean": -scores["test_mae"].mean(),
                        "CV MAE Std": scores["test_mae"].std(),
                        "CV RMSE Mean": np.sqrt(-scores["test_mse"]).mean(),
                        "CV RMSE Std": np.sqrt(-scores["test_mse"]).std(),
                        "CV R2 Mean": scores["test_r2"].mean(), "CV R2 Std": scores["test_r2"].std()})
        started = perf_counter(); pipeline.fit(X_train, y_train); elapsed = perf_counter() - started
        validation_rows.append({"Model": name, **metrics(y_val, pipeline.predict(X_val)), "Training Time": elapsed})

    cv_df = pd.DataFrame(cv_rows).sort_values("CV RMSE Mean")
    val_df = pd.DataFrame(validation_rows).merge(cv_df, on="Model").sort_values(["RMSE", "CV RMSE Mean"])
    cv_df.to_csv(OUTPUTS_DIR / "cross_validation_results.csv", index=False)
    val_df.to_csv(OUTPUTS_DIR / "validation_results.csv", index=False)
    best_name = str(val_df.iloc[0]["Model"])

    search = GridSearchCV(make_pipeline(list(X.columns), models()[best_name]), parameter_grid(best_name),
                          scoring="neg_root_mean_squared_error", cv=cv, n_jobs=-1, refit=True)
    search.fit(X_train, y_train)
    search_df = pd.DataFrame(search.cv_results_)
    search_df[[c for c in search_df if c.startswith("param_") or c in {"mean_test_score", "std_test_score", "rank_test_score"}]].to_csv(
        OUTPUTS_DIR / "hyperparameter_search_results.csv", index=False)
    payload = {"model_name": best_name, "best_cv_rmse": -search.best_score_, "best_params": search.best_params_,
               "cv_folds": 5, "scoring": "neg_root_mean_squared_error"}
    (OUTPUTS_DIR / "best_hyperparameters.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")

    final = make_pipeline(list(X.columns), models()[best_name]); final.set_params(**search.best_params_)
    final.fit(pd.concat([X_train, X_val]), pd.concat([y_train, y_val]))
    prediction = final.predict(X_test); test_metrics = metrics(y_test, prediction)
    pd.DataFrame([{"Model": best_name, **test_metrics}]).to_csv(OUTPUTS_DIR / "test_metrics.csv", index=False)
    joblib.dump(final, MODEL_PATH, compress=3)

    feature_names = final.named_steps["preprocessor"].get_feature_names_out()
    support = final.named_steps["feature_selection"].get_support()
    selected = feature_names[support]; model = final.named_steps["model"]
    values = getattr(model, "feature_importances_", getattr(model, "coef_", np.zeros(len(selected))))
    pd.DataFrame({"feature": selected, "importance": np.asarray(values).ravel(),
                  "abs_importance": np.abs(values)}).sort_values("abs_importance", ascending=False).to_csv(
        OUTPUTS_DIR / "feature_importance.csv", index=False)

    residuals = y_test.to_numpy() - prediction
    plt.figure(figsize=(8, 5)); plt.scatter(prediction, residuals, alpha=.25); plt.axhline(0, color="red");
    plt.xlabel("Predicted"); plt.ylabel("Residual"); plt.title("Residual Analysis"); plt.tight_layout();
    plt.savefig(OUTPUTS_DIR / "residual_plot.png", dpi=200); plt.close()
    plt.figure(figsize=(6, 6)); plt.scatter(y_test, prediction, alpha=.25); bounds=[min(y_test.min(), prediction.min()), max(y_test.max(), prediction.max())];
    plt.plot(bounds, bounds, "r--"); plt.xlabel("Actual"); plt.ylabel("Predicted"); plt.title("Prediction vs Actual"); plt.tight_layout();
    plt.savefig(OUTPUTS_DIR / "prediction_vs_actual.png", dpi=200); plt.close()

    summary = f"""REGRESSION PROJECT FINAL SUMMARY
Dataset: {metadata['dataset']} ({raw.shape[0]} rows, {raw.shape[1]} columns)
Source: {metadata['source']}
Fallback used: {metadata.get('fallback_used', False)}
Split: 60% train / 20% validation / 20% untouched test; random_state=42
Preprocessing: median imputation, StandardScaler, SelectKBest(f_regression)
Engineered features: RoomsPerBedroom, BedroomsPerOccupant (target-independent)
Models: {', '.join(models())}
Selected model: {best_name}
Best parameters: {search.best_params_}
Test metrics: {test_metrics}
Limitations: 1990 California census context; geographic and temporal transfer is limited; associations are not causal; capped target and spatial dependence can bias evaluation.
"""
    (OUTPUTS_DIR / "final_summary.txt").write_text(summary, encoding="utf-8")
    print(summary)


if __name__ == "__main__":
    main()
