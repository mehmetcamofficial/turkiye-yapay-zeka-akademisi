# Trendyol Data Profile

TEKNOFEST Trendyol veri tablolarını sütun adı varsaymadan, memory-bounded ve
sample kapsamını açıkça belirterek profiller.

```bash
./.venv/bin/python 02-data-science/trendyol-profile/run_profile.py
```

Envanter SHA-256 ve full row count bilgilerini bir kez kaydeder. Profil kalite,
kardinalite, numerik, kategorik ve metin uzunluğu metriklerini tablo başına
deterministik ilk 20.000 satır üzerinden üretir ve `metric_scope` ile sampled
olduğunu belirtir. Uygulama başlangıcı bu pipeline'ı çalıştırmaz.
