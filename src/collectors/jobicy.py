"""
Coletor Jobicy (Épico 2.4). API pública, industry=product, count=50.
Filtro de recência: últimas 48h (pubDate).
"""

import json
from datetime import datetime, timezone, timedelta
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

JOBICY_RECENT_HOURS = 48
JOBICY_COUNT = 50
JOBICY_BASE_URL = "https://jobicy.com/api/v2/remote-jobs"
LOG_PREFIX = "[fetch]"


def _parse_jobicy_date(pub_date: str) -> datetime | None:
    """Interpreta pubDate (ex: 2026-02-23T15:17:26+00:00) como UTC."""
    if not pub_date:
        return None
    try:
        s = str(pub_date).strip()
        if s.endswith("Z"):
            return datetime.fromisoformat(s.replace("Z", "+00:00"))
        if "+" in s or (len(s) > 10 and s[10:11] == "+"):
            return datetime.fromisoformat(s)
        return datetime.fromisoformat(s).replace(tzinfo=timezone.utc)
    except (ValueError, TypeError):
        return None


def _format_salary(j: dict) -> str | None:
    """Monta string de salário a partir de salaryMin, salaryMax, salaryCurrency, salaryPeriod."""
    min_s = j.get("salaryMin")
    max_s = j.get("salaryMax")
    currency = (j.get("salaryCurrency") or "").strip()
    period = (j.get("salaryPeriod") or "").strip()
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
    if period:
        parts.append(period)
    return " ".join(parts) if parts else None


def collect_jobicy() -> list[dict]:
    """
    Coletor: API Jobicy (industry=product, count=50).
    Retorna lista de jobs brutos para normalização (últimas 48h).
    """
    cutoff = datetime.now(timezone.utc) - timedelta(hours=JOBICY_RECENT_HOURS)
    url = f"{JOBICY_BASE_URL}?industry=product&count={JOBICY_COUNT}"
    print(f"{LOG_PREFIX} Coletor jobicy (industry=product, count={JOBICY_COUNT})...")

    try:
        req = Request(url, headers={"User-Agent": "JobRadar/1.0"})
        with urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except HTTPError as e:
        if e.code == 400 and "industry=product" in url:
            url = f"{JOBICY_BASE_URL}?count={JOBICY_COUNT}"
            try:
                req = Request(url, headers={"User-Agent": "JobRadar/1.0"})
                with urlopen(req, timeout=30) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
            except (URLError, HTTPError, json.JSONDecodeError, OSError):
                print(f"{LOG_PREFIX} Erro Jobicy (fallback): {e}")
                return []
        else:
            print(f"{LOG_PREFIX} Erro Jobicy: {e}")
            return []
    except (URLError, json.JSONDecodeError, OSError) as e:
        print(f"{LOG_PREFIX} Erro Jobicy: {e}")
        return []

    jobs = data.get("jobs") or []
    all_raw: list[dict] = []
    added = 0

    for j in jobs:
        pub = _parse_jobicy_date(j.get("pubDate"))
        if pub is None or pub < cutoff:
            continue
        raw_industry = j.get("jobIndustry")
        if isinstance(raw_industry, list):
            industry_str = " ".join(str(x) for x in raw_industry).lower()
        else:
            industry_str = str(raw_industry or "").lower()
        if "product" not in industry_str and industry_str.strip():
            continue
        all_raw.append({
            "title": j.get("jobTitle"),
            "company": j.get("companyName"),
            "location": j.get("jobGeo") or "",
            "salary": _format_salary(j),
            "url": j.get("url"),
            "description": j.get("jobDescription"),
            "date": j.get("pubDate"),
        })
        added += 1

    print(f"{LOG_PREFIX}   jobicy: {added} vagas (ultimas {JOBICY_RECENT_HOURS}h).")
    return all_raw
