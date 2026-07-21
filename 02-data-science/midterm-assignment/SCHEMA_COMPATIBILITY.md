# Şema Uyumluluk Raporu

Kontrol tarihi: 21 Temmuz 2026
Kaynak: TEKNOFEST Trendyol 2026 Datathon yerel dosyaları

## Gerçek tablolar

| Dosya | Satır | Sütun | Amaç |
| --- | ---: | ---: | --- |
| `items.csv` | 962.873 | 7 | Ürün kataloğu |
| `parsed_items_for_sky.parquet` | 962.873 | 12 | Parse edilmiş ürün kataloğu |
| `terms.csv` | 50.153 | 2 | Arama sorguları |
| `training_pairs.csv` | 250.000 | 4 | Query–item eğitim eşleri |
| `train_with_negatives.parquet` | 1.000.000 | 12 | Pozitif/negatif relevance eğitim tablosu |
| `submission_pairs.csv` | 3.359.679 | 3 | Test query–item eşleri |
| `sample_submission.csv` | 3.359.679 | 2 | Submission şablonu |

## Zorunlu alan uyumu

| Kaynak dosya | Zorunlu alan | Gerçek alan | Eşleşme | Dönüşüm | Güven |
| --- | --- | --- | --- | --- | --- |
| — | `indirim_orani` | — | Missing | Akademi transactional verisi gerekli | Yüksek |
| — | `musteri_puani` | — | Missing | Akademi transactional verisi gerekli | Yüksek |
| — | `odeme_turu` | — | Missing | Akademi transactional verisi gerekli | Yüksek |
| — | `musteri_tipi` | — | Missing | Akademi transactional verisi gerekli | Yüksek |
| — | `siparis_tarihi` | — | Missing | Akademi transactional verisi gerekli | Yüksek |
| — | `sehir` | — | Missing | Akademi transactional verisi gerekli | Yüksek |
| `items.csv` | `kategori` | `category` | Safe Semantic Match | Sütun adı Türkçeleştirilebilir; ürün kategorisi anlamı eşdeğer | Yüksek |
| — | `birim_fiyat` | — | Missing | Akademi transactional verisi gerekli | Yüksek |
| — | `toplam_tutar` | — | Missing | Akademi transactional verisi gerekli | Yüksek |
| — | `teslimat_gunu` | — | Missing | Akademi transactional verisi gerekli | Yüksek |

## Soru desteği

Mevcut Trendyol tablolarıyla dürüstçe desteklenen genel sorular:

- 1: İlk/son satırlar
- 2: Boyut ve sütunlar
- 3: `info()`, `describe()` ve tip listeleri
- 4: Eksik değer özeti
- 5: Eksik içeren satırlar
- 9: Duplicate analizi
- 11: `category` üzerinden kategori yazım analizi

Blocked sorular: **6, 7, 8, 10, 12, 13, 14, 15**. Soru 15'in yalnızca kategori
alt bölümü desteklenebilir; müşteri tipi, ödeme türü, puan ve toplam tutar
alt soruları bulunmadığı için bütün soru tamamlanmış sayılamaz.

## Sonuç

Durum: **Şema Uyumsuz**.

Bu veri ürün kataloğu ve search relevance final projesi için uygundur, fakat ara
ödevin müşteri/sipariş/ödeme/teslimat şemasına uygun değildir. İlgisiz ürün
alanları müşteri veya transaction alanlarına dönüştürülmeyecek; ara ödev akademinin
özgün transactional CSV'sini bekleyecektir.
