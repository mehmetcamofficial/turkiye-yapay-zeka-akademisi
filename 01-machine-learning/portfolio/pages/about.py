"""Portfolio methodology and reproducibility page."""

from portfolio.project_registry import get_project_registry
from portfolio.ui_components import artifact_checklist, hero_panel, information_panel, section_heading


def render() -> None:
    hero_panel("Proje Hakkında", "Portfolyo mimarisi, yeniden üretilebilirlik ilkeleri ve dürüst model raporlama yaklaşımı.", "METHODOLOGY")
    information_panel("Artifact-driven mimari", "Durum ve metrikler UI içinde yazılı değil; model, CSV, JSON ve rapor dosyalarından okunur.")
    information_panel("Yeniden üretilebilirlik", "Eğitim preprocessing adımları pipeline içindedir. Regresyon ve NLP normal eğitimde yerel CSV kullanır; random_state=42 uygulanır.")
    information_panel("Veri bilimi yönetişimi", "Ara ödev yerel veri ve zorunlu şema olmadan tamamlanmış sayılmaz. Kaggle verisi lisans koşulları doğrulanmadan repoya eklenmez; final proje resmî brief'e kadar Planlandı kalır.")
    information_panel("Sorumlu yorum", "Metrikler dokunulmamış test setlerine aittir; nedensellik, adalet veya farklı domainlerde üretim performansı garantisi değildir.")
    section_heading("Artifact denetimi")
    for project in get_project_registry()[:3]:
        section_heading(project["name"])
        artifact_checklist(project)
