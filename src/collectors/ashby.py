"""
Coletor Ashby (Épico 3.4). API pública por job board (companies.yaml com ats == "ashby").
POST para listar vagas; response com estrutura própria — mapeamento flexível por campo.
"""

import html
import json
import re
import time
from datetime import datetime, timezone
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

ASHBY_LIST_URL = "https://jobs.ashbyhq.com/api/non-user-facing/job-board/job-posting/list"
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
    """Extrai descrição em texto puro: descriptionPlain ou strip de descriptionHtml/description."""
    plain = (job.get("descriptionPlain") or "").strip()
    if plain:
        return plain
    html_val = job.get("descriptionHtml") or job.get("description") or ""
    return _strip_html(html_val)


def _get_location(job: dict) -> str:
    """Extrai localização (string)."""
    loc = job.get("location")
    if isinstance(loc, str):
        return loc.strip()
    if loc is not None:
        return str(loc).strip()
    return ""


def _get_url(job: dict) -> str:
    """Extrai URL da vaga (jobUrl ou url)."""
    return (job.get("jobUrl") or job.get("url") or "").strip()


def _get_date_iso(job: dict) -> str:
    """Extrai data como ISO string (publishedAt, updatedAt ou createdAt)."""
    for key in ("publishedAt", "updatedAt", "createdAt", "updated_at", "created_at"):
        val = job.get(key)
        if val is None:
            continue
        if isinstance(val, str) and val.strip():
            return val.strip()
        if isinstance(val, (int, float)):
            try:
                ts = int(val) / 1000.0 if val > 1e12 else int(val)
                return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()
            except (ValueError, OSError, OverflowError):
                return str(val)
    return ""


def _get_salary(job: dict) -> str | None:
    """Extrai salário: scrapeableCompensationSalarySummary, compensationTierSummary ou compensation."""
    comp = job.get("compensation")
    if isinstance(comp, dict):
        s = (comp.get("scrapeableCompensationSalarySummary") or comp.get("compensationTierSummary") or "").strip()
        if s:
            return s
    if isinstance(comp, str) and comp.strip():
        return comp.strip()
    return None


def collect_ashby(companies: list[dict]) -> list[dict]:
    """
    Coletor: Ashby Job Board API (POST) por empresa.
    companies: lista flat de dicts com name, ats, ats_id (ats == "ashby").
    POST body: {"organizationHostedJobsPageName": "{ats_id}"}.
    Retorna lista de jobs brutos (title, company, location, salary, url, description, date).
    """
    all_raw: list[dict] = []
    if companies:
        print(f"{LOG_PREFIX} 📡 Coletor ashby: {len(companies)} empresas...")

    for c in companies:
        ats_id = (c.get("ats_id") or "").strip()
        company_name = (c.get("name") or "").strip()
        if not ats_id:
            continue

        body = json.dumps({"organizationHostedJobsPageName": ats_id}).encode("utf-8")
        req = Request(
            ASHBY_LIST_URL,
            data=body,
            method="POST",
            headers={"User-Agent": "JobRadar/1.0", "Content-Type": "application/json"},
        )
        try:
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

        jobs = data.get("jobs") or data.get("results") or data.get("jobPostings") or []
        if isinstance(data, list):
            jobs = data

        for j in jobs:
            if not isinstance(j, dict):
                continue
            title = (j.get("title") or j.get("text") or "").strip()
            if not _title_matches(title):
                continue

            all_raw.append({
                "title": title,
                "company": company_name,
                "location": _get_location(j),
                "salary": _get_salary(j),
                "url": _get_url(j),
                "description": _get_description(j),
                "date": _get_date_iso(j),
            })

    if companies:
        print(f"{LOG_PREFIX}   ashby: {len(all_raw)} vagas de {len(companies)} empresas.")
    return all_raw
