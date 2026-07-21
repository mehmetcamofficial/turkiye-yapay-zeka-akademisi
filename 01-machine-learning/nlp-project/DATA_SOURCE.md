# Veri Kaynağı ve Yeniden Üretilebilirlik

## Kullanılan veri

- Ad: UCI Sentiment Labelled Sentences
- DOI: <https://doi.org/10.24432/C57604>
- Resmî sayfa: <https://archive.ics.uci.edu/dataset/331/sentiment+labelled+sentences>
- Lisans: Creative Commons Attribution 4.0 International (CC BY 4.0)
- Dil: İngilizce
- Kaynak alanlar: Amazon ürün, IMDb film ve Yelp restoran değerlendirmeleri
- Yerel kopya: `data/sentiment_dataset.csv`
- Yerel boyut: 3.000 satır, 3 sütun (`text`, `label`, `source`)
- Hedef: `0` negatif, `1` pozitif; nötr sınıf yoktur
- SHA-256: `77b6009330f9ea5cb435db3316a8317c9ae8c93ec9a6a73e2af28a7905b54588`
- Atıf: Kotzias et al. (2015), *From Group to Individual Labels Using Deep Features*

## Tek seferlik kurulum

```bash
python download_data.py
```

Kurulum scripti resmî UCI ZIP arşivini bir kez indirir. Metinleri sağdaki son
sekmeden ayırarak iç noktalama ve tırnakları korur. Mevcut CSV'nin üzerine
yazmaz. `train_model.py` ve `app.py` yalnızca yerel CSV/model dosyasını kullanır;
normal eğitim ve tahmin sırasında API veya internet gerekmez. İndirme başarısız
olursa sentetik metin üretilmez ve komut açık hata ile durur.

## Sınırlamalar

Örnekler kısa ve yalnızca belirgin olumlu/olumsuz İngilizce cümlelerden oluşur.
Nötr duygu, uzun bağlam, ironi ve güncel dil kapsamı sınırlıdır. Üç platformun
seçim süreci domain yanlılığı yaratabilir. Eğitim metrikleri gerçek dünya üretim
performansı veya nedensel sonuç olarak yorumlanmamalıdır.
