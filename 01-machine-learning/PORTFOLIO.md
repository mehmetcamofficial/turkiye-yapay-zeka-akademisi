# AI & Data Intelligence Platform Architecture

## Platform katmanları

1. `portfolio_app.py`: güvenli requested-page yönlendirmesi ve kompakt bölüm/sayfa navigasyonu.
2. `portfolio/pages/`: Overview, Data Analytics, Machine Learning, Model Operations ve dokümantasyon modülleri.
3. `project_registry.py` / `data_science_registry.py`: dosya ve kaydedilmiş raporlardan türetilen durumlar.
4. `loaders.py`: bounded veri yükleme ve lazy/cached model artifact erişimi.
5. `ui_components.py`: KPI, durum, hata ve Arrow dışı güvenli tablo sunumu.
6. `02-data-science/trendyol-profile/`: explicit CLI ile envanter, kalite, şema ve sampled profiling.

Model performansları yalnızca kaydedilmiş test artifact'larından okunur. Planlanan Trendyol final projesi tamamlanmış yetenek veya gerçek model performansı olarak gösterilmez.

## Mimari

```text
01-machine-learning/
├── portfolio_app.py
├── portfolio/
│   ├── config.py
│   ├── loaders.py
│   ├── project_registry.py
│   ├── styles.py
│   ├── ui_components.py
│   └── pages/
│       ├── overview.py
│       ├── churn.py
│       ├── regression.py
│       ├── nlp.py
│       ├── clustering.py
│       ├── deployment.py
│       ├── performance.py
│       ├── assignments.py
│       └── about.py
├── customer-churn-prediction/
├── regression-project/
└── nlp-project/

02-data-science/
├── midterm-assignment/
└── final-project/
```

Ana uygulama `portfolio_app.py` üzerinden çalışır. Churn adapter'ı mevcut sayfa
fonksiyonlarını dinamik olarak kullanır; eski uygulamanın tamamı kopyalanmaz ve
standalone çalışma davranışı korunur. Regresyon ve NLP modülleri kendi kaydedilmiş
pipeline ve output dosyalarını kullanır.

## Sayfalar

- Genel Bakış: artifact-driven özet ve proje kartları
- Customer Churn: özet, tekli/toplu tahmin, performans, metodoloji
- Regresyon: özet, tekli/toplu tahmin, performans, residual, veri kaynağı
- NLP Analizi: özet, tekli/toplu analiz, performans, terimler, hatalar, kaynak
- Kümeleme ve Deployment: gerçek dosya durumuna bağlı hazırlık ekranları
- Model Performansı: uyumsuz metrikleri ayrı problem bölümlerinde gösterir
- Akademi Ödevleri: kartlar ve erişilebilir durum tablosu
- Proje Hakkında: metodoloji, artifact ve yeniden üretilebilirlik
- Veri Bilimi Genel Bakış: dataset, notebook, şema ve yayın hazırlığı
- Ara Ödev: 15 soru, kalite raporları, Colab/teslim bilgisi
- Final Projesi: resmî brief'e kadar planlanan şema-duyarlı proje

## Merkezi registry

Her kayıt kimlik, ad, kategori, açıklama, dizin, hesaplanan durum, veri seti,
final model, ana/ikincil metrikler, model yolu, zorunlu output'lar, uygulama/eğitim
ve veri kaynağı varlığı, doğrulama zamanı ve sınırlamaları içerir. Tamamlanma
durumları model, test metriği ve zorunlu görsel/rapor dosyaları bulunmadan oluşmaz.

## Gerçek metrikler

| Bağlam | Final model | Test sonuçları |
| --- | --- | --- |
| Churn sınıflandırma | Logistic Regression | ROC AUC 0.8440; Accuracy 0.7942; Recall 0.5695; F1 0.5950 |
| Housing regresyon | Random Forest | RMSE 0.5121; MAE 0.3346; R² 0.8087 |
| Sentiment NLP | MultinomialNB | Accuracy 0.8191; Precision 0.8105; Recall 0.8322; F1 0.8212 |

Uygulama bu değerleri CSV artifact'larından yükler; burada yalnızca doğrulanmış
çalıştırmanın dokümantasyon özeti bulunur.

## Yeniden üretilebilirlik

- Python 3.12 ve pinlenmiş temel paket sürümleri
- `random_state=42`
- Leakage-safe preprocessing/CV
- Dokunulmamış final test kümeleri
- Regresyon ve NLP için yerel CSV ve `DATA_SOURCE.md`
- Normal training sırasında remote API zorunluluğu yok
- Eksik artifact'larda güvenli loader ve boş durum mesajı

## Çalıştırma

```bash
./.venv/bin/python -m streamlit run 01-machine-learning/portfolio_app.py
```

Bu komut depo kökündeki sanal ortamı bilinçli olarak seçer; global veya Anaconda
Streamlit çalıştırıcısı kullanılmamalıdır.

## Sınırlamalar

Metrikler problem türleri arasında eşdeğer değildir. Tarihsel/domain-spesifik
veriler, sınıf dengesizliği, hedef tavanı, kısa metin seçimi ve concept drift
genellemeyi sınırlar. Açıklanabilirlik çıktıları ilişkiyi gösterir, nedenselliği
değil.

## Portfolyo ekran görüntüleri

> Placeholder: Genel Bakış, tahmin modülleri ve cross-project performans
> ekran görüntüleri final yayın öncesinde buraya eklenecektir.
