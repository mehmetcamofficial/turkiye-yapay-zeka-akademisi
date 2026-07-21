# UCI İngilizce Duygu Analizi

Türkiye Yapay Zeka Akademisi portföyü için hazırlanmış çevrimdışı ikili metin
sınıflandırma projesidir.

## Veri yönetişimi

| Alan | Değer |
| --- | --- |
| Veri seti | UCI Sentiment Labelled Sentences |
| Kaynak | UCI ML Repository, DOI 10.24432/C57604 |
| Lisans | CC BY 4.0 |
| Dil | İngilizce |
| Yerel boyut | 3.000 satır × 3 sütun |
| Hedef | `label`: 0 negatif, 1 pozitif |
| Alanlar | Amazon, IMDb, Yelp |

Yerel kopya `data/sentiment_dataset.csv` altındadır. Kaynak/atıf ve yeniden
üretilebilirlik ayrıntıları [DATA_SOURCE.md](DATA_SOURCE.md) dosyasındadır.
Normal eğitim internet veya API kullanmaz; CSV yoksa açık hata verir. Sentetik
metin fallback'i yoktur.

## Yöntem

- Deterministik HTML/URL, lowercase ve whitespace temizliği
- Stratified %60/%20/%20 train-validation-test
- Pipeline içinde TF-IDF; leakage önleme
- Logistic Regression, LinearSVC ve MultinomialNB
- 5-fold StratifiedKFold, validation karşılaştırması ve GridSearchCV
- Testte Accuracy, Precision, Recall, F1, confusion matrix
- Pozitif/negatif terimler ve false-positive/false-negative hata analizi
- Tam pipeline: `models/nlp_pipeline.pkl`

Eğitim öncesi 18 birebir yinelenen kayıt kaldırılmış ve modelleme 2.982 benzersiz
etiketli kayıt üzerinde yapılmıştır. Yerel kaynak CSV değiştirilmeden 3.000 kaydı
korur.

## Final test sonucu

| Model | Accuracy | Precision | Recall | F1 |
| --- | ---: | ---: | ---: | ---: |
| MultinomialNB | 0.8191 | 0.8105 | 0.8322 | 0.8212 |

Değerler `outputs/test_metrics.csv` dosyasındaki dokunulmamış test bölümünden
okunmuştur; farklı domainlerde üretim performansı iddiası değildir.

## Çalıştırma

```bash
# Yalnızca yerel veri yoksa bir kez
python download_data.py

python train_model.py
streamlit run app.py
```

Streamlit tek metin tahmini, desteklenen güven skoru, `text` sütunlu CSV ile
toplu tahmin/indirme ve performans raporlarını gösterir.

## Sınırlamalar

Veri kısa, belirgin olumlu/olumsuz İngilizce cümleleri kapsar; nötr sınıf yoktur.
İroni, uzun bağlam, güncel dil ve farklı domainlere transfer sınırlıdır. Güven
skoru her model için kalibre olasılık değildir; metrikler üretim garantisi veya
nedensel kanıt değildir.
