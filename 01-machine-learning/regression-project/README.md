# California Housing Regresyon Projesi

Türkiye Yapay Zeka Akademisi portföyü için hazırlanmış, medyan bölgesel ev
değerini tahmin eden çevrimdışı ve yeniden üretilebilir regresyon çalışmasıdır.

## Veri yönetişimi

| Alan | Değer |
| --- | --- |
| Veri seti | California Housing |
| Kaynak | scikit-learn / StatLib, 1990 U.S. Census |
| Lisans | Veri için ayrı lisans belirtilmemiştir; ayrıntı `DATA_SOURCE.md` |
| Dil | Uygulanamaz; tamamen sayısal |
| Boyut | 20.640 satır × 9 sütun |
| Hedef | `target`, medyan ev değeri (100.000 USD birimi) |

Veri yerel `data/california_housing.csv` dosyasındadır. Normal eğitim indirme
yapmaz. Kaynak, atıf, lisans notu ve Diabetes fallback politikası için
[DATA_SOURCE.md](DATA_SOURCE.md) dosyasına bakın.

## Yöntem

- EDA, eksik değer ve IQR aykırı değer raporu
- Hedef kullanılmadan `RoomsPerBedroom` ve `BedroomsPerOccupant`
- Pipeline içinde median imputation, StandardScaler, SelectKBest
- %60/%20/%20 train-validation-test, `random_state=42`
- Linear Regression, Ridge, Random Forest ve Gradient Boosting
- 5-fold KFold CV, validation karşılaştırması ve GridSearchCV
- Dokunulmamış testte MAE, MSE, RMSE ve R²
- Residual analizi, prediction-vs-actual ve özellik önemi

Aykırı kayıtlar otomatik silinmez. Tüm preprocessing/feature-selection adımları
eğitim katmanlarında fit edilir. Final model `models/regression_model.pkl` olarak
kaydedilir.

## Final test sonucu

| Model | MAE | MSE | RMSE | R² |
| --- | ---: | ---: | ---: | ---: |
| Random Forest | 0.3346 | 0.2623 | 0.5121 | 0.8087 |

Bu değerler `outputs/test_metrics.csv` dosyasındaki dokunulmamış test sonucu
üzerinden alınmıştır; gerçek para biriminde üretim performansı iddiası değildir.

## Çalıştırma

```bash
# Yalnızca yerel veri yoksa bir kez
python download_data.py

python train_model.py
streamlit run app.py
```

Streamlit; tek tahmin, CSV toplu tahmin/indirme ve performans raporlarını sunar.
Girdi CSV'si sekiz ham özellik sütununu içermelidir.

## Çıktılar

`outputs/` altında veri profili, aykırı değer, CV/validation/tuning/test raporları,
özellik önemleri, residual ve prediction-vs-actual görselleri ile final özet;
`models/` altında tam sklearn pipeline bulunur.

## Sınırlamalar

Veri 1990 Kaliforniya bağlamıdır; güncel piyasalara doğrudan genellenemez.
Mekânsal bağımlılık ve hedef tavanı değerlendirmeyi etkileyebilir. Tahminler
nedensel veya ekspertiz sonucu değildir.
