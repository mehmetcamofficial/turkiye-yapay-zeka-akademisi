"""
Türkiye Yapay Zeka Akademisi
Customer Churn Analytics Dashboard

Çalıştırma:
streamlit run 01-machine-learning/customer-churn-prediction/app.py
"""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import streamlit as st


# =============================================================================
# DOSYA YOLLARI
# =============================================================================

BASE_DIR = Path(__file__).resolve().parent

MODEL_PATH = BASE_DIR / "models" / "churn_model.pkl"
TEST_METRICS_PATH = BASE_DIR / "outputs" / "test_metrics.csv"
VALIDATION_RESULTS_PATH = BASE_DIR / "outputs" / "validation_results.csv"
CLASSIFICATION_REPORT_PATH = (
    BASE_DIR / "outputs" / "classification_report.txt"
)
CONFUSION_MATRIX_PATH = (
    BASE_DIR / "outputs" / "confusion_matrix.png"
)
ROC_CURVE_PATH = BASE_DIR / "outputs" / "roc_curve.png"


# =============================================================================
# UYGULAMA AYARLARI
# =============================================================================

st.set_page_config(
    page_title="Churn Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =============================================================================
# SABİTLER
# =============================================================================

MODEL_INPUT_COLUMNS = [
    "Gender",
    "Senior Citizen",
    "Partner",
    "Dependents",
    "Tenure Months",
    "Phone Service",
    "Multiple Lines",
    "Internet Service",
    "Online Security",
    "Online Backup",
    "Device Protection",
    "Tech Support",
    "Streaming TV",
    "Streaming Movies",
    "Contract",
    "Paperless Billing",
    "Payment Method",
    "Monthly Charges",
    "Total Charges",
    "CLTV",
    "Average Monthly Spend",
    "Is Long Term Customer",
    "Has Support Services",
    "High Monthly Charge",
]

RAW_BATCH_COLUMNS = [
    "Gender",
    "Senior Citizen",
    "Partner",
    "Dependents",
    "Tenure Months",
    "Phone Service",
    "Multiple Lines",
    "Internet Service",
    "Online Security",
    "Online Backup",
    "Device Protection",
    "Tech Support",
    "Streaming TV",
    "Streaming Movies",
    "Contract",
    "Paperless Billing",
    "Payment Method",
    "Monthly Charges",
    "Total Charges",
    "CLTV",
]

NUMERIC_BATCH_COLUMNS = [
    "Tenure Months",
    "Monthly Charges",
    "Total Charges",
    "CLTV",
]

FINAL_MODEL_NAME = "Logistic Regression"
FINAL_TEST_ROC_AUC = 0.8438
FINAL_TEST_RECALL = 0.7995


# =============================================================================
# TASARIM
# =============================================================================

CUSTOM_CSS = """
<style>
    :root {
        --primary: #6366f1;
        --primary-dark: #4338ca;
        --surface: #ffffff;
        --surface-soft: #f8fafc;
        --border: #e2e8f0;
        --text-main: #0f172a;
        --text-muted: #64748b;
        --success: #059669;
        --warning: #d97706;
        --danger: #dc2626;
    }

    .stApp {
        background:
            radial-gradient(
                circle at 90% 5%,
                rgba(99, 102, 241, 0.09),
                transparent 25%
            ),
            linear-gradient(
                180deg,
                #f8fafc 0%,
                #f1f5f9 100%
            );
    }

    .block-container {
        max-width: 1500px;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }

    section[data-testid="stSidebar"] {
        border-right: 1px solid #e2e8f0;
    }

    section[data-testid="stSidebar"] > div {
        background:
            linear-gradient(
                180deg,
                #ffffff 0%,
                #f8fafc 100%
            );
    }

    .brand-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.45rem;
        background: rgba(99, 102, 241, 0.1);
        border: 1px solid rgba(99, 102, 241, 0.2);
        color: #4338ca;
        padding: 0.38rem 0.75rem;
        border-radius: 999px;
        font-size: 0.78rem;
        font-weight: 700;
        margin-bottom: 1rem;
    }

    .hero {
        background:
            linear-gradient(
                135deg,
                rgba(15, 23, 42, 0.98),
                rgba(49, 46, 129, 0.96)
            );
        border-radius: 24px;
        padding: 2.2rem;
        color: white;
        box-shadow: 0 18px 50px rgba(15, 23, 42, 0.18);
        margin-bottom: 1.5rem;
        overflow: hidden;
        position: relative;
    }

    .hero::after {
        content: "";
        position: absolute;
        width: 260px;
        height: 260px;
        border-radius: 50%;
        right: -90px;
        top: -110px;
        background: rgba(255, 255, 255, 0.08);
    }

    .hero h1 {
        color: white;
        font-size: clamp(2rem, 4vw, 3.35rem);
        line-height: 1.05;
        margin: 0 0 0.85rem 0;
        letter-spacing: -0.04em;
    }

    .hero p {
        color: rgba(255, 255, 255, 0.78);
        max-width: 780px;
        font-size: 1.04rem;
        line-height: 1.7;
        margin-bottom: 0;
    }

    .page-title {
        font-size: clamp(2rem, 3vw, 2.75rem);
        font-weight: 850;
        color: var(--text-main);
        letter-spacing: -0.035em;
        margin-bottom: 0.35rem;
    }

    .page-subtitle {
        color: var(--text-muted);
        font-size: 1.02rem;
        line-height: 1.65;
        margin-bottom: 1.65rem;
    }

    .section-title {
        color: var(--text-main);
        font-size: 1.3rem;
        font-weight: 800;
        margin-top: 0.3rem;
        margin-bottom: 0.9rem;
    }

    .info-card {
        background: rgba(255, 255, 255, 0.94);
        border: 1px solid var(--border);
        border-radius: 18px;
        padding: 1.3rem;
        min-height: 165px;
        box-shadow: 0 10px 28px rgba(15, 23, 42, 0.05);
    }

    .info-card-icon {
        font-size: 1.55rem;
        margin-bottom: 0.75rem;
    }

    .info-card-title {
        color: var(--text-main);
        font-weight: 800;
        font-size: 1.02rem;
        margin-bottom: 0.45rem;
    }

    .info-card-text {
        color: var(--text-muted);
        font-size: 0.9rem;
        line-height: 1.55;
    }

    .status-pill {
        display: inline-block;
        padding: 0.32rem 0.7rem;
        border-radius: 999px;
        font-size: 0.78rem;
        font-weight: 750;
        background: #dcfce7;
        color: #166534;
        border: 1px solid #bbf7d0;
    }

    .prediction-result {
        background: white;
        border: 1px solid var(--border);
        border-radius: 22px;
        padding: 1.6rem;
        box-shadow: 0 14px 38px rgba(15, 23, 42, 0.08);
        margin-top: 1.2rem;
    }

    .risk-low {
        background: #ecfdf5;
        border: 1px solid #a7f3d0;
        color: #065f46;
        border-radius: 16px;
        padding: 1rem;
    }

    .risk-medium {
        background: #fffbeb;
        border: 1px solid #fde68a;
        color: #92400e;
        border-radius: 16px;
        padding: 1rem;
    }

    .risk-high {
        background: #fef2f2;
        border: 1px solid #fecaca;
        color: #991b1b;
        border-radius: 16px;
        padding: 1rem;
    }

    .risk-title {
        font-weight: 850;
        font-size: 1.12rem;
        margin-bottom: 0.35rem;
    }

    .risk-copy {
        font-size: 0.92rem;
        line-height: 1.55;
    }

    .footer-note {
        color: var(--text-muted);
        font-size: 0.8rem;
        text-align: center;
        margin-top: 2.5rem;
        padding-top: 1.2rem;
        border-top: 1px solid var(--border);
    }

    div[data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.94);
        border: 1px solid var(--border);
        border-radius: 16px;
        padding: 1rem 1.1rem;
        box-shadow: 0 8px 24px rgba(15, 23, 42, 0.045);
    }

    div[data-testid="stMetricLabel"] {
        color: var(--text-muted);
    }

    div[data-testid="stMetricValue"] {
        color: var(--text-main);
        font-weight: 850;
    }

    div[data-testid="stForm"] {
        background: rgba(255, 255, 255, 0.93);
        border: 1px solid var(--border);
        border-radius: 22px;
        padding: 1.35rem;
        box-shadow: 0 12px 32px rgba(15, 23, 42, 0.055);
    }

    div.stButton > button,
    div[data-testid="stFormSubmitButton"] > button {
        width: 100%;
        border-radius: 12px;
        min-height: 3rem;
        font-weight: 800;
        border: none;
        background:
            linear-gradient(
                135deg,
                #6366f1,
                #4f46e5
            );
        color: white;
    }

    div.stButton > button:hover,
    div[data-testid="stFormSubmitButton"] > button:hover {
        background:
            linear-gradient(
                135deg,
                #4f46e5,
                #4338ca
            );
        color: white;
        border: none;
    }

    div[data-testid="stFileUploader"] {
        background: rgba(255, 255, 255, 0.9);
        border-radius: 18px;
        padding: 0.5rem;
    }

    .sidebar-model-card {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 15px;
        padding: 1rem;
        margin-top: 0.5rem;
    }

    .sidebar-model-name {
        color: #0f172a;
        font-weight: 800;
        margin-bottom: 0.3rem;
    }

    .sidebar-model-meta {
        color: #64748b;
        font-size: 0.82rem;
        line-height: 1.5;
    }
</style>
"""

st.markdown(
    CUSTOM_CSS,
    unsafe_allow_html=True,
)


# =============================================================================
# VERİ VE MODEL YÜKLEME
# =============================================================================

@st.cache_resource
def load_model():
    """Eğitilmiş makine öğrenmesi pipeline'ını yükler."""

    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Model dosyası bulunamadı: {MODEL_PATH}"
        )

    return joblib.load(MODEL_PATH)


@st.cache_data
def load_test_metrics() -> pd.DataFrame:
    """Final test metriklerini yükler."""

    if not TEST_METRICS_PATH.exists():
        return pd.DataFrame()

    return pd.read_csv(TEST_METRICS_PATH)


@st.cache_data
def load_validation_results() -> pd.DataFrame:
    """Doğrulama sonuçlarını yükler."""

    if not VALIDATION_RESULTS_PATH.exists():
        return pd.DataFrame()

    return pd.read_csv(VALIDATION_RESULTS_PATH)


@st.cache_data
def load_classification_report() -> str:
    """Sınıflandırma raporunu yükler."""

    if not CLASSIFICATION_REPORT_PATH.exists():
        return ""

    return CLASSIFICATION_REPORT_PATH.read_text(
        encoding="utf-8"
    )


# =============================================================================
# YARDIMCI FONKSİYONLAR
# =============================================================================

def calculate_engineered_features(
    tenure_months: int | float,
    monthly_charges: float,
    total_charges: float,
    tech_support: str,
    online_security: str,
) -> dict[str, float]:
    """Eğitim aşamasındaki özellik mühendisliğini tekrarlar."""

    tenure_value = float(tenure_months)
    monthly_value = float(monthly_charges)
    total_value = float(total_charges)

    if tenure_value > 0:
        average_monthly_spend = (
            total_value / tenure_value
        )
    else:
        average_monthly_spend = monthly_value

    is_long_term_customer = int(
        tenure_value >= 24
    )

    has_support_services = int(
        tech_support == "Yes"
        or online_security == "Yes"
    )

    high_monthly_charge = int(
        monthly_value > 70
    )

    return {
        "Average Monthly Spend": average_monthly_spend,
        "Is Long Term Customer": is_long_term_customer,
        "Has Support Services": has_support_services,
        "High Monthly Charge": high_monthly_charge,
    }


def create_customer_dataframe(
    gender: str,
    senior_citizen: str,
    partner: str,
    dependents: str,
    tenure_months: int,
    phone_service: str,
    multiple_lines: str,
    internet_service: str,
    online_security: str,
    online_backup: str,
    device_protection: str,
    tech_support: str,
    streaming_tv: str,
    streaming_movies: str,
    contract: str,
    paperless_billing: str,
    payment_method: str,
    monthly_charges: float,
    total_charges: float,
    cltv: float,
) -> pd.DataFrame:
    """Tek müşteri için model girdisi oluşturur."""

    engineered_features = calculate_engineered_features(
        tenure_months=tenure_months,
        monthly_charges=monthly_charges,
        total_charges=total_charges,
        tech_support=tech_support,
        online_security=online_security,
    )

    customer_data = {
        "Gender": gender,
        "Senior Citizen": senior_citizen,
        "Partner": partner,
        "Dependents": dependents,
        "Tenure Months": tenure_months,
        "Phone Service": phone_service,
        "Multiple Lines": multiple_lines,
        "Internet Service": internet_service,
        "Online Security": online_security,
        "Online Backup": online_backup,
        "Device Protection": device_protection,
        "Tech Support": tech_support,
        "Streaming TV": streaming_tv,
        "Streaming Movies": streaming_movies,
        "Contract": contract,
        "Paperless Billing": paperless_billing,
        "Payment Method": payment_method,
        "Monthly Charges": monthly_charges,
        "Total Charges": total_charges,
        "CLTV": cltv,
        **engineered_features,
    }

    return pd.DataFrame(
        [customer_data],
        columns=MODEL_INPUT_COLUMNS,
    )


def add_engineered_features_to_batch(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """Toplu tahmin verisine özellik mühendisliği uygular."""

    prepared_df = dataframe.copy()

    tenure_values = pd.to_numeric(
        prepared_df["Tenure Months"],
        errors="coerce",
    )

    monthly_values = pd.to_numeric(
        prepared_df["Monthly Charges"],
        errors="coerce",
    )

    total_values = pd.to_numeric(
        prepared_df["Total Charges"],
        errors="coerce",
    )

    safe_tenure = tenure_values.replace(
        0,
        np.nan,
    )

    average_monthly_spend = (
        total_values / safe_tenure
    ).fillna(monthly_values)

    prepared_df["Average Monthly Spend"] = (
        average_monthly_spend
    )

    prepared_df["Is Long Term Customer"] = (
        tenure_values >= 24
    ).astype(int)

    prepared_df["Has Support Services"] = (
        (
            prepared_df["Tech Support"].astype(str)
            == "Yes"
        )
        | (
            prepared_df["Online Security"].astype(str)
            == "Yes"
        )
    ).astype(int)

    prepared_df["High Monthly Charge"] = (
        monthly_values > 70
    ).astype(int)

    return prepared_df[MODEL_INPUT_COLUMNS]


def validate_batch_dataframe(
    dataframe: pd.DataFrame,
) -> list[str]:
    """CSV dosyasındaki eksikleri ve temel veri hatalarını kontrol eder."""

    errors: list[str] = []

    missing_columns = [
        column
        for column in RAW_BATCH_COLUMNS
        if column not in dataframe.columns
    ]

    if missing_columns:
        errors.append(
            "Eksik sütunlar: "
            + ", ".join(missing_columns)
        )

        return errors

    if dataframe.empty:
        errors.append(
            "CSV dosyası veri satırı içermiyor."
        )

        return errors

    for column in NUMERIC_BATCH_COLUMNS:
        converted_values = pd.to_numeric(
            dataframe[column],
            errors="coerce",
        )

        invalid_count = int(
            converted_values.isna().sum()
        )

        if invalid_count > 0:
            errors.append(
                f"'{column}' sütununda "
                f"{invalid_count} geçersiz değer var."
            )

    return errors


def normalize_batch_dataframe(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """CSV verisini model için temel olarak normalize eder."""

    normalized_df = dataframe.copy()

    for column in NUMERIC_BATCH_COLUMNS:
        normalized_df[column] = pd.to_numeric(
            normalized_df[column],
            errors="coerce",
        )

    text_columns = [
        column
        for column in RAW_BATCH_COLUMNS
        if column not in NUMERIC_BATCH_COLUMNS
    ]

    for column in text_columns:
        normalized_df[column] = (
            normalized_df[column]
            .astype(str)
            .str.strip()
        )

    return normalized_df


def get_risk_information(
    churn_probability: float,
) -> dict[str, str]:
    """Olasılığa göre risk seviyesi ve aksiyon önerisi üretir."""

    if churn_probability < 0.35:
        return {
            "level": "Düşük Risk",
            "css_class": "risk-low",
            "summary": (
                "Müşterinin kısa vadede ayrılma olasılığı düşük."
            ),
            "recommendation": (
                "Standart müşteri deneyimini sürdürün, "
                "memnuniyet sinyallerini periyodik olarak takip edin."
            ),
        }

    if churn_probability < 0.65:
        return {
            "level": "Orta Risk",
            "css_class": "risk-medium",
            "summary": (
                "Müşteride ayrılma eğilimi oluşturan bazı sinyaller var."
            ),
            "recommendation": (
                "Memnuniyet görüşmesi planlayın, kullanım davranışlarını "
                "inceleyin ve kişiselleştirilmiş teklif değerlendirin."
            ),
        }

    return {
        "level": "Yüksek Risk",
        "css_class": "risk-high",
        "summary": (
            "Müşterinin hizmetten ayrılma olasılığı yüksek."
        ),
        "recommendation": (
            "Müşteriyi öncelikli retention listesine alın; "
            "özel teklif, sözleşme yenileme avantajı veya "
            "doğrudan destek görüşmesi planlayın."
        ),
    }


def get_risk_label(
    probability: float,
) -> str:
    """Olasılığı metin risk etiketine dönüştürür."""

    if probability < 0.35:
        return "Düşük"

    if probability < 0.65:
        return "Orta"

    return "Yüksek"


def get_risk_factors(
    customer_df: pd.DataFrame,
) -> list[str]:
    """Müşteri girdilerinden açıklanabilir risk sinyalleri üretir."""

    customer = customer_df.iloc[0]
    factors: list[str] = []

    if customer["Contract"] == "Month-to-month":
        factors.append(
            "Aylık sözleşme kullanıyor; uzun vadeli bağlılık düşük olabilir."
        )

    if float(customer["Tenure Months"]) < 12:
        factors.append(
            "Müşterilik süresi 12 aydan kısa."
        )

    if float(customer["Monthly Charges"]) > 70:
        factors.append(
            "Aylık ücret seviyesi yüksek."
        )

    if customer["Tech Support"] in [
        "No",
        "No internet service",
    ]:
        factors.append(
            "Teknik destek hizmeti bulunmuyor."
        )

    if customer["Online Security"] in [
        "No",
        "No internet service",
    ]:
        factors.append(
            "Çevrimiçi güvenlik hizmeti bulunmuyor."
        )

    if customer["Payment Method"] == "Electronic check":
        factors.append(
            "Ödeme yöntemi elektronik çek."
        )

    if customer["Internet Service"] == "Fiber optic":
        factors.append(
            "Fiber internet müşterilerinde fiyat ve beklenti hassasiyeti görülebilir."
        )

    if customer["Paperless Billing"] == "Yes":
        factors.append(
            "Kağıtsız faturalandırma kullanıyor."
        )

    if not factors:
        factors.append(
            "Belirgin bir yüksek risk sinyali tespit edilmedi."
        )

    return factors


def dataframe_to_csv_bytes(
    dataframe: pd.DataFrame,
) -> bytes:
    """DataFrame'i UTF-8 BOM içeren CSV dosyasına dönüştürür."""

    return dataframe.to_csv(
        index=False,
    ).encode(
        "utf-8-sig"
    )


def create_sample_batch_dataframe() -> pd.DataFrame:
    """Toplu tahmin için örnek CSV oluşturur."""

    sample_data = [
        {
            "Customer ID": "CUST-001",
            "Gender": "Female",
            "Senior Citizen": "No",
            "Partner": "No",
            "Dependents": "No",
            "Tenure Months": 3,
            "Phone Service": "Yes",
            "Multiple Lines": "No",
            "Internet Service": "Fiber optic",
            "Online Security": "No",
            "Online Backup": "No",
            "Device Protection": "No",
            "Tech Support": "No",
            "Streaming TV": "Yes",
            "Streaming Movies": "Yes",
            "Contract": "Month-to-month",
            "Paperless Billing": "Yes",
            "Payment Method": "Electronic check",
            "Monthly Charges": 95.5,
            "Total Charges": 286.5,
            "CLTV": 2200,
        },
        {
            "Customer ID": "CUST-002",
            "Gender": "Male",
            "Senior Citizen": "No",
            "Partner": "Yes",
            "Dependents": "Yes",
            "Tenure Months": 48,
            "Phone Service": "Yes",
            "Multiple Lines": "Yes",
            "Internet Service": "DSL",
            "Online Security": "Yes",
            "Online Backup": "Yes",
            "Device Protection": "Yes",
            "Tech Support": "Yes",
            "Streaming TV": "No",
            "Streaming Movies": "No",
            "Contract": "Two year",
            "Paperless Billing": "No",
            "Payment Method": "Bank transfer (automatic)",
            "Monthly Charges": 55.0,
            "Total Charges": 2640.0,
            "CLTV": 6100,
        },
        {
            "Customer ID": "CUST-003",
            "Gender": "Female",
            "Senior Citizen": "Yes",
            "Partner": "Yes",
            "Dependents": "No",
            "Tenure Months": 16,
            "Phone Service": "Yes",
            "Multiple Lines": "Yes",
            "Internet Service": "Fiber optic",
            "Online Security": "No",
            "Online Backup": "Yes",
            "Device Protection": "No",
            "Tech Support": "No",
            "Streaming TV": "Yes",
            "Streaming Movies": "Yes",
            "Contract": "One year",
            "Paperless Billing": "Yes",
            "Payment Method": "Credit card (automatic)",
            "Monthly Charges": 88.0,
            "Total Charges": 1408.0,
            "CLTV": 3800,
        },
    ]

    return pd.DataFrame(sample_data)


def metric_value_from_dataframe(
    dataframe: pd.DataFrame,
    column_name: str,
    fallback_value: float,
) -> float:
    """Metrik CSV yapısından güvenli şekilde değer okur."""

    if dataframe.empty:
        return fallback_value

    if column_name not in dataframe.columns:
        return fallback_value

    try:
        return float(
            dataframe.iloc[0][column_name]
        )
    except (
        TypeError,
        ValueError,
        IndexError,
    ):
        return fallback_value


def render_page_header(
    title: str,
    subtitle: str,
    badge: str | None = None,
) -> None:
    """Standart sayfa başlığı oluşturur."""

    if badge:
        st.markdown(
            f'<div class="brand-badge">{badge}</div>',
            unsafe_allow_html=True,
        )

    st.markdown(
        f'<div class="page-title">{title}</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        f'<div class="page-subtitle">{subtitle}</div>',
        unsafe_allow_html=True,
    )


def render_info_card(
    icon: str,
    title: str,
    text: str,
) -> None:
    """Bilgilendirme kartı oluşturur."""

    st.markdown(
        f"""
        <div class="info-card">
            <div class="info-card-icon">{icon}</div>
            <div class="info-card-title">{title}</div>
            <div class="info-card-text">{text}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_footer() -> None:
    """Sayfa altı bilgisini oluşturur."""

    st.markdown(
        """
        <div class="footer-note">
            Türkiye Yapay Zeka Akademisi ·
            Machine Learning Portfolio ·
            Eğitim ve portföy amaçlı uygulama
        </div>
        """,
        unsafe_allow_html=True,
    )


# =============================================================================
# ANA SAYFA
# =============================================================================

def overview_page() -> None:
    """Portföy ana sayfasını oluşturur."""

    st.markdown(
        """
        <div class="hero">
            <div class="brand-badge">
                MACHINE LEARNING PORTFOLIO
            </div>
            <h1>Veriden karara giden<br>uçtan uca ML uygulaması</h1>
            <p>
                Veri hazırlama, özellik mühendisliği, model karşılaştırması,
                test değerlendirmesi ve Streamlit deployment adımlarını
                tek bir proje deneyiminde birleştiren müşteri kaybı
                tahmin sistemi.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    metrics_df = load_test_metrics()

    accuracy = metric_value_from_dataframe(
        metrics_df,
        "Accuracy",
        0.7495,
    )

    recall = metric_value_from_dataframe(
        metrics_df,
        "Recall",
        FINAL_TEST_RECALL,
    )

    f1_score = metric_value_from_dataframe(
        metrics_df,
        "F1 Score",
        0.6288,
    )

    roc_auc = metric_value_from_dataframe(
        metrics_df,
        "ROC AUC",
        FINAL_TEST_ROC_AUC,
    )

    metric_columns = st.columns(4)

    metric_columns[0].metric(
        "Test Accuracy",
        f"{accuracy:.3f}",
    )

    metric_columns[1].metric(
        "Test Recall",
        f"{recall:.3f}",
        help=(
            "Gerçek churn müşterilerinin model tarafından "
            "yakalanma oranı."
        ),
    )

    metric_columns[2].metric(
        "Test F1 Score",
        f"{f1_score:.3f}",
    )

    metric_columns[3].metric(
        "Test ROC AUC",
        f"{roc_auc:.3f}",
    )

    st.write("")

    st.markdown(
        '<div class="section-title">Proje modülleri</div>',
        unsafe_allow_html=True,
    )

    card_columns = st.columns(4)

    with card_columns[0]:
        render_info_card(
            icon="🎯",
            title="Tek Müşteri Tahmini",
            text=(
                "Müşteri profilini girerek churn olasılığını, "
                "risk seviyesini ve önerilen retention aksiyonunu görüntüleyin."
            ),
        )

    with card_columns[1]:
        render_info_card(
            icon="📁",
            title="Toplu CSV Analizi",
            text=(
                "Birden fazla müşteriyi aynı anda analiz edin, "
                "yüksek riskli kayıtları sıralayın ve sonuçları indirin."
            ),
        )

    with card_columns[2]:
        render_info_card(
            icon="📈",
            title="Model Performansı",
            text=(
                "Dört farklı makine öğrenmesi modelini karşılaştırın; "
                "test metriklerini ve ROC sonuçlarını inceleyin."
            ),
        )

    with card_columns[3]:
        render_info_card(
            icon="🧪",
            title="Geliştirilebilir Mimari",
            text=(
                "Yeni akademi ödevleri aynı dashboard altında "
                "bağımsız proje modülleri olarak eklenebilir."
            ),
        )

    st.write("")

    left_column, right_column = st.columns(
        [1.35, 1]
    )

    with left_column:
        st.markdown(
            '<div class="section-title">Proje akışı</div>',
            unsafe_allow_html=True,
        )

        project_flow_df = pd.DataFrame(
            {
                "Aşama": [
                    "1. Veri hazırlama",
                    "2. Özellik mühendisliği",
                    "3. Model karşılaştırma",
                    "4. Final değerlendirme",
                    "5. Uygulama",
                ],
                "Durum": [
                    "Tamamlandı",
                    "Tamamlandı",
                    "Tamamlandı",
                    "Tamamlandı",
                    "Aktif",
                ],
                "Çıktı": [
                    "Temizlenmiş müşteri verisi",
                    "4 yeni özellik",
                    "4 algoritma",
                    "Dokunulmamış test kümesi",
                    "Streamlit dashboard",
                ],
            }
        )

        st.dataframe(
            project_flow_df,
            use_column_width=True,
            hide_index=True,
        )

    with right_column:
        st.markdown(
            '<div class="section-title">Final model</div>',
            unsafe_allow_html=True,
        )

        st.markdown(
            f"""
            <div class="info-card">
                <div class="status-pill">MODEL READY</div>
                <div style="
                    color:#0f172a;
                    font-size:1.45rem;
                    font-weight:850;
                    margin-top:0.9rem;
                ">
                    {FINAL_MODEL_NAME}
                </div>
                <div style="
                    color:#64748b;
                    font-size:0.92rem;
                    line-height:1.65;
                    margin-top:0.6rem;
                ">
                    Model, doğrulama ROC AUC değerine göre seçildi.
                    Eğitim ve doğrulama kümeleri birleştirilerek yeniden
                    eğitildi ve bağımsız test kümesinde değerlendirildi.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.info(
        (
            "Yeni akademi ödevleri geldikçe ana menüye yeni proje "
            "sayfaları ekleyebilir ve bu uygulamayı kapsamlı bir "
            "Machine Learning Portfolio'ya dönüştürebiliriz."
        )
    )

    render_footer()


# =============================================================================
# TEK MÜŞTERİ TAHMİNİ
# =============================================================================

def single_prediction_page() -> None:
    """Tek müşteri churn tahmin ekranını oluşturur."""

    render_page_header(
        title="Tek Müşteri Tahmini",
        subtitle=(
            "Müşteri profilini, hizmet kullanımını ve faturalandırma "
            "bilgilerini girerek churn riskini hesaplayın."
        ),
        badge="CUSTOMER RISK SCORING",
    )

    try:
        model = load_model()
    except FileNotFoundError as error:
        st.error(
            str(error)
        )

        st.code(
            (
                "python "
                "01-machine-learning/"
                "customer-churn-prediction/"
                "train_model.py"
            ),
            language="bash",
        )

        st.stop()

    with st.form(
        "single_customer_prediction_form"
    ):
        profile_tab, services_tab, billing_tab = st.tabs(
            [
                "👤 Müşteri Profili",
                "📡 Hizmetler",
                "💳 Sözleşme ve Ödeme",
            ]
        )

        with profile_tab:
            profile_col_1, profile_col_2, profile_col_3 = (
                st.columns(3)
            )

            with profile_col_1:
                gender = st.selectbox(
                    "Cinsiyet",
                    [
                        "Female",
                        "Male",
                    ],
                )

                senior_citizen = st.selectbox(
                    "Yaşlı müşteri",
                    [
                        "No",
                        "Yes",
                    ],
                )

            with profile_col_2:
                partner = st.selectbox(
                    "Partneri var mı?",
                    [
                        "No",
                        "Yes",
                    ],
                )

                dependents = st.selectbox(
                    "Bakmakla yükümlü olduğu kişi var mı?",
                    [
                        "No",
                        "Yes",
                    ],
                )

            with profile_col_3:
                tenure_months = st.slider(
                    "Müşterilik süresi",
                    min_value=0,
                    max_value=72,
                    value=12,
                    step=1,
                    help="Ay cinsinden müşterilik süresi.",
                )

                cltv = st.number_input(
                    "Customer Lifetime Value",
                    min_value=0.0,
                    max_value=20000.0,
                    value=4000.0,
                    step=100.0,
                )

        with services_tab:
            service_col_1, service_col_2, service_col_3 = (
                st.columns(3)
            )

            with service_col_1:
                phone_service = st.selectbox(
                    "Telefon hizmeti",
                    [
                        "Yes",
                        "No",
                    ],
                )

                if phone_service == "No":
                    multiple_lines = "No phone service"

                    st.text_input(
                        "Birden fazla hat",
                        value="No phone service",
                        disabled=True,
                    )
                else:
                    multiple_lines = st.selectbox(
                        "Birden fazla hat",
                        [
                            "No",
                            "Yes",
                        ],
                    )

                internet_service = st.selectbox(
                    "İnternet hizmeti",
                    [
                        "Fiber optic",
                        "DSL",
                        "No",
                    ],
                )

            internet_unavailable = (
                internet_service == "No"
            )

            internet_options = (
                ["No internet service"]
                if internet_unavailable
                else ["No", "Yes"]
            )

            with service_col_2:
                online_security = st.selectbox(
                    "Çevrimiçi güvenlik",
                    internet_options,
                )

                online_backup = st.selectbox(
                    "Çevrimiçi yedekleme",
                    internet_options,
                )

                device_protection = st.selectbox(
                    "Cihaz koruması",
                    internet_options,
                )

            with service_col_3:
                tech_support = st.selectbox(
                    "Teknik destek",
                    internet_options,
                )

                streaming_tv = st.selectbox(
                    "TV yayını",
                    internet_options,
                )

                streaming_movies = st.selectbox(
                    "Film yayını",
                    internet_options,
                )

        with billing_tab:
            billing_col_1, billing_col_2, billing_col_3 = (
                st.columns(3)
            )

            with billing_col_1:
                contract = st.selectbox(
                    "Sözleşme türü",
                    [
                        "Month-to-month",
                        "One year",
                        "Two year",
                    ],
                )

                paperless_billing = st.selectbox(
                    "Kağıtsız faturalandırma",
                    [
                        "Yes",
                        "No",
                    ],
                )

            with billing_col_2:
                payment_method = st.selectbox(
                    "Ödeme yöntemi",
                    [
                        "Electronic check",
                        "Mailed check",
                        "Bank transfer (automatic)",
                        "Credit card (automatic)",
                    ],
                )

                monthly_charges = st.number_input(
                    "Aylık ücret",
                    min_value=0.0,
                    max_value=250.0,
                    value=70.0,
                    step=1.0,
                )

            estimated_total = (
                monthly_charges * tenure_months
            )

            with billing_col_3:
                total_charges = st.number_input(
                    "Toplam ücret",
                    min_value=0.0,
                    max_value=30000.0,
                    value=float(
                        estimated_total
                    ),
                    step=10.0,
                )

                st.caption(
                    (
                        "Tahmini başlangıç değeri: "
                        f"{estimated_total:,.2f}"
                    )
                )

        submitted = st.form_submit_button(
            "Churn Riskini Hesapla"
        )

    if submitted:
        customer_df = create_customer_dataframe(
            gender=gender,
            senior_citizen=senior_citizen,
            partner=partner,
            dependents=dependents,
            tenure_months=tenure_months,
            phone_service=phone_service,
            multiple_lines=multiple_lines,
            internet_service=internet_service,
            online_security=online_security,
            online_backup=online_backup,
            device_protection=device_protection,
            tech_support=tech_support,
            streaming_tv=streaming_tv,
            streaming_movies=streaming_movies,
            contract=contract,
            paperless_billing=paperless_billing,
            payment_method=payment_method,
            monthly_charges=monthly_charges,
            total_charges=total_charges,
            cltv=cltv,
        )

        try:
            prediction = int(
                model.predict(
                    customer_df
                )[0]
            )

            probability = float(
                model.predict_proba(
                    customer_df
                )[0, 1]
            )
        except Exception as error:
            st.error(
                (
                    "Tahmin sırasında bir hata oluştu. "
                    f"Detay: {error}"
                )
            )

            st.stop()

        risk_info = get_risk_information(
            probability
        )

        risk_factors = get_risk_factors(
            customer_df
        )

        st.markdown(
            '<div class="prediction-result">',
            unsafe_allow_html=True,
        )

        st.markdown(
            '<div class="section-title">Tahmin sonucu</div>',
            unsafe_allow_html=True,
        )

        result_columns = st.columns(4)

        result_columns[0].metric(
            "Churn Olasılığı",
            f"%{probability * 100:.1f}",
        )

        result_columns[1].metric(
            "Model Kararı",
            (
                "Ayrılabilir"
                if prediction == 1
                else "Kalması Bekleniyor"
            ),
        )

        result_columns[2].metric(
            "Risk Seviyesi",
            risk_info["level"],
        )

        result_columns[3].metric(
            "Kullanılan Model",
            "Logistic Regression",
        )

        st.progress(
            min(
                max(
                    probability,
                    0.0,
                ),
                1.0,
            )
        )

        st.markdown(
            f"""
            <div class="{risk_info['css_class']}">
                <div class="risk-title">
                    {risk_info['level']}
                </div>
                <div class="risk-copy">
                    {risk_info['summary']}
                    <br><br>
                    <strong>Önerilen aksiyon:</strong>
                    {risk_info['recommendation']}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.write("")

        explanation_col, data_col = st.columns(
            [1.1, 1]
        )

        with explanation_col:
            st.markdown(
                "#### Tespit edilen risk sinyalleri"
            )

            for factor in risk_factors:
                st.write(
                    f"• {factor}"
                )

        with data_col:
            st.markdown(
                "#### Hesaplanan özellikler"
            )

            engineered_display_df = customer_df[
                [
                    "Average Monthly Spend",
                    "Is Long Term Customer",
                    "Has Support Services",
                    "High Monthly Charge",
                ]
            ].copy()

            engineered_display_df.columns = [
                "Ort. Aylık Harcama",
                "Uzun Süreli Müşteri",
                "Destek Hizmeti Var",
                "Yüksek Aylık Ücret",
            ]

            st.dataframe(
                engineered_display_df.round(2),
                use_column_width=True,
                hide_index=True,
            )

        with st.expander(
            "Model girdisinin tamamını göster"
        ):
            st.dataframe(
                customer_df,
                use_column_width=True,
                hide_index=True,
            )

        st.markdown(
            "</div>",
            unsafe_allow_html=True,
        )

    render_footer()


# =============================================================================
# TOPLU CSV TAHMİNİ
# =============================================================================

def batch_prediction_page() -> None:
    """CSV dosyasıyla toplu churn analizi yapar."""

    render_page_header(
        title="Toplu CSV Analizi",
        subtitle=(
            "Bir müşteri listesini yükleyerek tüm kayıtların churn "
            "olasılıklarını hesaplayın, yüksek riskli müşterileri "
            "önceliklendirin ve analiz sonucunu indirin."
        ),
        badge="BATCH PREDICTION",
    )

    try:
        model = load_model()
    except FileNotFoundError as error:
        st.error(
            str(error)
        )

        st.stop()

    sample_df = create_sample_batch_dataframe()

    instruction_col, download_col = st.columns(
        [1.5, 1]
    )

    with instruction_col:
        st.info(
            (
                "CSV dosyasında gerekli müşteri sütunları bulunmalıdır. "
                "`Customer ID` gibi ek sütunlar korunur ve sonuç "
                "dosyasına dahil edilir."
            )
        )

    with download_col:
        st.download_button(
            label="Örnek CSV Şablonunu İndir",
            data=dataframe_to_csv_bytes(
                sample_df
            ),
            file_name="churn_batch_template.csv",
            mime="text/csv",
            use_column_width=True,
        )

    uploaded_file = st.file_uploader(
        "Müşteri CSV dosyasını yükleyin",
        type=["csv"],
        help=(
            "Dosya UTF-8 veya yaygın CSV formatlarından biri olabilir."
        ),
    )

    if uploaded_file is None:
        st.markdown(
            '<div class="section-title">Örnek veri önizlemesi</div>',
            unsafe_allow_html=True,
        )

        st.dataframe(
            sample_df,
            use_column_width=True,
            hide_index=True,
        )

        render_footer()
        return

    try:
        uploaded_df = pd.read_csv(
            uploaded_file
        )
    except UnicodeDecodeError:
        try:
            uploaded_file.seek(0)

            uploaded_df = pd.read_csv(
                uploaded_file,
                encoding="latin-1",
            )
        except Exception as error:
            st.error(
                (
                    "CSV dosyası okunamadı. "
                    f"Detay: {error}"
                )
            )

            render_footer()
            return
    except Exception as error:
        st.error(
            (
                "CSV dosyası okunamadı. "
                f"Detay: {error}"
            )
        )

        render_footer()
        return

    st.success(
        (
            f"Dosya başarıyla yüklendi: "
            f"{len(uploaded_df)} müşteri kaydı."
        )
    )

    preview_tab, columns_tab = st.tabs(
        [
            "Veri Önizlemesi",
            "Sütun Kontrolü",
        ]
    )

    with preview_tab:
        st.dataframe(
            uploaded_df.head(25),
            use_column_width=True,
            hide_index=True,
        )

    with columns_tab:
        existing_columns = set(
            uploaded_df.columns
        )

        column_status_df = pd.DataFrame(
            {
                "Gerekli Sütun": RAW_BATCH_COLUMNS,
                "Durum": [
                    (
                        "Mevcut"
                        if column in existing_columns
                        else "Eksik"
                    )
                    for column in RAW_BATCH_COLUMNS
                ],
            }
        )

        st.dataframe(
            column_status_df,
            use_column_width=True,
            hide_index=True,
        )

    validation_errors = validate_batch_dataframe(
        uploaded_df
    )

    if validation_errors:
        st.error(
            "CSV dosyası tahmin için hazır değil."
        )

        for error_message in validation_errors:
            st.write(
                f"• {error_message}"
            )

        render_footer()
        return

    if st.button(
        "Toplu Tahmini Başlat",
        use_column_width=True,
    ):
        normalized_df = normalize_batch_dataframe(
            uploaded_df
        )

        try:
            model_input_df = add_engineered_features_to_batch(
                normalized_df
            )

            predictions = model.predict(
                model_input_df
            ).astype(int)

            probabilities = model.predict_proba(
                model_input_df
            )[:, 1]
        except Exception as error:
            st.error(
                (
                    "Toplu tahmin sırasında hata oluştu. "
                    f"Detay: {error}"
                )
            )

            render_footer()
            return

        result_df = uploaded_df.copy()

        result_df["Churn Prediction"] = np.where(
            predictions == 1,
            "Ayrılabilir",
            "Kalması Bekleniyor",
        )

        result_df["Churn Probability"] = (
            probabilities
        )

        result_df["Churn Probability (%)"] = (
            probabilities * 100
        ).round(2)

        result_df["Risk Level"] = [
            get_risk_label(
                float(probability)
            )
            for probability in probabilities
        ]

        result_df["Recommended Action"] = [
            get_risk_information(
                float(probability)
            )["recommendation"]
            for probability in probabilities
        ]

        result_df = result_df.sort_values(
            by="Churn Probability",
            ascending=False,
        ).reset_index(
            drop=True
        )

        high_risk_count = int(
            (
                result_df["Risk Level"]
                == "Yüksek"
            ).sum()
        )

        medium_risk_count = int(
            (
                result_df["Risk Level"]
                == "Orta"
            ).sum()
        )

        predicted_churn_count = int(
            (
                result_df["Churn Prediction"]
                == "Ayrılabilir"
            ).sum()
        )

        average_probability = float(
            result_df["Churn Probability"]
            .mean()
        )

        st.markdown(
            '<div class="section-title">Analiz özeti</div>',
            unsafe_allow_html=True,
        )

        summary_columns = st.columns(4)

        summary_columns[0].metric(
            "Toplam Müşteri",
            f"{len(result_df):,}",
        )

        summary_columns[1].metric(
            "Tahmini Churn",
            f"{predicted_churn_count:,}",
        )

        summary_columns[2].metric(
            "Yüksek Risk",
            f"{high_risk_count:,}",
        )

        summary_columns[3].metric(
            "Ortalama Risk",
            f"%{average_probability * 100:.1f}",
        )

        if high_risk_count > 0:
            st.warning(
                (
                    f"{high_risk_count} müşteri yüksek risk grubunda. "
                    "Bu müşteriler retention ekibi tarafından öncelikli "
                    "olarak incelenmelidir."
                )
            )
        elif medium_risk_count > 0:
            st.info(
                (
                    f"{medium_risk_count} müşteri orta risk grubunda. "
                    "Proaktif iletişim planlanabilir."
                )
            )
        else:
            st.success(
                "Yüklenen listede yüksek veya orta riskli müşteri bulunmadı."
            )

        result_tab, high_risk_tab, distribution_tab = st.tabs(
            [
                "Tüm Sonuçlar",
                "Yüksek Riskli Müşteriler",
                "Risk Dağılımı",
            ]
        )

        with result_tab:
            preferred_columns = [
                column
                for column in [
                    "Customer ID",
                    "Gender",
                    "Tenure Months",
                    "Contract",
                    "Monthly Charges",
                    "Churn Prediction",
                    "Churn Probability (%)",
                    "Risk Level",
                    "Recommended Action",
                ]
                if column in result_df.columns
            ]

            st.dataframe(
                result_df[preferred_columns],
                use_column_width=True,
                hide_index=True,
            )

        with high_risk_tab:
            high_risk_df = result_df[
                result_df["Risk Level"]
                == "Yüksek"
            ]

            if high_risk_df.empty:
                st.success(
                    "Yüksek riskli müşteri bulunmadı."
                )
            else:
                st.dataframe(
                    high_risk_df[
                        preferred_columns
                    ],
                    use_column_width=True,
                    hide_index=True,
                )

        with distribution_tab:
            risk_distribution_df = (
                result_df["Risk Level"]
                .value_counts()
                .reindex(
                    [
                        "Yüksek",
                        "Orta",
                        "Düşük",
                    ],
                    fill_value=0,
                )
                .rename_axis(
                    "Risk Seviyesi"
                )
                .reset_index(
                    name="Müşteri Sayısı"
                )
            )

            st.bar_chart(
                risk_distribution_df.set_index(
                    "Risk Seviyesi"
                )
            )

        st.download_button(
            label="Tahmin Sonuçlarını CSV Olarak İndir",
            data=dataframe_to_csv_bytes(
                result_df
            ),
            file_name="churn_prediction_results.csv",
            mime="text/csv",
            use_column_width=True,
        )

    render_footer()


# =============================================================================
# MODEL PERFORMANSI
# =============================================================================

def model_performance_page() -> None:
    """Model performans sayfasını oluşturur."""

    render_page_header(
        title="Model Performansı",
        subtitle=(
            "Doğrulama kümesindeki model karşılaştırmasını ve "
            "seçilen final modelin bağımsız test kümesi sonuçlarını inceleyin."
        ),
        badge="MODEL EVALUATION",
    )

    metrics_df = load_test_metrics()

    accuracy = metric_value_from_dataframe(
        metrics_df,
        "Accuracy",
        0.7495,
    )

    precision = metric_value_from_dataframe(
        metrics_df,
        "Precision",
        0.5182,
    )

    recall = metric_value_from_dataframe(
        metrics_df,
        "Recall",
        FINAL_TEST_RECALL,
    )

    f1_score = metric_value_from_dataframe(
        metrics_df,
        "F1 Score",
        0.6288,
    )

    roc_auc = metric_value_from_dataframe(
        metrics_df,
        "ROC AUC",
        FINAL_TEST_ROC_AUC,
    )

    metric_columns = st.columns(5)

    metric_columns[0].metric(
        "Accuracy",
        f"{accuracy:.4f}",
    )

    metric_columns[1].metric(
        "Precision",
        f"{precision:.4f}",
    )

    metric_columns[2].metric(
        "Recall",
        f"{recall:.4f}",
    )

    metric_columns[3].metric(
        "F1 Score",
        f"{f1_score:.4f}",
    )

    metric_columns[4].metric(
        "ROC AUC",
        f"{roc_auc:.4f}",
    )

    st.write("")

    st.markdown(
        '<div class="section-title">Doğrulama modeli karşılaştırması</div>',
        unsafe_allow_html=True,
    )

    validation_df = load_validation_results()

    if validation_df.empty:
        st.info(
            "Model karşılaştırma sonuçları bulunamadı."
        )
    else:
        display_df = validation_df.copy()

        numeric_columns = [
            "Accuracy",
            "Precision",
            "Recall",
            "F1 Score",
            "ROC AUC",
            "Training Time",
        ]

        available_numeric_columns = [
            column
            for column in numeric_columns
            if column in display_df.columns
        ]

        display_df[
            available_numeric_columns
        ] = display_df[
            available_numeric_columns
        ].round(4)

        st.dataframe(
            display_df,
            use_column_width=True,
            hide_index=True,
        )

        if "Model" in display_df.columns:
            chart_columns = [
                column
                for column in [
                    "Accuracy",
                    "Precision",
                    "Recall",
                    "F1 Score",
                    "ROC AUC",
                ]
                if column in display_df.columns
            ]

            chart_df = display_df[
                [
                    "Model",
                    *chart_columns,
                ]
            ].set_index(
                "Model"
            )

            st.bar_chart(
                chart_df
            )

    st.write("")

    st.markdown(
        '<div class="section-title">Test görselleri</div>',
        unsafe_allow_html=True,
    )

    visual_col_1, visual_col_2 = st.columns(2)

    with visual_col_1:
        st.markdown(
            "#### Confusion Matrix"
        )

        if CONFUSION_MATRIX_PATH.exists():
            st.image(
                str(
                    CONFUSION_MATRIX_PATH
                ),
                use_column_width=True,
            )
        else:
            st.info(
                "Confusion matrix görseli bulunamadı."
            )

    with visual_col_2:
        st.markdown(
            "#### ROC Curve"
        )

        if ROC_CURVE_PATH.exists():
            st.image(
                str(
                    ROC_CURVE_PATH
                ),
                use_column_width=True,
            )
        else:
            st.info(
                "ROC curve görseli bulunamadı."
            )

    classification_report = load_classification_report()

    if classification_report:
        with st.expander(
            "Sınıflandırma raporunu göster"
        ):
            st.code(
                classification_report,
                language="text",
            )

    st.info(
        (
            "Model seçimi doğrulama ROC AUC değerine göre yapılmıştır. "
            "Final test kümesi yalnızca son değerlendirme aşamasında "
            "kullanılmıştır."
        )
    )

    render_footer()


# =============================================================================
# PROJE BİLGİLERİ
# =============================================================================

def project_information_page() -> None:
    """Proje yöntem ve dokümantasyon sayfasını oluşturur."""

    render_page_header(
        title="Proje Bilgileri",
        subtitle=(
            "Customer Churn Prediction projesinin problem tanımı, "
            "veri işleme adımları, model seçimi ve sınırlamalarının özeti."
        ),
        badge="PROJECT DOCUMENTATION",
    )

    problem_tab, pipeline_tab, ethics_tab = st.tabs(
        [
            "Problem ve Amaç",
            "ML Pipeline",
            "Etik ve Sınırlamalar",
        ]
    )

    with problem_tab:
        st.markdown(
            "### Problem"
        )

        st.write(
            """
            Telekomünikasyon şirketleri için mevcut müşterileri korumak,
            yeni müşteri edinmekten daha düşük maliyetli olabilir.
            Bu proje, müşteri özelliklerini kullanarak hizmetten ayrılma
            ihtimali yüksek müşterileri erken tespit etmeyi amaçlar.
            """
        )

        st.markdown(
            "### İş değeri"
        )

        st.write(
            """
            Model çıktıları aşağıdaki operasyonel süreçlerde kullanılabilir:

            - Yüksek riskli müşterilerin önceliklendirilmesi
            - Kişiselleştirilmiş sadakat kampanyaları
            - Müşteri destek görüşmelerinin planlanması
            - Sözleşme yenileme tekliflerinin hedeflenmesi
            - Churn nedenlerinin analiz edilmesi
            """
        )

        st.markdown(
            "### Hedef değişken"
        )

        st.write(
            """
            Modelin hedefi müşterinin churn durumudur:

            - `0`: Müşterinin kalması bekleniyor
            - `1`: Müşterinin ayrılabileceği tahmin ediliyor
            """
        )

    with pipeline_tab:
        pipeline_df = pd.DataFrame(
            {
                "Adım": [
                    "Veri yükleme",
                    "Veri temizleme",
                    "Özellik mühendisliği",
                    "Train/validation/test ayrımı",
                    "Preprocessing",
                    "Model eğitimi",
                    "Model seçimi",
                    "Final test",
                    "Model kaydetme",
                    "Streamlit arayüzü",
                ],
                "Açıklama": [
                    "Telco müşteri verisi pandas ile yüklendi.",
                    "Sayısal ve kategorik alanlar kontrol edildi.",
                    "Dört yeni davranışsal özellik oluşturuldu.",
                    "Veri %60, %20 ve %20 oranında ayrıldı.",
                    "Sayısal ve kategorik değişkenler pipeline ile işlendi.",
                    "Dört sınıflandırma algoritması eğitildi.",
                    "Doğrulama ROC AUC değerine göre seçim yapıldı.",
                    "Seçilen model bağımsız test kümesinde değerlendirildi.",
                    "Pipeline joblib formatında kaydedildi.",
                    "Tekli ve toplu tahmin arayüzü oluşturuldu.",
                ],
            }
        )

        st.dataframe(
            pipeline_df,
            use_column_width=True,
            hide_index=True,
        )

        st.markdown(
            "### Karşılaştırılan modeller"
        )

        st.write(
            """
            - Logistic Regression
            - Decision Tree
            - Random Forest
            - Gradient Boosting
            """
        )

        st.markdown(
            "### Özellik mühendisliği"
        )

        feature_df = pd.DataFrame(
            {
                "Yeni Özellik": [
                    "Average Monthly Spend",
                    "Is Long Term Customer",
                    "Has Support Services",
                    "High Monthly Charge",
                ],
                "Açıklama": [
                    "Toplam ücretin müşterilik süresine oranı",
                    "Müşterilik süresinin 24 ay veya daha fazla olması",
                    "Teknik destek veya çevrimiçi güvenlik hizmeti bulunması",
                    "Aylık ücretin 70 birimin üzerinde olması",
                ],
            }
        )

        st.dataframe(
            feature_df,
            use_column_width=True,
            hide_index=True,
        )

    with ethics_tab:
        st.warning(
            (
                "Bu uygulama eğitim ve portföy amaçlıdır. "
                "Gerçek müşteriler hakkında tamamen otomatik karar "
                "vermek için tek başına kullanılmamalıdır."
            )
        )

        st.markdown(
            "### Dikkat edilmesi gereken noktalar"
        )

        st.write(
            """
            - Model sonuçları olasılık tahminidir, kesin karar değildir.
            - Eğitim verisindeki önyargılar modele yansıyabilir.
            - Müşteri verileri gizlilik ve veri koruma kurallarına uygun
              işlenmelidir.
            - Retention tekliflerinde ayrımcı uygulamalardan kaçınılmalıdır.
            - Model performansı zaman içinde düzenli olarak izlenmelidir.
            - Veri dağılımı değiştiğinde model yeniden eğitilmelidir.
            """
        )

        st.markdown(
            "### Teknik sınırlamalar"
        )

        st.write(
            """
            - Mevcut model tek bir tarihsel veri setiyle eğitilmiştir.
            - Olasılık eşik değeri varsayılan olarak 0.50'dir.
            - Model, nedensellik değil istatistiksel ilişki öğrenir.
            - Gerçek üretim ortamında model monitoring ve drift analizi gerekir.
            """
        )

    render_footer()


# =============================================================================
# YAKINDA EKLENECEK ÖDEVLER
# =============================================================================

def assignments_page() -> None:
    """Yeni akademi ödevlerinin ekleneceği yol haritasını gösterir."""

    render_page_header(
        title="Akademi Ödevleri",
        subtitle=(
            "Yeni ödevler geldikçe her çalışma bağımsız bir proje "
            "modülü olarak bu portföye eklenecek."
        ),
        badge="LEARNING ROADMAP",
    )

    assignments_df = pd.DataFrame(
        {
            "Proje": [
                "Customer Churn Prediction",
                "Regresyon Projesi",
                "Kümeleme Projesi",
                "NLP Projesi",
                "Model Deployment",
            ],
            "Kategori": [
                "Sınıflandırma",
                "Regresyon",
                "Unsupervised Learning",
                "Natural Language Processing",
                "MLOps",
            ],
            "Durum": [
                "Tamamlandı",
                "Yeni ödev bekleniyor",
                "Yeni ödev bekleniyor",
                "Yeni ödev bekleniyor",
                "Planlandı",
            ],
        }
    )

    st.dataframe(
        assignments_df,
        use_column_width=True,
        hide_index=True,
    )

    st.markdown(
        '<div class="section-title">Geliştirme planı</div>',
        unsafe_allow_html=True,
    )

    roadmap_columns = st.columns(3)

    with roadmap_columns[0]:
        render_info_card(
            icon="1️⃣",
            title="Ödevi Analiz Et",
            text=(
                "Problem, veri seti, teslim kriterleri ve değerlendirme "
                "metrikleri birlikte incelenir."
            ),
        )

    with roadmap_columns[1]:
        render_info_card(
            icon="2️⃣",
            title="Modeli Geliştir",
            text=(
                "Notebook veya Python pipeline hazırlanır, modeller "
                "karşılaştırılır ve çıktılar kaydedilir."
            ),
        )

    with roadmap_columns[2]:
        render_info_card(
            icon="3️⃣",
            title="Dashboard'a Ekle",
            text=(
                "Yeni proje mevcut Streamlit portföyüne bağımsız "
                "bir sayfa olarak entegre edilir."
            ),
        )

    st.success(
        (
            "Customer Churn Prediction modülü aktif. "
            "Yeni ödevi paylaştığında mevcut yapıyı bozmadan "
            "yeni bir menü bölümü ekleyebiliriz."
        )
    )

    render_footer()


# =============================================================================
# SIDEBAR VE ANA UYGULAMA
# =============================================================================

def render_sidebar() -> str:
    """Sol navigasyon menüsünü oluşturur."""

    with st.sidebar:
        st.markdown(
            "## 📊 Churn Analytics"
        )

        st.caption(
            "Türkiye Yapay Zeka Akademisi"
        )

        st.markdown(
            """
            <div class="sidebar-model-card">
                <div class="sidebar-model-name">
                    ML Portfolio Dashboard
                </div>
                <div class="sidebar-model-meta">
                    Veri hazırlama, modelleme, değerlendirme ve
                    interaktif tahmin modülleri.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.write("")

        selected_page = st.radio(
            "Navigasyon",
            [
                "🏠 Genel Bakış",
                "🎯 Tek Müşteri Tahmini",
                "📁 Toplu CSV Analizi",
                "📈 Model Performansı",
                "📚 Proje Bilgileri",
                "🧩 Akademi Ödevleri",
            ],
            label_visibility="collapsed",
        )

        st.divider()

        st.caption(
            "FINAL MODEL"
        )

        st.success(
            FINAL_MODEL_NAME
        )

        model_metric_col_1, model_metric_col_2 = (
            st.columns(2)
        )

        model_metric_col_1.metric(
            "ROC AUC",
            f"{FINAL_TEST_ROC_AUC:.3f}",
        )

        model_metric_col_2.metric(
            "Recall",
            f"{FINAL_TEST_RECALL:.3f}",
        )

        st.caption(
            "Branch: feature/churn-dashboard-v2"
        )

    return selected_page


def main() -> None:
    """Streamlit uygulamasını çalıştırır."""

    selected_page = render_sidebar()

    page_mapping = {
        "🏠 Genel Bakış": overview_page,
        "🎯 Tek Müşteri Tahmini": single_prediction_page,
        "📁 Toplu CSV Analizi": batch_prediction_page,
        "📈 Model Performansı": model_performance_page,
        "📚 Proje Bilgileri": project_information_page,
        "🧩 Akademi Ödevleri": assignments_page,
    }

    page_function = page_mapping.get(
        selected_page,
        overview_page,
    )

    page_function()


if __name__ == "__main__":
    main()