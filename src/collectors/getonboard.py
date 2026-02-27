"""
Coletor Get on Board (Épico 7.2). API pública LATAM-first, sem auth.
Busca product manager remote; filtro por keywords PM/TPM no título.
"""

import json
import time
from datetime import datetime, timezone, timedelta
from urllib.request import urlopen, Request
from urllib.parse import urlencode
from urllib.error import URLError, HTTPError

from . import TITLE_KEYWORDS_LATAM

GETONBOARD_BASE = "https://www.getonbrd.com/api/v0/search/jobs"
GETONBOARD_RECENT_HOURS = 168
GETONBOARD_PER_PAGE = 50
LOG_PREFIX = "[fetch]"


def _parse_published_at(ts: int | None) -> datetime | None:
    """Converte published_at (Unix timestamp) para datetime UTC."""
    if ts is None:
        return None
    try:
        return datetime.fromtimestamp(int(ts), tz=timezone.utc)
    except (ValueError, TypeError, OSError):
        return None


def _matches_title(title: str) -> bool:
    """True se o título contém alguma keyword PM/TPM."""
    if not title:
        return False
    lower = title.lower()
    return any(kw in lower for kw in TITLE_KEYWORDS_LATAM)


def _format_salary(min_s: int | None, max_s: int | None) -> str | None:
    if min_s is None and max_s is None:
        return None
    if min_s is not None and max_s is not None and min_s != max_s:
        return f"{min_s}-{max_s}"
    return str(max_s if min_s is None else min_s)


def collect_getonboard() -> list[dict]:
    """
    Coletor: API Get on Board (LATAM). Busca product manager remote.
    Retorna lista de jobs brutos; apenas remote, título com PM/TPM; últimas 7 dias.
    """
    now_local = datetime.now().astimezone()
    cutoff = now_local - timedelta(hours=GETONBOARD_RECENT_HOURS)
    all_raw: list[dict] = []
    page = 1
    total_pages = 1

    print(f"{LOG_PREFIX} 📡 Coletor getonboard (LATAM)...")

    while page <= total_pages:
        params = {
            "query": "product manager",
            "remote": "true",
            "per_page": GETONBOARD_PER_PAGE,
            "page": page,
        }
        url = f"{GETONBOARD_BASE}?{urlencode(params)}"
        try:
            req = Request(url, headers={"User-Agent": "JobRadar/1.0"})
            with urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except (URLError, HTTPError, json.JSONDecodeError, OSError) as e:
            print(f"{LOG_PREFIX} ✗ Erro Get on Board (página {page}): {e}")
            break

        meta = data.get("meta") or {}
        total_pages = int(meta.get("total_pages", 1) or 1)
        # Limite de segurança para evitar requests em excesso
        total_pages = min(total_pages, 5)
        items = data.get("data") or []

        for item in items:
            if not isinstance(item, dict):
                continue
            attrs = item.get("attributes") or item
            if not isinstance(attrs, dict):
                continue
            if not attrs.get("remote"):
                continue
            title = attrs.get("title") or ""
            if not _matches_title(title):
                continue
            pub_ts = attrs.get("published_at")
            pub_dt = _parse_published_at(pub_ts)
            if pub_dt is not None:
                pub_local = pub_dt.astimezone()
                if pub_local < cutoff:
                    continue
            links = item.get("links") or {}
            url_job = links.get("public_url") or ""
            desc = attrs.get("description") or ""
            date_str = ""
            if pub_ts is not None:
                date_str = datetime.fromtimestamp(pub_ts, tz=timezone.utc).isoformat()
            # A API de search retorna o nome da empresa em attributes.company (string)
            company = str(attrs.get("company") or "")

            all_raw.append({
                "title": title,
                "company": company,
                "location": "Remote",
                "salary": _format_salary(attrs.get("min_salary"), attrs.get("max_salary")),
                "url": url_job,
                "description": desc,
                "date": date_str,
            })

        page += 1
        if page <= total_pages:
            # Rate limiting entre requests de páginas subsequentes
            time.sleep(1)

    print(f"{LOG_PREFIX}   getonboard: {len(all_raw)} vagas (remote, PM/TPM, últimas {GETONBOARD_RECENT_HOURS}h).")
    return all_raw
