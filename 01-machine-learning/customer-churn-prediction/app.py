"""
Türkiye Yapay Zeka Akademisi
Customer Churn Prediction - Streamlit Application

Run:
streamlit run 01-machine-learning/customer-churn-prediction/app.py
"""

from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import streamlit as st


BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "models" / "churn_model.pkl"
TEST_METRICS_PATH = BASE_DIR / "outputs" / "test_metrics.csv"
VALIDATION_RESULTS_PATH = BASE_DIR / "outputs" / "validation_results.csv"
CONFUSION_MATRIX_PATH = BASE_DIR / "outputs" / "confusion_matrix.png"
ROC_CURVE_PATH = BASE_DIR / "outputs" / "roc_curve.png"


st.set_page_config(
    page_title="Customer Churn Prediction",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


CUSTOM_CSS = """
<style>
    .stApp {
        background-color: #f7f9fc;
    }

    .main-title {
        font-size: 2.5rem;
        font-weight: 800;
        margin-bottom: 0.2rem;
    }

    .subtitle {
        font-size: 1.05rem;
        color: #5f6b7a;
        margin-bottom: 2rem;
    }

    .metric-card {
        background: white;
        border: 1px solid #e7ebf0;
        border-radius: 16px;
        padding: 1.2rem;
        box-shadow: 0 4px 16px rgba(20, 30, 55, 0.06);
        min-height: 135px;
    }

    .metric-label {
        color: #667085;
        font-size: 0.9rem;
        margin-bottom: 0.4rem;
    }

    .metric-value {
        font-size: 1.9rem;
        font-weight: 750;
    }

    .result-card {
        background: white;
        border: 1px solid #e7ebf0;
        border-radius: 18px;
        padding: 1.5rem;
        box-shadow: 0 5px 20px rgba(20, 30, 55, 0.07);
        margin-top: 1rem;
    }

    .risk-low {
        color: #0f9d58;
        font-weight: 800;
    }

    .risk-medium {
        color: #f59e0b;
        font-weight: 800;
    }

    .risk-high {
        color: #dc2626;
        font-weight: 800;
    }

    div[data-testid="stMetric"] {
        background-color: white;
        border: 1px solid #e7ebf0;
        padding: 1rem;
        border-radius: 14px;
    }

    div.stButton > button {
        width: 100%;
        border-radius: 12px;
        height: 3rem;
        font-weight: 700;
    }
</style>
"""

st.markdown(
    CUSTOM_CSS,
    unsafe_allow_html=True,
)


@st.cache_resource
def load_model():
    """Load the trained machine learning pipeline."""

    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Model dosyası bulunamadı: {MODEL_PATH}"
        )

    return joblib.load(MODEL_PATH)


@st.cache_data
def load_test_metrics() -> pd.DataFrame:
    """Load test performance metrics."""

    if not TEST_METRICS_PATH.exists():
        return pd.DataFrame()

    return pd.read_csv(TEST_METRICS_PATH)


@st.cache_data
def load_validation_results() -> pd.DataFrame:
    """Load model validation comparison results."""

    if not VALIDATION_RESULTS_PATH.exists():
        return pd.DataFrame()

    return pd.read_csv(VALIDATION_RESULTS_PATH)


def calculate_engineered_features(
    tenure_months: int,
    monthly_charges: float,
    total_charges: float,
    tech_support: str,
    online_security: str,
) -> dict[str, float]:
    """Calculate the same engineered features used during training."""

    if tenure_months > 0:
        average_monthly_spend = (
            total_charges / tenure_months
        )
    else:
        average_monthly_spend = monthly_charges

    is_long_term_customer = int(
        tenure_months >= 24
    )

    has_support_services = int(
        tech_support == "Yes"
        or online_security == "Yes"
    )

    high_monthly_charge = int(
        monthly_charges > 70
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
    """Create a one-row dataframe for prediction."""

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
        [customer_data]
    )


def get_risk_information(
    churn_probability: float,
) -> tuple[str, str, str]:
    """Return risk level, CSS class and recommendation."""

    if churn_probability < 0.35:
        return (
            "Düşük Risk",
            "risk-low",
            (
                "Müşterinin ayrılma olasılığı düşük görünüyor. "
                "Mevcut müşteri deneyimi korunabilir."
            ),
        )

    if churn_probability < 0.65:
        return (
            "Orta Risk",
            "risk-medium",
            (
                "Müşteri yakından takip edilmelidir. "
                "Kişiselleştirilmiş teklif veya memnuniyet görüşmesi önerilir."
            ),
        )

    return (
        "Yüksek Risk",
        "risk-high",
        (
            "Müşterinin ayrılma riski yüksek. "
            "Sadakat kampanyası, özel indirim veya destek görüşmesi önerilir."
        ),
    )


def display_test_metrics() -> None:
    """Display final model metrics."""

    metrics_df = load_test_metrics()

    if metrics_df.empty:
        st.info(
            "Test metrikleri henüz oluşturulmamış."
        )
        return

    row = metrics_df.iloc[0]

    st.subheader(
        "Final Model Performance"
    )

    columns = st.columns(5)

    metric_mapping = [
        ("Accuracy", "Accuracy"),
        ("Precision", "Precision"),
        ("Recall", "Recall"),
        ("F1 Score", "F1 Score"),
        ("ROC AUC", "ROC AUC"),
    ]

    for column, (
        label,
        metric_name,
    ) in zip(
        columns,
        metric_mapping,
    ):
        value = float(
            row[metric_name]
        )

        column.metric(
            label=label,
            value=f"{value:.3f}",
        )


def display_model_comparison() -> None:
    """Display validation model comparison table."""

    validation_df = load_validation_results()

    if validation_df.empty:
        st.info(
            "Model karşılaştırma sonuçları bulunamadı."
        )
        return

    display_df = validation_df.copy()

    numeric_columns = [
        "Accuracy",
        "Precision",
        "Recall",
        "F1 Score",
        "ROC AUC",
        "Training Time",
    ]

    available_columns = [
        column
        for column in numeric_columns
        if column in display_df.columns
    ]

    display_df[available_columns] = (
        display_df[available_columns]
        .round(4)
    )

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
    )


def display_model_visuals() -> None:
    """Display confusion matrix and ROC curve."""

    left_column, right_column = st.columns(2)

    with left_column:
        st.subheader(
            "Confusion Matrix"
        )

        if CONFUSION_MATRIX_PATH.exists():
            st.image(
                str(CONFUSION_MATRIX_PATH),
                use_container_width=True,
            )
        else:
            st.info(
                "Confusion matrix görseli bulunamadı."
            )

    with right_column:
        st.subheader(
            "ROC Curve"
        )

        if ROC_CURVE_PATH.exists():
            st.image(
                str(ROC_CURVE_PATH),
                use_container_width=True,
            )
        else:
            st.info(
                "ROC curve görseli bulunamadı."
            )


def prediction_page() -> None:
    """Render the customer prediction page."""

    st.markdown(
        '<div class="main-title">Customer Churn Prediction</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        (
            '<div class="subtitle">'
            "Müşteri özelliklerini girerek müşterinin hizmetten "
            "ayrılma olasılığını tahmin edin."
            "</div>"
        ),
        unsafe_allow_html=True,
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
            )
        )

        st.stop()

    with st.form(
        "customer_prediction_form"
    ):
        st.subheader(
            "Müşteri Profili"
        )

        profile_col_1, profile_col_2, profile_col_3 = (
            st.columns(3)
        )

        with profile_col_1:
            gender = st.selectbox(
                "Cinsiyet",
                [
                    "Male",
                    "Female",
                ],
            )

            senior_citizen = st.selectbox(
                "Yaşlı müşteri",
                [
                    "No",
                    "Yes",
                ],
            )

            partner = st.selectbox(
                "Partneri var mı?",
                [
                    "No",
                    "Yes",
                ],
            )

        with profile_col_2:
            dependents = st.selectbox(
                "Bakmakla yükümlü olduğu kişi var mı?",
                [
                    "No",
                    "Yes",
                ],
            )

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
                max_value=10000.0,
                value=4000.0,
                step=100.0,
            )

        with profile_col_3:
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

            payment_method = st.selectbox(
                "Ödeme yöntemi",
                [
                    "Electronic check",
                    "Mailed check",
                    "Bank transfer (automatic)",
                    "Credit card (automatic)",
                ],
            )

        st.divider()

        st.subheader(
            "Hizmet Bilgileri"
        )

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

        st.divider()

        st.subheader(
            "Faturalandırma Bilgileri"
        )

        billing_col_1, billing_col_2 = (
            st.columns(2)
        )

        with billing_col_1:
            monthly_charges = st.number_input(
                "Aylık ücret",
                min_value=0.0,
                max_value=200.0,
                value=70.0,
                step=1.0,
            )

        estimated_total = (
            monthly_charges * tenure_months
        )

        with billing_col_2:
            total_charges = st.number_input(
                "Toplam ücret",
                min_value=0.0,
                max_value=20000.0,
                value=float(
                    estimated_total
                ),
                step=10.0,
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

        risk_level, risk_class, recommendation = (
            get_risk_information(
                probability
            )
        )

        st.markdown(
            '<div class="result-card">',
            unsafe_allow_html=True,
        )

        st.subheader(
            "Tahmin Sonucu"
        )

        result_col_1, result_col_2, result_col_3 = (
            st.columns(3)
        )

        with result_col_1:
            st.metric(
                "Churn Olasılığı",
                f"%{probability * 100:.1f}",
            )

        with result_col_2:
            st.metric(
                "Tahmin",
                (
                    "Ayrılabilir"
                    if prediction == 1
                    else "Kalması Bekleniyor"
                ),
            )

        with result_col_3:
            st.markdown(
                (
                    f"### Risk Seviyesi\n"
                    f'<span class="{risk_class}">'
                    f"{risk_level}"
                    "</span>"
                ),
                unsafe_allow_html=True,
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

        st.info(
            recommendation
        )

        with st.expander(
            "Tahminde kullanılan müşteri verilerini göster"
        ):
            st.dataframe(
                customer_df,
                use_container_width=True,
                hide_index=True,
            )

        st.markdown(
            "</div>",
            unsafe_allow_html=True,
        )


def model_performance_page() -> None:
    """Render model performance page."""

    st.markdown(
        '<div class="main-title">Model Performance</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        (
            '<div class="subtitle">'
            "Doğrulama karşılaştırması ve final test performansı."
            "</div>"
        ),
        unsafe_allow_html=True,
    )

    display_test_metrics()

    st.divider()

    st.subheader(
        "Validation Model Comparison"
    )

    display_model_comparison()

    st.divider()

    display_model_visuals()


def project_information_page() -> None:
    """Render project information page."""

    st.markdown(
        '<div class="main-title">Project Information</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        (
            '<div class="subtitle">'
            "Customer churn prediction projesinin yöntem ve kapsam özeti."
            "</div>"
        ),
        unsafe_allow_html=True,
    )

    st.subheader(
        "Problem"
    )

    st.write(
        """
        Bu proje, telekomünikasyon müşterilerinin hizmetten ayrılma
        olasılığını makine öğrenmesi kullanarak tahmin etmeyi amaçlar.
        Tahmin sonuçları, yüksek riskli müşterilerin erken tespit edilerek
        müşteri kaybını azaltmaya yönelik aksiyonların planlanmasında
        kullanılabilir.
        """
    )

    st.subheader(
        "Kullanılan Modeller"
    )

    st.write(
        """
        - Logistic Regression
        - Decision Tree
        - Random Forest
        - Gradient Boosting
        """
    )

    st.subheader(
        "Değerlendirme Yaklaşımı"
    )

    st.write(
        """
        Veri seti stratified yöntemle eğitim, doğrulama ve test
        kümelerine ayrılmıştır. Modeller doğrulama ROC AUC değerine
        göre karşılaştırılmış, seçilen model eğitim ve doğrulama
        verileriyle yeniden eğitilmiş ve dokunulmamış test kümesinde
        değerlendirilmiştir.
        """
    )

    st.subheader(
        "Kullanılan Metrikler"
    )

    st.write(
        """
        - Accuracy
        - Precision
        - Recall
        - F1 Score
        - ROC AUC
        """
    )

    st.warning(
        (
            "Bu uygulama eğitim ve portföy amaçlıdır. "
            "Gerçek müşteriler hakkında otomatik karar vermek için "
            "tek başına kullanılmamalıdır."
        )
    )


def main() -> None:
    """Run the Streamlit application."""

    with st.sidebar:
        st.title(
            "Churn Analytics"
        )

        st.caption(
            "Machine Learning Dashboard"
        )

        selected_page = st.radio(
            "Sayfa",
            [
                "Müşteri Tahmini",
                "Model Performansı",
                "Proje Bilgileri",
            ],
        )

        st.divider()

        st.write(
            "Seçilen final model:"
        )

        st.success(
            "Logistic Regression"
        )

        st.write(
            "Test ROC AUC:"
        )

        st.metric(
            label="ROC AUC",
            value="0.844",
        )

    if selected_page == "Müşteri Tahmini":
        prediction_page()

    elif selected_page == "Model Performansı":
        model_performance_page()

    else:
        project_information_page()


if __name__ == "__main__":
    main()