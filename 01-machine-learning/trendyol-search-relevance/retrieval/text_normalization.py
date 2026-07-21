"""Turkish-aware retrieval normalization that preserves commercial identifiers."""
from __future__ import annotations
import html,re,unicodedata

_TRANSLATION=str.maketrans({"I":"ı","İ":"i"})
_UNITS=re.compile(r"(?<=\d)\s*(ml|lt|l|kg|gr|g|cm|mm|gb|tb|w|mah)\b",re.I)

def normalize_retrieval_text(value:object)->str:
    if value is None:return ""
    text=html.unescape(str(value)); text=unicodedata.normalize("NFKC",text).translate(_TRANSLATION).lower()
    text=re.sub(r"<[^>]+>"," ",text); text=text.replace("’","'").replace("–","-").replace("—","-")
    text=re.sub(r"(?<=\w)'(?=\w)"," ",text); text=re.sub(r"(?<=\w)-(?=\w)","-",text)
    text=re.sub(r"[^\w\s\-+]"," ",text,flags=re.UNICODE); text=_UNITS.sub(lambda m:m.group(1).lower(),text)
    text=re.sub(r"(.)\1{3,}",r"\1\1",text); return re.sub(r"\s+"," ",text).strip()

def build_searchable_text(row,variant="enriched_product_text",attribute_limit=240,field_weights=None)->str:
    title=normalize_retrieval_text(row.get("title",""))
    if variant=="title_only":return title
    names=("title","category","brand","gender","age_group","attributes")
    fields={"title":title,"category":normalize_retrieval_text(row.get("category","")),"brand":normalize_retrieval_text(row.get("brand","")),"gender":normalize_retrieval_text(row.get("gender","")),"age_group":normalize_retrieval_text(row.get("age_group","")),"attributes":normalize_retrieval_text(row.get("attributes",""))[:attribute_limit]}
    weights={name:1 for name in names}; weights.update(field_weights or {})
    return " ".join(value for name in names for value in [fields[name]]*max(0,int(weights[name])) if value)
