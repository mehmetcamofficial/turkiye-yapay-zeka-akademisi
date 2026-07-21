"""Native unified-portfolio UI for the existing churn pipeline."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from portfolio.churn_service import (RAW_COLUMNS, predict_batch, prepare_model_input,
                                     sample_batch, validate_raw_batch)
from portfolio.config import CHURN_DIR, CHURN_MODEL_PATH
from portfolio.loaders import (load_csv_safe, load_image_path_safe,
                               load_json_safe, load_model_safe, load_text_safe)
from portfolio.project_registry import project_by_id
from portfolio.ui_components import (artifact_checklist, classification_report_frame, empty_state_panel,
                                     hero_panel, information_panel, metric_table,
                                     prediction_result_card, render_safe_table, section_heading)


def _model_result():
    return load_model_safe(CHURN_MODEL_PATH)


def _single_prediction() -> None:
    model_result = _model_result()
    if not model_result.ok:
        empty_state_panel("Model kullanılamıyor", model_result.public_message)
        return
    with st.form("portfolio_churn_single"):
        left, right = st.columns(2)
        with left:
            gender = st.selectbox("Cinsiyet", ["Female", "Male"])
            senior = st.selectbox("Senior Citizen", ["No", "Yes"])
            partner = st.selectbox("Partner", ["No", "Yes"])
            dependents = st.selectbox("Dependents", ["No", "Yes"])
            tenure = st.number_input("Tenure Months", min_value=0, max_value=120, value=12)
            phone = st.selectbox("Phone Service", ["Yes", "No"])
            multiple = st.selectbox("Multiple Lines", ["No", "Yes", "No phone service"])
            internet = st.selectbox("Internet Service", ["Fiber optic", "DSL", "No"])
            security = st.selectbox("Online Security", ["No", "Yes", "No internet service"])
            backup = st.selectbox("Online Backup", ["No", "Yes", "No internet service"])
        with right:
            protection = st.selectbox("Device Protection", ["No", "Yes", "No internet service"])
            support = st.selectbox("Tech Support", ["No", "Yes", "No internet service"])
            tv = st.selectbox("Streaming TV", ["No", "Yes", "No internet service"])
            movies = st.selectbox("Streaming Movies", ["No", "Yes", "No internet service"])
            contract = st.selectbox("Contract", ["Month-to-month", "One year", "Two year"])
            paperless = st.selectbox("Paperless Billing", ["Yes", "No"])
            payment = st.selectbox("Payment Method", ["Electronic check", "Mailed check", "Bank transfer (automatic)", "Credit card (automatic)"])
            monthly = st.number_input("Monthly Charges", min_value=0.0, value=75.0)
            total = st.number_input("Total Charges", min_value=0.0, value=900.0)
            cltv = st.number_input("CLTV", min_value=0.0, value=3500.0)
        submitted = st.form_submit_button("Churn Riskini Hesapla")
    if submitted:
        raw = pd.DataFrame([dict(zip(RAW_COLUMNS, [gender, senior, partner, dependents, tenure, phone, multiple,
            internet, security, backup, protection, support, tv, movies, contract, paperless, payment,
            monthly, total, cltv]))])
        try:
            prepared = prepare_model_input(raw)
            prediction = int(model_result.model.predict(prepared)[0])
            probability = float(model_result.model.predict_proba(prepared)[0, 1])
            risk = "Yüksek" if probability >= .7 else ("Orta" if probability >= .4 else "Düşük")
            prediction_result_card("Churn tahmini", "Risk var" if prediction else "Risk düşük",
                                   f"Churn olasılığı {probability:.1%} · Risk seviyesi: {risk}. Sonuç eğitim amaçlıdır.")
        except Exception:
            st.error("Tahmin oluşturulamadı. Girdi değerlerini kontrol edin.")


def _read_uploaded_csv(uploaded) -> pd.DataFrame | None:
    try:
        frame = pd.read_csv(uploaded)
        if len(frame.columns) == 1:
            uploaded.seek(0)
            alternate = pd.read_csv(uploaded, sep=";")
            if len(alternate.columns) > 1:
                frame = alternate
        return frame
    except (UnicodeError, pd.errors.ParserError, ValueError):
        st.error("CSV dosyası okunamadı. UTF-8, virgül veya noktalı virgül formatını kontrol edin.")
        return None


def _batch_prediction() -> None:
    template = sample_batch()
    st.download_button("Örnek CSV şablonunu indir", template.to_csv(index=False).encode("utf-8"),
                       "churn_batch_template.csv", "text/csv")
    uploaded = st.file_uploader("Müşteri CSV dosyası", type="csv", key="portfolio_churn_batch")
    if uploaded is None:
        information_panel("Toplu tahmin", "Kimlik ve diğer ek sütunlar sonuçta korunur. Zorunlu model sütunları şablonda bulunur.")
        return
    frame = _read_uploaded_csv(uploaded)
    if frame is None:
        return
    errors = validate_raw_batch(frame)
    if errors:
        for error in errors: st.warning(error)
        return
    st.caption(f"{len(frame)} kayıt doğrulandı.")
    render_safe_table(frame, max_rows=25)
    if st.button("Toplu Tahmini Başlat", key="portfolio_churn_batch_run"):
        model_result = _model_result()
        if not model_result.ok:
            st.error(model_result.public_message); return
        try:
            result = predict_batch(model_result.model, frame)
            st.session_state["churn_batch_result"] = result
        except Exception:
            st.error("Toplu tahmin tamamlanamadı. CSV değerlerini kontrol edin.")
    result = st.session_state.get("churn_batch_result")
    if isinstance(result, pd.DataFrame):
        render_safe_table(result, max_rows=100, download_name=None)
        high_risk = result[result["Risk Band"] == "Yüksek"]
        col1, col2 = st.columns(2)
        with col1:
            st.download_button("Tüm sonuçları indir", result.to_csv(index=False).encode("utf-8"), "churn_predictions.csv", "text/csv")
        with col2:
            st.download_button("Yüksek risk listesini indir", high_risk.to_csv(index=False).encode("utf-8"), "high_risk_customers.csv", "text/csv")
        st.caption(f"Yüksek riskli kayıt: {len(high_risk)}")


def _performance() -> None:
    reports = [("Final test metrikleri", "test_metrics.csv"), ("Validation sonuçları", "validation_results.csv"),
               ("Cross-validation", "cross_validation_results.csv"), ("GridSearchCV sonuçları", "hyperparameter_search_results.csv")]
    for title, filename in reports:
        section_heading(title); metric_table(load_csv_safe(str(CHURN_DIR / "outputs" / filename)))
    section_heading("En iyi hiperparametreler")
    params = load_json_safe(str(CHURN_DIR / "outputs/best_hyperparameters.json"))
    if params: st.json(params)
    else: empty_state_panel("Rapor bulunamadı", "Hiperparametre JSON artifact’ı mevcut değil.")
    report = load_text_safe(str(CHURN_DIR / "outputs/classification_report.txt"))
    if report:
        section_heading("Sınıflandırma raporu", "Sınıf, macro ve weighted ortalamalar.")
        metric_table(classification_report_frame(report))
    columns = st.columns(2)
    for column, filename, title in [(columns[0], "confusion_matrix.png", "Confusion Matrix"), (columns[1], "roc_curve.png", "ROC Curve")]:
        with column:
            image = load_image_path_safe(str(CHURN_DIR / "outputs" / filename))
            if image: st.image(image, caption=title, use_column_width=True)


def _explainability() -> None:
    section_heading("Seçilen özellikler")
    selected = load_csv_safe(str(CHURN_DIR / "outputs/selected_features.csv"))
    if "selected" in selected: selected = selected[selected["selected"] == True]  # noqa: E712
    metric_table(selected)
    section_heading("Katsayılar ve özellik etkileri")
    metric_table(load_csv_safe(str(CHURN_DIR / "outputs/feature_importance.csv")))
    st.caption("Katsayı ve önemler istatistiksel ilişkiyi gösterir; nedensellik kanıtı değildir.")


def render() -> None:
    hero_panel("Customer Churn", "Telekom müşteri kaybı için doğrulanmış pipeline, canlı tahmin ve model değerlendirmesi.", "MACHINE LEARNING")
    tabs = st.tabs(["Genel Bakış", "Tekli Tahmin", "Toplu CSV Analizi", "Model Performansı", "Açıklanabilirlik", "Metodoloji", "Teknik Detaylar"])
    project = project_by_id("churn")
    with tabs[0]:
        metrics = load_csv_safe(str(CHURN_DIR / "outputs/test_metrics.csv"))
        columns = st.columns(4)
        for column, name in zip(columns, ["Accuracy", "Recall", "F1 Score", "ROC AUC"]):
            value = float(metrics.iloc[0][name]) if not metrics.empty and name in metrics else None
            column.metric(name, "—" if value is None else f"{value:.4f}")
        information_panel("Amaç", project["description"])
        information_panel("Veri ve model", f"{project['dataset']} ({project['dataset_size']}) · {project['final_model']}")
        information_panel("İş akışı", "EDA → feature engineering → preprocessing → feature selection → 5-fold CV → tuning → dokunulmamış test")
        information_panel("Sınırlamalar", "; ".join(project["limitations"]))
    with tabs[1]: _single_prediction()
    with tabs[2]: _batch_prediction()
    with tabs[3]: _performance()
    with tabs[4]: _explainability()
    with tabs[5]:
        information_panel("Preprocessing", "Sayısal median imputation ve scaling; kategorik most-frequent imputation ve OneHotEncoder. Tüm adımlar pipeline içinde fit edilir.")
        information_panel("Model seçimi", "Dört aday model 5-fold stratified CV ve validation sonuçlarıyla karşılaştırıldı; test seti yalnızca final değerlendirmede kullanıldı.")
    with tabs[6]:
        with st.expander("Artifact kontrol listesi", expanded=False): artifact_checklist(project)
        with st.expander("Final rapor", expanded=False):
            summary = load_text_safe(str(CHURN_DIR / "outputs/final_summary.txt"))
            st.text(summary) if summary else st.info("Final rapor mevcut değil.")
