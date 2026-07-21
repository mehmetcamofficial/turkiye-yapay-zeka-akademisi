"""Canonical churn inference preparation shared by the portfolio UI.

The saved pipeline already contains imputation, encoding, feature selection and
the classifier. This module only recreates the target-independent engineered
columns used by the original standalone dashboard.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

RAW_COLUMNS = [
    "Gender", "Senior Citizen", "Partner", "Dependents", "Tenure Months",
    "Phone Service", "Multiple Lines", "Internet Service", "Online Security",
    "Online Backup", "Device Protection", "Tech Support", "Streaming TV",
    "Streaming Movies", "Contract", "Paperless Billing", "Payment Method",
    "Monthly Charges", "Total Charges", "CLTV",
]
MODEL_COLUMNS = RAW_COLUMNS + [
    "Average Monthly Spend", "Is Long Term Customer", "Has Support Services",
    "High Monthly Charge",
]
NUMERIC_COLUMNS = ["Tenure Months", "Monthly Charges", "Total Charges", "CLTV"]


def sample_batch() -> pd.DataFrame:
    """Return a valid, deterministic two-row CSV template."""
    return pd.DataFrame([
        {"Customer Reference":"CUST-001", "Gender":"Female", "Senior Citizen":"No", "Partner":"Yes", "Dependents":"No",
         "Tenure Months":12, "Phone Service":"Yes", "Multiple Lines":"No", "Internet Service":"Fiber optic",
         "Online Security":"No", "Online Backup":"Yes", "Device Protection":"No", "Tech Support":"No",
         "Streaming TV":"Yes", "Streaming Movies":"Yes", "Contract":"Month-to-month", "Paperless Billing":"Yes",
         "Payment Method":"Electronic check", "Monthly Charges":89.5, "Total Charges":1074.0, "CLTV":3200},
        {"Customer Reference":"CUST-002", "Gender":"Male", "Senior Citizen":"No", "Partner":"Yes", "Dependents":"Yes",
         "Tenure Months":48, "Phone Service":"Yes", "Multiple Lines":"Yes", "Internet Service":"DSL",
         "Online Security":"Yes", "Online Backup":"Yes", "Device Protection":"Yes", "Tech Support":"Yes",
         "Streaming TV":"No", "Streaming Movies":"No", "Contract":"Two year", "Paperless Billing":"No",
         "Payment Method":"Bank transfer (automatic)", "Monthly Charges":64.2, "Total Charges":3081.6, "CLTV":5100},
    ])


def validate_raw_batch(frame: pd.DataFrame) -> list[str]:
    """Return friendly schema/data errors without raising."""
    if frame.empty:
        return ["CSV dosyası veri satırı içermiyor."]
    missing = [column for column in RAW_COLUMNS if column not in frame.columns]
    if missing:
        return ["CSV dosyasında gerekli sütunlar bulunamadı: " + ", ".join(missing)]
    errors = []
    for column in NUMERIC_COLUMNS:
        values = pd.to_numeric(frame[column].astype(str).str.replace(",", ".", regex=False), errors="coerce")
        if values.isna().any():
            errors.append(f"{column} sütununda sayıya dönüştürülemeyen değerler var.")
    return errors


def prepare_model_input(frame: pd.DataFrame) -> pd.DataFrame:
    """Normalize raw inputs and add the original engineered features."""
    prepared = frame.copy()
    for column in NUMERIC_COLUMNS:
        prepared[column] = pd.to_numeric(
            prepared[column].astype(str).str.replace(",", ".", regex=False), errors="coerce"
        )
    tenure = prepared["Tenure Months"]
    monthly = prepared["Monthly Charges"]
    total = prepared["Total Charges"]
    prepared["Average Monthly Spend"] = (total / tenure.replace(0, np.nan)).fillna(monthly)
    prepared["Is Long Term Customer"] = (tenure >= 24).astype(int)
    prepared["Has Support Services"] = (
        prepared["Tech Support"].astype(str).eq("Yes") |
        prepared["Online Security"].astype(str).eq("Yes")
    ).astype(int)
    prepared["High Monthly Charge"] = (monthly > 70).astype(int)
    return prepared[MODEL_COLUMNS]


def predict_batch(model, frame: pd.DataFrame) -> pd.DataFrame:
    """Preserve source columns and append predictions, probabilities and bands."""
    prediction_input = prepare_model_input(frame[RAW_COLUMNS])
    predictions = model.predict(prediction_input)
    probabilities = model.predict_proba(prediction_input)[:, 1]
    result = frame.copy()
    result["Churn Prediction"] = predictions
    result["Churn Probability"] = probabilities
    result["Risk Band"] = pd.cut(
        probabilities, bins=[-np.inf, 0.4, 0.7, np.inf],
        labels=["Düşük", "Orta", "Yüksek"], right=False,
    ).astype(str)
    return result
