# Trendyol Search & Product Intelligence — Proje Planı

## Durum

V1 leakage-aware baseline tamamlandı; üretimleştirme ve V2 semantik geliştirmeler planlandı. Doğrulanmış bounded sonuçlar `RESULTS.md` içindedir.

## Amaç

Yerel Trendyol katalog, sorgu ve relevance tablolarından query-product alaka sınıflandırması; katalog ve sorgu profilleme; batch ve canlı scoring için tekrar üretilebilir bir pipeline tasarlamak.

## Aşamalar

1. Kaydedilmiş veri profili ve kalite kontrollerini kabul kriterlerine bağla.
2. Query/title normalizasyonu, uzunluk ve lexical-overlap özelliklerini üret.
3. Stratified validation split ve class/sample-weight politikasını dondur.
4. TF-IDF ile Logistic Regression, LinearSVC ve MultinomialNB baseline'larını karşılaştır.
5. Cross-validation ve kontrollü hiperparametre araması yap.
6. Accuracy, Precision, Recall, F1, PR AUC ve uygunsa ROC AUC raporla.
7. Confusion matrix, FP/FN, top terms ve kategori-seviyesi performansı incele.
8. Final pipeline artifact'ı, batch scoring ve Streamlit canlı scoring modülünü doğrula.

## Teslimler

Model artifact, test/validation tabloları, hata analizi, model card, reproducibility metadata ve deployment contract. Tüm metrikler yalnızca deney tamamlandıktan sonra gerçek çıktılardan alınır.
