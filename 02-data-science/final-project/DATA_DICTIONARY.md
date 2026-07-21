# Veri Sözlüğü

| Alan | Kaynak | Anlam |
|---|---|---|
| `id` | pair tabloları | Query-product çift kaydı |
| `term_id` | terms/pairs | Sorgu anahtarı |
| `query` | terms/training | Kullanıcı arama metni |
| `item_id` | items/pairs | Ürün anahtarı |
| `title` | items/training | Ürün başlığı |
| `category` | items/training | Ürün katalog kategorisi |
| `brand` | items/training | Ürün markası |
| `attributes` | items/training | Yarı-yapısal ürün özellikleri |
| `label` | training | Query-product relevance hedefi |
| `sample_weight` | train_with_negatives | Eğitim örneği ağırlığı |

`gender`, `age_group` ve parse edilmiş renk/materyal/beden alanları ürün bağlamındadır; müşteri demografisi olarak yorumlanmaz. Ödeme, sipariş, fiyat ve teslimat alanları yoktur.
