# Trendyol Veri Kalitesi ve Keşifsel Veri Analizi

Gerçek Trendyol ürün kataloğu, sorgu ve query-product relevance tabloları üzerinde tekrar üretilebilir ara proje.

## Durum

**Geliştiriliyor.** Yedi kaynak tablo ve yaklaşık 0,91 GiB veri yerelde hazırdır. Envanter tam dosya metadata'sını; dağılım ve kalite raporları ise tablo başına deterministic ilk 20.000 satırı kullanır.

Kapsam veri envanteri, gerçek şema, eksik/duplicate değerler, kategori/marka, title/query/attributes metin kalitesi ve label dağılımına uyarlanmıştır. Ödeme, müşteri, sipariş, fiyat veya teslimat analizi yapıldığı iddia edilmez. Özgün ödevle farklar `SCHEMA_COMPATIBILITY.md` içinde korunur.
