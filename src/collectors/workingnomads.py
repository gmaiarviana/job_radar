"""
Coletor Working Nomads (Épico 7.7). API pública JSON, sem auth, sem paginação.
Filtro client-side: título com keywords PM/TPM. Recência: 7 dias.
"""

import json
from datetime import datetime, timezone, timedelta
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

from . import TITLE_KEYWORDS

WORKINGNOMADS_API_URL = "https://www.workingnomads.com/jobsapi"
WORKINGNOMADS_RECENT_HOURS = 168
LOG_PREFIX = "[fetch]"


def _parse_date(date_str: str) -> datetime | None:
    """Interpreta campo de data ISO como datetime com tz."""
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


def _matches_title(title: str) -> bool:
    """True se o título contém alguma keyword PM/TPM."""
    if not title:
        return False
    lower = title.lower()
    return any(kw in lower for kw in TITLE_KEYWORDS)


def collect_workingnomads() -> list[dict]:
    """
    Coletor: API Working Nomads (JSON, request único).
    Retorna lista de jobs brutos para normalização.
    """
    now_local = datetime.now().astimezone()
    cutoff = now_local - timedelta(hours=WORKINGNOMADS_RECENT_HOURS)
    all_raw: list[dict] = []

    print(f"{LOG_PREFIX} 📡 Coletor workingnomads...")

    try:
        req = Request(WORKINGNOMADS_API_URL, headers={"User-Agent": "JobRadar/1.0"})
        with urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except (URLError, HTTPError, json.JSONDecodeError, OSError) as e:
        print(f"{LOG_PREFIX} ✗ Erro Working Nomads: {e}")
        return []

    jobs = data if isinstance(data, list) else data.get("jobs") or data.get("data") or []

    added = 0
    for j in jobs:
        if not isinstance(j, dict):
            continue
        title = j.get("title") or ""
        if not _matches_title(title):
            continue

        # Filtro de recência
        date_val = j.get("pub_date") or j.get("pubDate") or j.get("published_at") or j.get("date") or ""
        pub_dt = _parse_date(date_val)
        if pub_dt is not None:
            pub_local = pub_dt.astimezone()
            if pub_local < cutoff:
                continue

        all_raw.append({
            "title": title,
            "company": j.get("company_name") or j.get("company") or "",
            "location": j.get("location") or "",
            "salary": None,
            "url": j.get("url") or "",
            "description": j.get("description") or "",
            "date": date_val,
        })
        added += 1

    print(f"{LOG_PREFIX}   workingnomads: {added} vagas (PM/TPM, últimas {WORKINGNOMADS_RECENT_HOURS}h).")
    return all_raw
