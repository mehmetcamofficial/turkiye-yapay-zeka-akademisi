# Deployment Planı

1. Tek bir preprocessing + estimator pipeline artifact'ı kaydet.
2. Model, veri sözlüğü, feature contract, sürüm ve checksum metadata'sını birlikte yayınla.
3. Batch CSV scoring ve tek query-product scoring için aynı servis fonksiyonunu kullan.
4. Streamlit formunda şema doğrulama, bounded preview ve güvenli hata mesajları uygula.
5. API aşamasında `/health`, `/metadata` ve `/predict` contract'larını test et.
6. Latency, hata oranı, input drift ve skor dağılımını izle.
7. Rollback için önceki doğrulanmış artifact'ı koru.

Deployment henüz uygulanmadı; endpoint veya canlı performans iddiası yoktur.
