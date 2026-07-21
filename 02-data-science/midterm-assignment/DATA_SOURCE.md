# Veri Kaynağı

- Planlanan veri: **TEKNOFEST Trendyol 2026 Datathon**
- Kaggle kimliği: `thetrumpet/teknofest-trendyol-2026-datathonn`
- Kaynak: <https://www.kaggle.com/datasets/thetrumpet/teknofest-trendyol-2026-datathonn>
- İlk belirtilen dosya: `items.csv`
- Yerel dizin: `02-data-science/midterm-assignment/data/`
- Mevcut yerel durum: 7 tablo indirildi; toplam yaklaşık 976 MB
- SHA-256: dosya bazında `outputs/dataset_inventory.json` içinde kaydedildi

## Lisans ve yeniden dağıtım

Veri setinin lisansı/yarışma koşulları yerel olarak doğrulanamadı. Bu nedenle
redistribution izni varsayılmamış, tüm veri dosyaları `.gitignore` kapsamına
alınmıştır. Veri repository yazarına aitmiş gibi sunulmaz. Kullanıcı Kaggle
sayfasındaki güncel koşulları kabul etmek ve uygunluğu kontrol etmekle yükümlüdür.

## İndirme

Kaggle CLI ve kullanıcının kendi credentials dosyası hazırlandıktan sonra:

```bash
./.venv/bin/python 02-data-science/download_data.py
```

Normal notebook ve Streamlit başlangıcı bu komutu çalıştırmaz; ağ erişimi yoktur.
Akademinin özgün e-ticaret CSV'si farklıysa dosya yerel `data/` dizinine konabilir
veya `ACADEMY_ECOMMERCE_DATA` ortam değişkeniyle seçilebilir.

## Sınırlamalar

Gerçek şema incelendi: veri ürün kataloğu, arama sorgusu ve query–item
relevance alanları içeriyor. Ara ödevin müşteri/sipariş/teslimat alanları yoktur;
bu veri final proje kaynağı olarak uygundur.
