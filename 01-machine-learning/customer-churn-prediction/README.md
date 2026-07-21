# Müşteri Kaybı Tahmini (Customer Churn Prediction)

## 1. Proje Başlığı

**Telekomünikasyon Müşteri Kaybı (Churn) Tahmini**
Türkiye Yapay Zeka Akademisi — Makine Öğrenmesi Final Ödevi

## 2. Öğrenci / Proje Bağlamı

Bu proje, Türkiye Yapay Zeka Akademisi Makine Öğrenmesi dersi kapsamında hazırlanmış uçtan uca bir **ikili sınıflandırma** çalışmasıdır. Amaç; veri keşfi, sızıntısız ön işleme, özellik mühendisliği, özellik seçimi, model karşılaştırma, çapraz doğrulama, hiperparametre ayarı, bağımsız test değerlendirmesi ve Streamlit arayüzü ile tahmin sunumunu tek bir yeniden üretilebilir pipeline içinde birleştirmektir.

## 3. Problem Tanımı

Telekomünikasyon şirketlerinde mevcut müşteriyi elde tutmak, genellikle yeni müşteri edinmekten daha düşük maliyetlidir. Bu çalışmada müşteri profili, hizmet kullanımı ve faturalandırma bilgileri kullanılarak müşterinin hizmetten ayrılma olasılığı tahmin edilir.

İş değeri:

- Yüksek riskli müşterilerin önceliklendirilmesi
- Retention kampanyalarının hedeflenmesi
- Destek görüşmelerinin planlanması
- Sözleşme yenileme tekliflerinin optimize edilmesi

## 4. Veri Seti Açıklaması ve Kaynak

| Özellik | Değer |
| --- | --- |
| Dosya | `data/telco_customer_churn.csv` |
| Ayırıcı | `;` (noktalı virgül) |
| Ham boyut | 7043 satır × 33 sütun |
| Temizlenmiş boyut | 7043 satır × 25 sütun |
| Bağlam | Telekomünikasyon müşteri kaydı |
| Kaynak tipi | Akademik / eğitim amaçlı Telco Customer Churn veri seti |

Veri seti; demografi, hizmet abonelikleri, sözleşme türü, ödeme yöntemi, aylık/toplam ücret ve churn etiketlerini içerir.

## 5. Sınıflandırma Hedefi

| Değer | Anlam |
| --- | --- |
| `0` | Müşterinin kalması bekleniyor (No Churn) |
| `1` | Müşterinin ayrılma riski var (Churn) |

Hedef sütun: **`Churn Value`**

Hedef dağılımı:

| Sınıf | Adet | Oran |
| --- | ---: | ---: |
| 0 — No Churn | 5174 | %73.46 |
| 1 — Churn | 1869 | %26.54 |

## 6. Depo Yapısı

```text
customer-churn-prediction/
├── app.py                      # Streamlit dashboard
├── train_model.py              # Uçtan uca eğitim pipeline'ı
├── requirements.txt
├── README.md
├── data/
│   └── telco_customer_churn.csv
├── models/
│   └── churn_model.pkl         # Final sklearn pipeline
└── outputs/
    ├── data_profile.txt
    ├── outlier_analysis.csv
    ├── selected_features.csv
    ├── cross_validation_results.csv
    ├── validation_results.csv
    ├── hyperparameter_search_results.csv
    ├── best_hyperparameters.json
    ├── test_metrics.csv
    ├── classification_report.txt
    ├── confusion_matrix.png
    ├── roc_curve.png
    ├── feature_importance.csv
    └── final_summary.txt
```

## 7. Kurulum

Python **3.12** önerilir.

```bash
cd 01-machine-learning/customer-churn-prediction
python3.12 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Bağımlılıklar:

| Paket | Sürüm |
| --- | --- |
| numpy | 1.26.4 |
| pandas | 2.2.3 |
| scikit-learn | 1.5.2 |
| matplotlib | 3.9.2 |
| streamlit | 1.39.0 |
| joblib | 1.4.2 |

## 8. Eğitim Talimatları

Proje kökünden:

```bash
python 01-machine-learning/customer-churn-prediction/train_model.py
```

veya proje dizininden:

```bash
python train_model.py
```

Eğitim akışı:

1. Veri yükleme ve EDA
2. Eksik değer / kodlama / sızıntı önleme
3. Aykırı değer analizi (silmeden)
4. Özellik mühendisliği
5. %60 / %20 / %20 stratified bölme
6. 5-fold StratifiedKFold çapraz doğrulama
7. Doğrulama seti model karşılaştırması
8. GridSearchCV hiperparametre ayarı
9. Train + validation ile final eğitim
10. Tek seferlik test değerlendirmesi
11. Açıklanabilirlik ve özet rapor

## 9. Streamlit Talimatları

```bash
streamlit run 01-machine-learning/customer-churn-prediction/app.py
```

Sayfalar:

| Sayfa | İşlev |
| --- | --- |
| Genel Bakış | Proje özeti ve test metrikleri |
| Tek Müşteri Tahmini | Form ile bireysel churn skoru |
| Toplu CSV Analizi | Çoklu müşteri tahmini ve indirme |
| Model Performansı | CV, validation, hiperparametre, özellikler, test görselleri |
| Proje Bilgileri | Yöntem ve sınırlamalar |
| Akademi Ödevleri | Portföy yol haritası |

## 10. Deployment Linki

Streamlit Cloud / public deployment bağlantısı (varsa buraya eklenir):

> **Deployment linki:** _henüz yayınlanmadı / placeholder_

Yerel çalıştırma için yukarıdaki Streamlit komutu yeterlidir.

## 11. Veri İncelemesi (EDA)

`outputs/data_profile.txt` dosyasında şunlar kaydedilir:

- İlk 5 satır
- Veri boyutu
- Sütun adları
- Veri tipleri
- Betimleyici istatistikler
- Eksik değer sayıları
- Hedef dağılımı

Özet:

| Madde | Sonuç |
| --- | --- |
| Ham boyut | 7043 × 33 |
| Temizlenmiş boyut | 7043 × 25 |
| Churn oranı | %26.54 |

## 12. Eksik Değerler

Eksik değerler **sklearn Pipeline içinde**, yalnızca eğitim verisine `fit` edilerek doldurulur:

| Sütun tipi | Strateji |
| --- | --- |
| Sayısal | `SimpleImputer(strategy="median")` |
| Kategorik | `SimpleImputer(strategy="most_frequent")` |

Böylece validation/test bilgisinin imputer’a sızması engellenir.

## 13. Kodlama (Encoding)

Kategorik değişkenler pipeline içinde şu şekilde kodlanır:

```text
OneHotEncoder(handle_unknown="ignore", sparse_output=False)
```

Sayısal değişkenler için `StandardScaler` kullanılır. Tüm dönüşümler final `churn_model.pkl` pipeline’ının parçasıdır; Streamlit tahminleri aynı dönüşümleri otomatik uygular.

## 14. Aykırı Değer Analizi

IQR yöntemi ile incelenen sütunlar:

- Tenure Months
- Monthly Charges
- Total Charges
- Average Monthly Spend

Sonuç dosyası: `outputs/outlier_analysis.csv`

| Sütun | Outlier adedi | Oran |
| --- | ---: | ---: |
| Tenure Months | 0 | %0.00 |
| Monthly Charges | 0 | %0.00 |
| Total Charges | 0 | %0.00 |
| Average Monthly Spend | 0 | %0.00 |

**Politika:** Aykırı değerler otomatik silinmez. Aşırı değerler meşru müşteri davranışını temsil edebilir. Pipeline median imputation + scaling ile robust davranır; satır silme yapılmaz.

## 15. Özellik Mühendisliği

Hedef kullanılmadan üretilen özellikler:

| Özellik | Tanım |
| --- | --- |
| Average Monthly Spend | `Total Charges / Tenure Months` (tenure=0 ise Monthly Charges) |
| Is Long Term Customer | Tenure Months ≥ 24 ise 1 |
| Has Support Services | Tech Support veya Online Security = Yes ise 1 |
| High Monthly Charge | Monthly Charges > **70** ise 1 (sabit domain eşiği) |

`High Monthly Charge` için tüm veri seti medyanı kullanılmaz; böylece train/test sızıntısı ve eğitim–çıkarım tutarsızlığı önlenir. Streamlit arayüzü aynı kuralı uygular.

## 16. Özellik Seçimi

Pipeline adımı:

```text
SelectFromModel(
    LogisticRegression(penalty="l1", solver="liblinear", ...),
    threshold="median"
)
```

- Preprocessing sonrası, model öncesinde yer alır
- Yalnızca eğitim katmanlarına fit edilir
- One-hot sonrası özellik uzayında çalışır

Çıktı: `outputs/selected_features.csv`
Seçilen özellik sayısı: **26 / 51** (encode sonrası)

## 17. Train–Validation–Test Bölünmesi

| Küme | Oran | Satır | Kullanım |
| --- | ---: | ---: | --- |
| Train | %60 | 4225 | CV, model karşılaştırma, tuning |
| Validation | %20 | 1409 | Model seçimi / doğrulama metrikleri |
| Test | %20 | 1409 | Yalnızca final değerlendirme |

- `stratify=y`
- `random_state=42`
- Test setine tuning veya model seçiminde dokunulmaz

## 18. Karşılaştırılan Modeller

1. Logistic Regression
2. Decision Tree
3. Random Forest
4. Gradient Boosting

Karşılaştırma metrikleri:

- Accuracy
- Precision
- Recall
- F1 Score
- ROC AUC
- Eğitim süresi

## 19. Çapraz Doğrulama

- Yöntem: `StratifiedKFold(n_splits=5, shuffle=True, random_state=42)`
- Yalnızca **eğitim** verisi üzerinde
- Dosya: `outputs/cross_validation_results.csv`

| Model | CV ROC AUC Mean | CV ROC AUC Std | CV F1 Mean | CV F1 Std |
| --- | ---: | ---: | ---: | ---: |
| Gradient Boosting | 0.8611 | 0.0163 | 0.6121 | 0.0317 |
| Random Forest | 0.8587 | 0.0128 | 0.6435 | 0.0221 |
| Logistic Regression | 0.8558 | 0.0213 | 0.6421 | 0.0238 |
| Decision Tree | 0.8181 | 0.0188 | 0.6066 | 0.0216 |

## 20. Hiperparametre Ayarı

Seçilen model üzerinde:

- `GridSearchCV`
- `scoring="roc_auc"`
- 5-fold StratifiedKFold
- `n_jobs=-1`
- `refit=True`

Seçilen model: **Logistic Regression** (doğrulama ROC AUC öncelikli)

En iyi parametreler (`outputs/best_hyperparameters.json`):

| Parametre | Değer |
| --- | --- |
| model__C | 2.0 |
| model__class_weight | null |
| model__solver | lbfgs |
| En iyi CV ROC AUC | 0.8561 |

Arama sonuçları: `outputs/hyperparameter_search_results.csv`

## 21. Doğrulama Sonuçları

Dosya: `outputs/validation_results.csv`
(Doğrulama metrikleri + CV özeti birlikte)

| Model | Accuracy | Precision | Recall | F1 | ROC AUC | Training Time (s) | CV ROC AUC Mean |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Logistic Regression | 0.7466 | 0.5144 | 0.8128 | 0.6301 | **0.8659** | 0.16 | 0.8558 |
| Gradient Boosting | 0.8084 | 0.6699 | 0.5481 | 0.6029 | 0.8644 | 0.94 | 0.8611 |
| Random Forest | 0.7935 | 0.5892 | 0.7326 | 0.6532 | 0.8639 | 0.43 | 0.8587 |
| Decision Tree | 0.7289 | 0.4936 | 0.8235 | 0.6172 | 0.8298 | 0.20 | 0.8181 |

Model seçimi: validation ROC AUC + CV özeti; test seti kullanılmadı.

## 22. Final Test Sonuçları

Tuned pipeline, train + validation birleşiminde yeniden eğitilmiş; test seti **tek kez** değerlendirilmiştir.

| Metrik | Değer |
| --- | ---: |
| Model | Logistic Regression |
| Accuracy | 0.7942 |
| Precision | 0.6228 |
| Recall | 0.5695 |
| F1 Score | 0.5950 |
| ROC AUC | 0.8440 |

Dosya: `outputs/test_metrics.csv`

## 23. Confusion Matrix ve ROC Eğrisi

- Confusion matrix: `outputs/confusion_matrix.png`
- ROC curve: `outputs/roc_curve.png`
- Classification report: `outputs/classification_report.txt`

Sınıflandırma raporu özeti:

| Sınıf | Precision | Recall | F1 | Support |
| --- | ---: | ---: | ---: | ---: |
| No Churn | 0.8491 | 0.8754 | 0.8620 | 1035 |
| Churn | 0.6228 | 0.5695 | 0.5950 | 374 |
| Accuracy |  |  | 0.7942 | 1409 |

## 24. Açıklanabilirlik (Explainability)

Logistic Regression katsayıları, L1 feature selection sonrası seçilen özellikler üzerinden çıkarılır.

Dosya: `outputs/feature_importance.csv`

Örnek güçlü ilişkiler:

| Özellik | Yön | Yorum |
| --- | --- | --- |
| Dependents = Yes | Churn riskini azaltır | Aile/bağlılık sinyali |
| Tenure Months | Churn riskini azaltır | Uzun süreli müşteri |
| Contract = Month-to-month | Churn riskini artırır | Kısa vadeli sözleşme |
| Contract = Two year | Churn riskini azaltır | Uzun sözleşme |
| Payment Method = Electronic check | Churn riskini artırır | Ödeme kanalı sinyali |

**Önemli:** Bu sonuçlar istatistiksel ilişkidir; **nedensellik değildir**.

## 25. Sınırlamalar

- Veri seti tek bir telekom bağlamını / coğrafyayı temsil edebilir; genelleme garantisi yoktur.
- Sınıf dengesizliği vardır (~%26.5 churn); Precision/Recall dengesi dikkatle okunmalıdır.
- Zamanla kavram kayması (concept drift) oluşabilir; model izlenmeli ve periyodik yeniden eğitilmelidir.
- Tahminler nedensel sonuç değildir; “neden churn oldu?” sorusuna tek başına cevap vermez.
- Varsayılan karar eşiği (0.5) iş maliyetlerine göre optimize edilmelidir.
- False positive (gereksiz retention maliyeti) ile false negative (kaçırılan churn) maliyetleri farklıdır.
- Proje eğitim / portföy amaçlıdır; tamamen otomatik müşteri kararları için tek başına kullanılmamalıdır.

## 26. Yeniden Üretilebilirlik

| Madde | Değer |
| --- | --- |
| random_state | 42 |
| Split | stratified 60/20/20 |
| CV | StratifiedKFold 5, shuffle=True |
| Python | 3.12 |
| scikit-learn | 1.5.2 |
| Final artifact | `models/churn_model.pkl` (tam pipeline) |
| Yol standardı | `Path(__file__).resolve().parent` |

Aynı ortam ve komutlarla metrikler yeniden üretilebilir.

## 27. Sonuç

Bu proje, müşteri kaybı tahminini uçtan uca bir makine öğrenmesi final ödevi standardında ele alır:

- Sızıntısız ön işleme ve özellik mühendisliği
- Pipeline içi özellik seçimi
- Dört aday model + 5-fold CV
- GridSearchCV ile hiperparametre ayarı
- Bağımsız test değerlendirmesi
- Katsayı tabanlı açıklanabilirlik
- Streamlit ile tekli / toplu tahmin arayüzü

Final model **Logistic Regression** olup test ROC AUC değeri yaklaşık **0.844**’tür. Model, retention ekiplerine olasılıksal bir risk skoru sunar; nihai iş kararları eşik optimizasyonu ve domain bilgisi ile desteklenmelidir.
