"""
Pipeline de coleta: executa coletores, normaliza, deduplica e filtra por recência.
"""

import json
from datetime import date, datetime
from pathlib import Path
from typing import Any

import yaml

from src.job_schema import normalize_job

LOG_PREFIX = "[fetch]"


def load_config() -> dict:
    """Carrega config/search.yaml."""
    config_path = Path("config/search.yaml")
    if not config_path.exists():
        raise FileNotFoundError("Configuração config/search.yaml não encontrada.")
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def run_pipeline(collectors_config: list[tuple[str, Any]]) -> list[dict]:
    """
    Executa todos os coletores, normaliza para o schema único e deduplica por id_hash.
    Retorna lista de jobs normalizados (sem filtro de 7 dias; isso é feito em remove_duplicates).
    """
    all_normalized: list[dict] = []
    seen_hashes: set[str] = set()

    for source_name, collector_fn in collectors_config:
        raw_list = collector_fn()
        for raw in raw_list:
            job = normalize_job(raw, source_name)
            if job["id_hash"] in seen_hashes:
                continue
            seen_hashes.add(job["id_hash"])
            all_normalized.append(job)

    return all_normalized


def remove_duplicates(new_jobs: list[dict], raw_dir: Path) -> list[dict]:
    """
    Remove vagas cujo id_hash já existe nos arquivos dos últimos 7 dias.
    """
    recent_hashes: set[str] = set()
    today = date.today()

    try:
        for f in raw_dir.glob("*.json"):
            try:
                file_date_str = f.name.split("_")[0]
                file_date = datetime.strptime(file_date_str, "%Y-%m-%d").date()
                days_diff = (today - file_date).days
                if 0 <= days_diff <= 7:
                    with open(f, "r", encoding="utf-8") as file:
                        data = json.load(file)
                        for job in data.get("jobs", []):
                            h = job.get("id_hash") or job.get("id")
                            if h:
                                recent_hashes.add(h)
            except (ValueError, IndexError, KeyError):
                continue
    except Exception as e:
        print(f"{LOG_PREFIX} ! Aviso ao ler duplicatas: {e}")

    filtered = []
    removed = 0
    for job in new_jobs:
        h = job.get("id_hash")
        if h and h in recent_hashes:
            removed += 1
            continue
        filtered.append(job)
        if h:
            recent_hashes.add(h)

    if removed > 0:
        print(f"{LOG_PREFIX} 🧹 Removidas {removed} vagas duplicatas (id_hash nos últimos 7 dias).")

    return filtered


def filter_old_jobs(jobs: list[dict]) -> list[dict]:
    """Descarta vagas com mais de 14 dias com base no campo 'date'."""
    critical_patterns = ["3 weeks", "4 weeks", "month", "months", "2 weeks ago"]
    filtered = []
    discarded = 0
    for job in jobs:
        date_str = (job.get("date") or "").lower()
        if any(p in date_str for p in critical_patterns):
            discarded += 1
        else:
            filtered.append(job)
    if discarded > 0:
        print(f"{LOG_PREFIX} ⏳ Descartadas {discarded} vagas antigas (> 14 dias).")
    return filtered


# --- 2.5 Quality Guard (pré-scoring) ---
MIN_JD_LENGTH = 500
GENERIC_TITLES = frozenset(
    s.strip().lower()
    for s in (
        "opportunity",
        "job opening",
        "job",
        "position",
        "remote",
        "new job",
        "open position",
    )
)


def _quality_guard_reason(job: dict) -> str | None:
    """
    Retorna o motivo de descarte ou None se o job passar no quality guard.
    """
    jd = (job.get("jd_full") or "").strip()
    if len(jd) < MIN_JD_LENGTH:
        return "jd_too_short"

    title = (job.get("title") or "").strip()
    if not title:
        return "title_empty"
    if title.lower() in GENERIC_TITLES:
        return "title_generic"

    company = (job.get("company") or "").strip()
    if not company:
        return "company_empty"

    return None


def apply_quality_guard(jobs: list[dict]) -> tuple[list[dict], list[dict]]:
    """
    Pré-scoring: descarta jobs com JD < 500 chars, título vazio/genérico ou empresa vazia.
    Retorna (jobs_que_passaram, lista_de_descartados).
    Cada item em descartados é o job com campo extra "discard_reason" para o log.
    """
    kept: list[dict] = []
    discarded: list[dict] = []

    for job in jobs:
        reason = _quality_guard_reason(job)
        if reason is None:
            kept.append(job)
        else:
            discarded.append({**job, "discard_reason": reason})

    return kept, discarded
