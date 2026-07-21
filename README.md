# turkiye-yapay-zeka-akademisi
Türkiye Yapay Zeka Akademisi kapsamında geliştirilen makine öğrenmesi ve yapay zekâ projeleri.

## Trendyol Search Relevance Intelligence

Public Datathon verisindeki sorgu–ürün çiftleri için ikili alaka sınıflandırması yapan bağımsız makine öğrenmesi projesidir.

- Veri modu: deterministik `sample`, 100.000 satır
- Validation: `term_id` bazlı GroupShuffleSplit; sorgu overlap `0`
- Seçilen model: word/character TF-IDF + açık benzerlik özellikleri + Logistic Regression
- Validation: F1 `0.626047`, precision `0.7406`, recall `0.5422`, PR AUC `0.716490`
- Demo: AI & Data Intelligence Platform içinde tekli, batch ve 5.000 ürünlük bounded playground

Sonuçlar production arama kalitesi kanıtı değildir. Model public yarışma verisinin sınırlı örneğinde çalışan lexical bir baseline’dır; semantik eşanlamlılar, intent belirsizliği, nadir kategoriler ve katalog drift’i önemli sınırlamalardır.
