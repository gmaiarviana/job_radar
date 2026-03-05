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
HIMALAYAS_PAGE_SIZE = 20
LOG_PREFIX = "[fetch]"


def _parse_date(date_val) -> datetime | None:
    """Interpreta campo de data como datetime com tz.
    Aceita: epoch int/float, epoch string numérica, ISO string.
    """
    if date_val is None or date_val == "":
        return None
    try:
        # Numeric epoch (int, float, or string of digits)
        if isinstance(date_val, (int, float)):
            return datetime.fromtimestamp(date_val, tz=timezone.utc)
        s = str(date_val).strip()
        if s.isdigit() or (s.replace(".", "", 1).isdigit() and "." in s):
            return datetime.fromtimestamp(float(s), tz=timezone.utc)
        # ISO string
        if s.endswith("Z"):
            return datetime.fromisoformat(s.replace("Z", "+00:00"))
        # Detect timezone offset: +HH:MM or -HH:MM after the date portion
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


def collect_himalayas() -> list[dict]:
    """
    Coletor: API Himalayas (JSON paginado, até 5 páginas).
    Retorna lista de jobs brutos para normalização.
    """
    now_local = datetime.now().astimezone()
    cutoff = now_local - timedelta(hours=HIMALAYAS_RECENT_HOURS)
    all_raw: list[dict] = []

    print(f"{LOG_PREFIX} 📡 Coletor himalayas...")

    for page in range(HIMALAYAS_MAX_PAGES):
        offset = page * HIMALAYAS_PAGE_SIZE
        url = f"{HIMALAYAS_API_URL}?limit={HIMALAYAS_PAGE_SIZE}&offset={offset}"
        try:
            req = Request(url, headers={"User-Agent": "JobRadar/1.0"})
            with urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except (URLError, HTTPError, json.JSONDecodeError, OSError) as e:
            print(f"{LOG_PREFIX} ✗ Erro Himalayas (offset {offset}): {e}")
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

            # locationRestrictions: pode ser lista ou string
            loc_raw = j.get("locationRestrictions") or j.get("locationRestriction") or j.get("location") or ""
            if isinstance(loc_raw, list):
                location = ", ".join(str(x) for x in loc_raw if x)
            else:
                location = str(loc_raw)

            # Salário: minSalary/maxSalary/currency quando disponíveis
            salary = None
            min_sal = j.get("minSalary")
            max_sal = j.get("maxSalary")
            currency = j.get("currency") or "USD"
            if min_sal and max_sal:
                salary = f"{currency} {min_sal}–{max_sal}"
            elif min_sal:
                salary = f"{currency} {min_sal}+"
            elif max_sal:
                salary = f"Up to {currency} {max_sal}"

            all_raw.append({
                "title": title,
                "company": j.get("companyName") or j.get("company_name") or "",
                "location": location,
                "salary": salary,
                "url": j.get("applicationLink") or j.get("application_link") or j.get("url") or "",
                "description": j.get("description") or "",
                "date": str(date_val) if date_val else "",
            })

        if page < HIMALAYAS_MAX_PAGES - 1:
            time.sleep(0.5)

    print(f"{LOG_PREFIX}   himalayas: {len(all_raw)} vagas (PM/TPM, últimas {HIMALAYAS_RECENT_HOURS}h).")
    return all_raw
