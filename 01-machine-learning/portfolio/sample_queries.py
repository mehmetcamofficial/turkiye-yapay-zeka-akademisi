from __future__ import annotations

from typing import Any

SAMPLE_QUERIES: list[dict[str, Any]] = [
    {"label": "kablosuz kulaklık", "query": "kablosuz kulaklık", "title": "Bluetooth Kablosuz Kulaklık", "category": "Kulaklık", "brand": "Sony"},
    {"label": "bluetooth kulaklık", "query": "bluetooth kulaklık", "title": "Bluetooth Kablosuz Stereo Kulaklık", "category": "Kulaklık", "brand": "JBL"},
    {"label": "kadın spor ayakkabı", "query": "kadın spor ayakkabı", "title": "Kadın Koşu Ayakkabısı", "category": "Spor Ayakkabı", "brand": "Nike", "gender": "Kadın"},
    {"label": "erkek siyah tişört", "query": "erkek siyah tişört", "title": "Erkek Siyah Basic Tişört", "category": "Tişört", "brand": "Mavi", "gender": "Erkek"},
    {"label": "çocuk yağmurluk", "query": "çocuk yağmurluk", "title": "Çocuk Su Geçirmez Yağmurluk", "category": "Dış Giyim", "brand": "Lumberjack", "gender": "Unisex", "age_group": "Çocuk"},
    {"label": "robot süpürge", "query": "robot süpürge", "title": "Akıllı Robot Süpürge", "category": "Süpürge", "brand": "Xiaomi"},
    {"label": "kahve makinesi", "query": "kahve makinesi", "title": "Türk Kahvesi Makinesi", "category": "Kahve Makinesi", "brand": "Arçelik"},
    {"label": "oyun laptopu", "query": "oyun laptopu", "title": "Oyun Bilgisayarı", "category": "Laptop", "brand": "ASUS"},
    {"label": "telefon kılıfı", "query": "telefon kılıfı", "title": "Silikon Telefon Kılıfı", "category": "Telefon Aksesuarı", "brand": "Samsung"},
    {"label": "bebek bezi", "query": "bebek bezi", "title": "Bebek Bezi Mega Paket", "category": "Bebek Bezi", "brand": "Prima", "age_group": "Bebek"},
    {"label": "güneş kremi", "query": "güneş kremi", "title": "Güneş Koruyucu Krem SPF 50", "category": "Cilt Bakım", "brand": "Nivea"},
    {"label": "çalışma masası", "query": "çalışma masası", "title": "Ayarlanabilir Çalışma Masası", "category": "Mobilya", "brand": "İkea"},
    {"label": "koşu ayakkabısı", "query": "koşu ayakkabısı", "title": "Erkek Koşu Ayakkabısı", "category": "Spor Ayakkabı", "brand": "Adidas", "gender": "Erkek"},
    {"label": "akıllı saat", "query": "akıllı saat", "title": "Akıllı Saat", "category": "Saat", "brand": "Apple"},
    {"label": "saç kurutma makinesi", "query": "saç kurutma makinesi", "title": "Saç Kurutma Makinesi", "category": "Kişisel Bakım", "brand": "Philips"},
]


def get_sample_queries() -> list[dict[str, Any]]:
    return SAMPLE_QUERIES


def get_sample_labels() -> list[str]:
    return ["Custom / Özel"] + [q["label"] for q in SAMPLE_QUERIES]


def get_sample_by_label(label: str) -> dict[str, Any] | None:
    if label == "Custom / Özel":
        return None
    for q in SAMPLE_QUERIES:
        if q["label"] == label:
            return q
    return None
