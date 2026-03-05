"""
Coletor Working Nomads (Épico 7.7). API pública JSON, sem auth, sem paginação.
Filtro client-side: título com keywords PM/TPM. Recência: 7 dias.
"""

import json
from datetime import datetime, timezone, timedelta
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

from . import TITLE_KEYWORDS

WORKINGNOMADS_API_URL = "https://www.workingnomads.com/api/exposed_jobs/"
WORKINGNOMADS_RECENT_HOURS = 168
LOG_PREFIX = "[fetch]"


def _parse_date(date_val) -> datetime | None:
    """Interpreta campo de data como datetime com tz.
    Aceita: epoch int/float, epoch string numérica, ISO string.
    """
    if date_val is None or date_val == "":
        return None
    try:
        if isinstance(date_val, (int, float)):
            return datetime.fromtimestamp(date_val, tz=timezone.utc)
        s = str(date_val).strip()
        if s.isdigit() or (s.replace(".", "", 1).isdigit() and "." in s):
            return datetime.fromtimestamp(float(s), tz=timezone.utc)
        if s.endswith("Z"):
            return datetime.fromisoformat(s.replace("Z", "+00:00"))
        # Detect timezone offset: +HH:MM or -HH:MM after the date portion
        # Check for +/- after position 10 (past the YYYY-MM-DD part)
        tail = s[10:] if len(s) > 10 else ""
        if "+" in tail or (tail.count("-") > 0 and tail.rfind("-") > 0):
            return datetime.fromisoformat(s)
        return datetime.fromisoformat(s).replace(tzinfo=timezone.utc)
    except (ValueError, TypeError, OSError):
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
