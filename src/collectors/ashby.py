"""
Coletor Ashby (Épico 3.4). API pública oficial GET por job board (companies.yaml com ats == "ashby").
GET https://api.ashbyhq.com/posting-api/job-board/{ats_id} — retorna JSON com chave jobs.
"""

import json
import re
import time
import html
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

ASHBY_JOB_BOARD_BASE = "https://api.ashbyhq.com/posting-api/job-board"
LOG_PREFIX = "[fetch]"

TITLE_KEYWORDS = (
    "product manager",
    "program manager",
    "tpm",
    "technical program",
)


def _title_matches(title: str) -> bool:
    if not title:
        return False
    t = title.lower()
    return any(kw in t for kw in TITLE_KEYWORDS)


def _strip_html(html_str: str) -> str:
    """Remove tags e normaliza entidades HTML para texto corrido."""
    if not html_str:
        return ""
    s = str(html_str).strip()
    s = re.sub(r"<[^>]+>", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return html.unescape(s)


def _get_description(job: dict) -> str:
    """Extrai descrição: descriptionPlain (oficial) ou strip de descriptionHtml/description."""
    plain = (job.get("descriptionPlain") or "").strip()
    if plain:
        return plain
    html_val = job.get("descriptionHtml") or job.get("description") or ""
    return _strip_html(html_val)


def collect_ashby(companies: list[dict]) -> list[dict]:
    """
    Coletor: Ashby Job Board API (GET oficial) por empresa.
    companies: lista flat de dicts com name, ats, ats_id (ats == "ashby").
    GET https://api.ashbyhq.com/posting-api/job-board/{ats_id}
    Retorna lista de jobs brutos (title, company, location, salary=null, url, description, date).
    """
    all_raw: list[dict] = []
    if companies:
        print(f"{LOG_PREFIX} 📡 Coletor ashby: {len(companies)} empresas...")

    for c in companies:
        ats_id = (c.get("ats_id") or "").strip()
        company_name = (c.get("name") or "").strip()
        if not ats_id:
            continue

        url = f"{ASHBY_JOB_BOARD_BASE}/{ats_id}"
        try:
            req = Request(url, headers={"User-Agent": "JobRadar/1.0"})
            with urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except HTTPError as e:
            print(f"{LOG_PREFIX} WARN ashby/{ats_id}: {e.code} — slug inválido ou indisponível")
            time.sleep(0.5)
            continue
        except (URLError, json.JSONDecodeError, OSError) as e:
            print(f"{LOG_PREFIX} WARN ashby/{ats_id}: {e} — slug inválido ou indisponível")
            time.sleep(0.5)
            continue

        time.sleep(0.5)

        jobs = data.get("jobs") or []
        for j in jobs:
            if not isinstance(j, dict):
                continue
            title = (j.get("title") or "").strip()
            if not _title_matches(title):
                continue

            loc = j.get("location")
            location = (loc.strip() if isinstance(loc, str) else (str(loc).strip() if loc is not None else ""))

            all_raw.append({
                "title": title,
                "company": company_name,
                "location": location,
                "salary": None,
                "url": (j.get("jobUrl") or "").strip(),
                "description": _get_description(j),
                "date": (j.get("publishedAt") or "").strip() if isinstance(j.get("publishedAt"), str) else "",
            })

    if companies:
        print(f"{LOG_PREFIX}   ashby: {len(all_raw)} vagas de {len(companies)} empresas.")
    return all_raw
