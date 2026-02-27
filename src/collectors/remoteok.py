"""
Coletor Remote OK (Épico 7.2). API pública, sem auth.
Filtro client-side: apenas título (position) com keywords específicas ligadas a PM/TPM.
Filtro de recência: últimas 7 dias. Atribuição obrigatória nos logs (Source: Remote OK).
"""

import json
from datetime import datetime, timezone, timedelta
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

from . import TITLE_KEYWORDS

REMOTEOK_API_URL = "https://remoteok.com/api"
REMOTEOK_RECENT_HOURS = 168
REMOTEOK_USER_AGENT = "JobRadar/1.0 (https://github.com/job-radar; Source: Remote OK)"
LOG_PREFIX = "[fetch]"

# Alias mantido para compatibilidade com diagnose_collectors e outros imports legados.
POSITION_KEYWORDS = TITLE_KEYWORDS


def _parse_remoteok_date(date_str: str) -> datetime | None:
    """Interpreta date (ex: 2026-02-26T12:00:06+00:00) como datetime com tz."""
    if not date_str:
        return None
    try:
        s = str(date_str).strip()
        if s.endswith("Z"):
            return datetime.fromisoformat(s.replace("Z", "+00:00"))
        if "+" in s or (len(s) > 10 and s[10:11] == "+"):
            return datetime.fromisoformat(s)
        return datetime.fromisoformat(s).replace(tzinfo=timezone.utc)
    except (ValueError, TypeError):
        return None


def _matches_filter(job: dict) -> bool:
    """True se o título/cargo contém alguma das POSITION_KEYWORDS."""
    position = (job.get("position") or "").lower()
    return any(kw in position for kw in POSITION_KEYWORDS)


def _format_salary(job: dict) -> str | None:
    """Monta string de salário a partir de salary_min, salary_max (e currency se existir)."""
    min_s = job.get("salary_min")
    max_s = job.get("salary_max")
    currency = (job.get("salary_currency") or "").strip()
    if min_s is None and max_s is None:
        return None
    parts = []
    if min_s is not None or max_s is not None:
        if min_s is not None and max_s is not None and min_s != max_s:
            parts.append(f"{min_s}-{max_s}")
        else:
            parts.append(str(max_s if min_s is None else min_s))
    if currency:
        parts.append(currency)
    return " ".join(parts) if parts else None


def collect_remoteok() -> list[dict]:
    """
    Coletor: API Remote OK. Retorna lista de jobs brutos (últimas 7 dias).
    Filtro: tags product/management/exec ou position com PM/TPM.
    Requisito legal: logs mencionam "Source: Remote OK".
    """
    now_local = datetime.now().astimezone()
    cutoff = now_local - timedelta(hours=REMOTEOK_RECENT_HOURS)
    all_raw: list[dict] = []

    print(f"{LOG_PREFIX} 📡 Coletor remoteok (Source: Remote OK)...")

    try:
        req = Request(REMOTEOK_API_URL, headers={"User-Agent": REMOTEOK_USER_AGENT})
        with urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except (URLError, HTTPError, json.JSONDecodeError, OSError) as e:
        print(f"{LOG_PREFIX} ✗ Erro Remote OK: {e}")
        return []

    if not isinstance(data, list) or len(data) < 2:
        print(f"{LOG_PREFIX}   remoteok: 0 vagas (resposta inválida ou vazia).")
        return []

    # Primeiro item é metadata (ignorar)
    jobs = data[1:]
    added = 0
    for j in jobs:
        if not isinstance(j, dict):
            continue
        position = j.get("position") or ""
        if not _matches_filter(j):
            continue
        date_val = j.get("date")
        pub_dt = _parse_remoteok_date(date_val)
        if pub_dt is None:
            continue
        pub_local = pub_dt.astimezone()
        if pub_local < cutoff:
            continue
        url_val = j.get("url") or j.get("apply_url")
        if not url_val and j.get("slug"):
            url_val = f"https://remoteok.com/l/{j.get('id', j.get('slug', ''))}"
        all_raw.append({
            "title": position,
            "company": j.get("company"),
            "location": j.get("location") or "",
            "salary": _format_salary(j),
            "url": url_val or "",
            "description": j.get("description"),
            "date": date_val,
        })
        added += 1

    print(f"{LOG_PREFIX}   remoteok: {added} vagas (últimas {REMOTEOK_RECENT_HOURS}h, Source: Remote OK).")
    return all_raw
