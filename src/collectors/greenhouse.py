"""
Coletor Greenhouse (Épico 3.2). API pública por board (companies.yaml com ats == "greenhouse").
Lista vagas por board, filtra por título (PM/TPM/program manager), busca JD completo por job id.
"""

import json
import time
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

GREENHOUSE_BOARDS_BASE = "https://boards-api.greenhouse.io/v1/boards"
LOG_PREFIX = "[fetch]"

# Filtro de título: case insensitive
TITLE_KEYWORDS = (
    "product manager",
    "program manager",
    "tpm",
    "technical program",
)


def _title_matches(title: str) -> bool:
    """True se o título contém algum dos TITLE_KEYWORDS (case insensitive)."""
    if not title:
        return False
    t = title.lower()
    return any(kw in t for kw in TITLE_KEYWORDS)


def _location_name(loc: dict | None) -> str:
    """Extrai o nome da localização do objeto location da API."""
    if not loc or not isinstance(loc, dict):
        return ""
    return str(loc.get("name") or "").strip()


def collect_greenhouse(companies: list[dict]) -> list[dict]:
    """
    Coletor: Greenhouse Job Board API por empresa.
    companies: lista flat de dicts com name, ats, ats_id (extraída do yaml para ats == "greenhouse").
    Para cada empresa: GET boards/{ats_id}/jobs, filtra por título, depois GET boards/{ats_id}/jobs/{id} para content.
    Retorna lista de jobs brutos (title, company, location, salary=null, url, description, date).
    """
    all_raw: list[dict] = []
    if companies:
        print(f"{LOG_PREFIX} 📡 Coletor greenhouse: {len(companies)} empresas...")

    for c in companies:
        ats_id = (c.get("ats_id") or "").strip()
        company_name = (c.get("name") or "").strip()
        if not ats_id:
            continue

        list_url = f"{GREENHOUSE_BOARDS_BASE}/{ats_id}/jobs"
        try:
            req = Request(list_url, headers={"User-Agent": "JobRadar/1.0"})
            with urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except HTTPError as e:
            print(f"{LOG_PREFIX} WARN greenhouse/{ats_id}: {e.code} — slug inválido ou indisponível")
            time.sleep(0.5)
            continue
        except (URLError, json.JSONDecodeError, OSError) as e:
            print(f"{LOG_PREFIX} WARN greenhouse/{ats_id}: {e} — slug inválido ou indisponível")
            time.sleep(0.5)
            continue

        time.sleep(0.5)

        jobs = data.get("jobs") or []
        for j in jobs:
            title = (j.get("title") or "").strip()
            if not _title_matches(title):
                continue

            job_id = j.get("id")
            if job_id is None:
                continue

            detail_url = f"{GREENHOUSE_BOARDS_BASE}/{ats_id}/jobs/{job_id}"
            try:
                req = Request(detail_url, headers={"User-Agent": "JobRadar/1.0"})
                with urlopen(req, timeout=30) as resp:
                    detail = json.loads(resp.read().decode("utf-8"))
            except HTTPError as e:
                print(f"{LOG_PREFIX} WARN greenhouse/{ats_id}: {e.code} — slug inválido ou indisponível")
                time.sleep(0.5)
                continue
            except (URLError, json.JSONDecodeError, OSError) as e:
                print(f"{LOG_PREFIX} WARN greenhouse/{ats_id}: {e} — slug inválido ou indisponível")
                time.sleep(0.5)
                continue

            time.sleep(0.5)

            content = detail.get("content") or ""
            loc = detail.get("location")
            location_str = _location_name(loc) if isinstance(loc, dict) else (j.get("location") and _location_name(j["location"]) or "")

            all_raw.append({
                "title": title,
                "company": company_name,
                "location": location_str,
                "salary": None,
                "url": detail.get("absolute_url") or j.get("absolute_url") or "",
                "description": content,
                "date": detail.get("updated_at") or j.get("updated_at") or "",
            })

    if companies:
        print(f"{LOG_PREFIX}   greenhouse: {len(all_raw)} vagas de {len(companies)} empresas.")
    return all_raw
