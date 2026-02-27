"""
Coletor Remotive (Épico 2.2). API pública, categorias product e project-management.
Filtro de recência: últimas 7 dias (publication_date).
"""

import json
from datetime import datetime, timezone, timedelta
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

REMOTIVE_CATEGORIES = ["product", "project-management"]
REMOTIVE_RECENT_HOURS = 168
REMOTIVE_LIMIT = 100
REMOTIVE_BASE_URL = "https://remotive.com/api/remote-jobs"
LOG_PREFIX = "[fetch]"


def _parse_remotive_date(publication_date: str) -> datetime | None:
    """Interpreta publication_date (ex: 2026-02-16T10:16:38) como UTC."""
    if not publication_date:
        return None
    try:
        s = str(publication_date).strip()
        if s.endswith("Z"):
            return datetime.fromisoformat(s.replace("Z", "+00:00"))
        if "+" in s or (len(s) > 10 and s[10] == "+"):
            return datetime.fromisoformat(s)
        return datetime.fromisoformat(s).replace(tzinfo=timezone.utc)
    except (ValueError, TypeError):
        return None


def collect_remotive() -> list[dict]:
    """
    Coletor: API Remotive (product + project-management).
    Retorna lista de jobs brutos para normalização (últimas 7 dias).
    """
    # Cutoff em horário local (últimas N horas no fuso do usuário)
    now_local = datetime.now().astimezone()
    cutoff = now_local - timedelta(hours=REMOTIVE_RECENT_HOURS)
    all_raw: list[dict] = []

    for category in REMOTIVE_CATEGORIES:
        url = f"{REMOTIVE_BASE_URL}?category={category}&limit={REMOTIVE_LIMIT}"
        print(f"{LOG_PREFIX} 📡 Coletor remotive: {category} (limit={REMOTIVE_LIMIT})...")

        try:
            req = Request(url, headers={"User-Agent": "JobRadar/1.0"})
            with urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except (URLError, HTTPError, json.JSONDecodeError, OSError) as e:
            print(f"{LOG_PREFIX} ✗ Erro Remotive ({category}): {e}")
            continue

        jobs = data.get("jobs") or []
        added = 0
        for j in jobs:
            pub_utc = _parse_remotive_date(j.get("publication_date"))
            if pub_utc is None:
                continue
            pub_local = pub_utc.astimezone()
            if pub_local < cutoff:
                continue
            all_raw.append({
                "title": j.get("title"),
                "company": j.get("company_name"),
                "location": j.get("candidate_required_location"),
                "salary": j.get("salary"),
                "url": j.get("url"),
                "description": j.get("description"),
                "date": j.get("publication_date"),
            })
            added += 1
        print(f"{LOG_PREFIX}   remotive/{category}: {added} vagas (últimas {REMOTIVE_RECENT_HOURS}h).")
    return all_raw
