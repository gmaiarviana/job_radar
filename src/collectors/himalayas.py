"""
Coletor Himalayas (Épico 7.7). API pública JSON paginada, sem auth.
Filtro client-side: título com keywords PM/TPM. Recência: 7 dias.
"""

import json
import time
from datetime import datetime, timezone, timedelta
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

from . import TITLE_KEYWORDS

HIMALAYAS_API_URL = "https://himalayas.app/jobs/api"
HIMALAYAS_RECENT_HOURS = 168
HIMALAYAS_MAX_PAGES = 5
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


def collect_himalayas() -> list[dict]:
    """
    Coletor: API Himalayas (JSON paginado, até 5 páginas).
    Retorna lista de jobs brutos para normalização.
    """
    now_local = datetime.now().astimezone()
    cutoff = now_local - timedelta(hours=HIMALAYAS_RECENT_HOURS)
    all_raw: list[dict] = []

    print(f"{LOG_PREFIX} 📡 Coletor himalayas...")

    for page in range(1, HIMALAYAS_MAX_PAGES + 1):
        url = f"{HIMALAYAS_API_URL}?page={page}"
        try:
            req = Request(url, headers={"User-Agent": "JobRadar/1.0"})
            with urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except (URLError, HTTPError, json.JSONDecodeError, OSError) as e:
            print(f"{LOG_PREFIX} ✗ Erro Himalayas (página {page}): {e}")
            break

        jobs = data.get("jobs") or data.get("data") or []
        if not jobs:
            break

        for j in jobs:
            if not isinstance(j, dict):
                continue
            title = j.get("title") or ""
            if not _matches_title(title):
                continue

            # Filtro de recência se campo de data disponível
            date_val = j.get("pubDate") or j.get("published_at") or j.get("postedDate") or j.get("updated_at") or ""
            pub_dt = _parse_date(date_val)
            if pub_dt is not None:
                pub_local = pub_dt.astimezone()
                if pub_local < cutoff:
                    continue

            all_raw.append({
                "title": title,
                "company": j.get("companyName") or j.get("company_name") or "",
                "location": j.get("locationRestriction") or j.get("location") or "",
                "salary": None,
                "url": j.get("applicationLink") or j.get("application_link") or j.get("url") or "",
                "description": j.get("description") or "",
                "date": date_val,
            })

        if page < HIMALAYAS_MAX_PAGES:
            time.sleep(0.5)

    print(f"{LOG_PREFIX}   himalayas: {len(all_raw)} vagas (PM/TPM, últimas {HIMALAYAS_RECENT_HOURS}h).")
    return all_raw
