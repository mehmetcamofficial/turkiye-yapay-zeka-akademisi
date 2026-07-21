# Deney Planı

V1 uygulaması 100.000 satırlık sample, term-group validation ve beş adaylı karşılaştırmayı tamamladı. Aşağıdaki ilkeler V2 deneylerinde de geçerlidir.

- Hedef: `label`; birincil birim query-product çifti.
- Veri sızıntısı kontrolü: aynı çiftin split'ler arasında tekrarı engellenir; gerekirse query-grup split'i ayrıca değerlendirilir.
- Özellikler: normalize query/title, word/character TF-IDF, lexical overlap, uzunluk farkları ve güvenli katalog alanları.
- Baseline: Logistic Regression, LinearSVC, MultinomialNB.
- Ağırlıklar: `sample_weight` desteği estimator uyumluluğuna göre açıkça kaydedilir.
- Değerlendirme: Accuracy, Precision, Recall, F1, PR AUC; skor semantiği uygunsa ROC AUC.
- Validation: sabit random seed, stratified holdout, ardından CV ve sınırlı tuning.
- Analiz: confusion matrix, false positive/negative örnekleri, top terms ve category-level performans.
- Kabul: offline tekrar çalıştırılabilirlik, kaydedilmiş config/split metadata ve test setine yalnızca final erişim.
