"""
Schema único de vagas e normalização (Épico 2.1).

Usado pelo pipeline de fetch e, se necessário, por score/outros módulos.
"""

import hashlib
from datetime import datetime

JOB_SCHEMA_KEYS = (
    "id_hash",
    "source",
    "title",
    "company",
    "location",
    "salary",
    "jd_full",
    "url",
    "collected_at",
    "date",
)


def make_id_hash(company: str, title: str) -> str:
    """id_hash baseado em company + title (case insensitive) para dedupe cross-fonte."""
    key = f"{str(company or '').strip().lower()}|{str(title or '').strip().lower()}"
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


def normalize_job(raw: dict, source: str) -> dict:
    """
    Converte um job bruto de qualquer coletor para o schema mínimo.
    Garante todos os campos do schema; preenche com string vazia ou null quando ausente.
    """
    company = str(raw.get("company") or "").strip()
    title = str(raw.get("title") or "").strip()
    id_hash = make_id_hash(company, title)

    jd_full = (
        str(raw.get("jd_full") or raw.get("description") or raw.get("requirements") or "")
    ).strip()

    collected_at = datetime.now().astimezone().isoformat()

    return {
        "id_hash": id_hash,
        "id": id_hash,  # compatibilidade com score.py
        "source": source,
        "title": title,
        "company": company,
        "location": str(raw.get("location") or "").strip(),
        "salary": raw.get("salary"),
        "jd_full": jd_full,
        "url": str(raw.get("url") or "").strip(),
        "collected_at": collected_at,
        "date": str(raw.get("date") or "").strip(),
    }
