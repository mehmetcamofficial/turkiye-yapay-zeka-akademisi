# AI & Data Intelligence Platform

## Yerel başlangıç

```bash
./.venv/bin/python -m streamlit run 01-machine-learning/portfolio_app.py
```

Uygulama Python/Streamlit tabanlıdır; Node.js veya npm gerektirmez. Tüm kontroller repository kökündeki `.venv` ile çalıştırılır.

## Runtime mimarisi

- Sayfa registry'si `portfolio_app.py` ve `portfolio/config.py` tarafından yönetilir.
- Tablo çıktıları `render_safe_table` üzerinden semantik HTML olarak render edilir; varsayılan yol PyArrow kullanmaz.
- Modeller yalnızca tahmin veya Model Registry sayfasında `st.cache_resource` ile yüklenir.
- Büyük Trendyol tabloları başlangıçta okunmaz. UI kaydedilmiş inventory ve bounded profil çıktılarını kullanır.
- Artifact Health okunabilirlik, yüklenebilirlik ve cache'lenmiş checksum durumunu raporlar.

## Trendyol uyarlaması

Ara çalışma, özgün transactional alanları uydurmak yerine gerçek ürün kataloğu ve query-product relevance şemasına uyarlandı. Profil metrikleri tablo başına deterministic ilk 20.000 satır olarak açıkça etiketlenir. Final proje henüz plan aşamasındadır ve model metriği içermez.

## Segmentation fault sorun giderme

Önceki çökme, karma pandas tablolarının Streamlit Arrow dönüşümüne girdiği `metric_table` yolunda oluşuyordu. Portfolyo tabloları artık Arrow dışı güvenli renderer kullanır. Kontrol için:

```bash
rg 'st\.(dataframe|table|data_editor)' 01-machine-learning/portfolio
PYTHONFAULTHANDLER=1 ./.venv/bin/python -m streamlit run 01-machine-learning/portfolio_app.py --server.fileWatcherType none
```

Sorun tekrarlanırsa Python traceback, açılan sayfa, paket sürümleri ve process exit code birlikte kaydedilmelidir; geniş paket yükseltmesi ilk müdahale değildir.

Türkiye Yapay Zeka Akademisi kapsamında geliştirilen makine öğrenmesi
modüllerini veri bilimi ara ödevi ve planlanan final projesiyle tek Streamlit
arayüzünde birleştiren uygulamalı portfolyodur.

## Çalıştırma

Python 3.12 ve proje bağımlılıklarını kurduktan sonra depo kökünden:

```bash
./.venv/bin/python -m streamlit run 01-machine-learning/portfolio_app.py
```

Bare `streamlit run` kullanmayın; komutun proje sanal ortamındaki NumPy,
scikit-learn ve Streamlit paketlerini kullanması model artifact uyumluluğu için
gereklidir.

Standalone proje uygulamaları korunmuştur:

```bash
./.venv/bin/python -m streamlit run 01-machine-learning/customer-churn-prediction/app.py
./.venv/bin/python -m streamlit run 01-machine-learning/regression-project/app.py
./.venv/bin/python -m streamlit run 01-machine-learning/nlp-project/app.py
```

## Projeler ve doğrulanmış test sonuçları

| Proje | Problem | Veri | Final model | Test metriği |
| --- | --- | --- | --- | --- |
| Customer Churn | Sınıflandırma | Telco Customer Churn, 7.043 × 33 | Logistic Regression | ROC AUC 0.8440 |
| California Housing | Regresyon | California Housing, 20.640 × 9 | Random Forest | RMSE 0.5121, R² 0.8087 |
| Sentiment Analysis | NLP sınıflandırma | UCI Sentiment, 3.000 × 3 | MultinomialNB | Accuracy 0.8191, F1 0.8212 |
| Customer Segmentation | Kümeleme | Henüz seçilmedi | — | Henüz başlanmadı |
| Model Deployment | MLOps | Uygulanamaz | — | Planlandı |

Veri bilimi bölümünde ara ödev notebook'u hazırdır ancak meşru yerel veri
bulunmadığı için durum `Veri Bekleniyor`; final projesi resmî brief gelene kadar
`Planlandı` durumundadır.

Bu değerler uygulama içinde hard-code edilmez; ilgili `outputs/test_metrics.csv`
dosyalarından okunur. Tablo, mevcut doğrulanmış artifact'ların dokümantasyon
özetidir.

## Veri kaynakları

- Churn: yerel Telco Customer Churn CSV; proje README'sindeki kapsam ve sınırlamalar
- Regresyon: scikit-learn California Housing / StatLib, 1990 U.S. Census
- NLP: UCI Sentiment Labelled Sentences, CC BY 4.0, İngilizce

Regresyon ve NLP projelerindeki `DATA_SOURCE.md` dosyaları kaynak, lisans,
checksum, hedef, preprocessing ve sınırlamaları açıklar. Normal eğitim yerel CSV
kullanır ve her çalıştırmada indirme yapmaz.

## Eğitim

```bash
python 01-machine-learning/customer-churn-prediction/train_model.py
python 01-machine-learning/regression-project/train_model.py
python 01-machine-learning/nlp-project/train_model.py
```

Modeller yalnızca bilinçli olarak yeniden eğitim gerektiğinde çalıştırılmalıdır.
Preprocessing ve feature selection adımları sklearn pipeline içinde fit edilir;
test setleri tuning sırasında kullanılmaz.

## Durum metodolojisi

`portfolio/project_registry.py` her proje için zorunlu model ve rapor dosyalarını
kontrol eder. Eksik dosya varsa proje tamamlandı gösterilmez. Metrikler CSV'den,
tuning bilgisi JSON'dan, metodoloji metni raporlardan yüklenir. Eksik veya bozuk
artifact tüm uygulamayı çökertmek yerine profesyonel boş durum bileşeni üretir.

## Sınırlamalar

Projeler eğitim/portfolyo amaçlıdır. Test metrikleri farklı problem tipleri
arasında doğrudan kıyaslanamaz. Veriler tarihsel ve belirli domainlere aittir;
tahminler nedensel sonuç, adalet garantisi veya üretim performansı taahhüdü
değildir. Drift, eşik maliyetleri ve domain transferi ayrıca değerlendirilmelidir.

Ayrıntılı mimari için [PORTFOLIO.md](PORTFOLIO.md) dosyasına bakın.
