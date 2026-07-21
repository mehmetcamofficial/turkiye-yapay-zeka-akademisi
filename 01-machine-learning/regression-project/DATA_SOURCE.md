# Veri Kaynağı ve Yeniden Üretilebilirlik

## Kullanılan veri

- Ad: California Housing
- Yerel kopya: `data/california_housing.csv`
- Boyut: 20.640 satır, 9 sütun (8 girdi + `target`)
- Orijinal bağlam: 1990 ABD nüfus sayımından Kaliforniya census block group kayıtları
- Hedef: Bölgesel medyan ev değeri; birim 100.000 USD
- SHA-256: `d77e47abf8adbf425f82dd80ebc02dc6a30dc6e9525fa1ee9076789647cba2bf`
- Sağlayıcı: StatLib; scikit-learn `fetch_california_housing`
- Kaynak: <https://scikit-learn.org/1.5/datasets/real_world.html#california-housing-dataset>
- Referans: Pace, R. K. & Barry, R. (1997), *Sparse Spatial Autoregressions*

## Lisans notu

Scikit-learn yazılımı BSD-3-Clause lisanslıdır; ancak scikit-learn veri seti
sayfası California Housing verisi için ayrı bir veri lisansı belirtmez. Bu
nedenle veri lisansı BSD olarak yanlış sunulmamıştır. Veri eğitim/araştırma
bağlamında, kaynak ve akademik çalışma atfı korunarak kullanılır. Yeniden
dağıtım yapılacak ortamın kendi lisans/uygunluk incelemesini yapması gerekir.

## Tek seferlik kurulum

```bash
python download_data.py
```

Script önce California Housing'u indirir ve metadata kaydeder. İndirme mümkün
değilse scikit-learn ile birlikte gelen Diabetes veri setine açıkça işaretlenmiş
fallback uygular. Bu depodaki mevcut metadata `fallback_used: false` değerine
sahiptir. `train_model.py` ağ erişimi yapmaz; yerel CSV yoksa açık hata verir.

## Bütünlük ve sınırlamalar

Yerel CSV 20.640 satır ve 9 sütun içerir. Veri 1990 Kaliforniya bağlamına,
mekânsal bağımlılığa ve üstten sınırlandırılmış hedef değerlere sahiptir;
güncel piyasa fiyatı veya ekspertiz değeri değildir.
