"""
Coletor Lever (Épico 3.3). API pública por site (companies.yaml com ats == "lever").
GET postings por ats_id, filtro por título; JD a partir de descriptionPlain + lists (texto sem HTML).
"""

import json
import re
import time
import html
from datetime import datetime, timezone
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

LEVER_POSTINGS_BASE = "https://api.lever.co/v0/postings"
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


def _format_salary(salary_range: dict | None) -> str | None:
    """Monta string a partir de salaryRange (currency, interval, min, max)."""
    if not salary_range or not isinstance(salary_range, dict):
        return None
    min_v = salary_range.get("min")
    max_v = salary_range.get("max")
    currency = (salary_range.get("currency") or "").strip()
    interval = (salary_range.get("interval") or "").strip()
    parts = []
    if min_v is not None or max_v is not None:
        if min_v is not None and max_v is not None and min_v != max_v:
            parts.append(f"{min_v}-{max_v}")
        else:
            parts.append(str(max_v if min_v is None else min_v))
    if currency:
        parts.append(currency)
    if interval:
        parts.append(interval)
    return " ".join(parts) if parts else None


def _build_description(posting: dict) -> str:
    """Concatena descriptionPlain, blocos lists (header + content sem HTML) e additionalPlain."""
    parts = []
    plain = (posting.get("descriptionPlain") or "").strip()
    if plain:
        parts.append(plain)
    lists = posting.get("lists") or []
    for item in lists:
        if not isinstance(item, dict):
            continue
        header = (item.get("text") or "").strip()
        content_html = item.get("content") or ""
        content = _strip_html(content_html)
        parts.append(f"{header}\n{content}\n")
    additional = (posting.get("additionalPlain") or "").strip()
    if additional:
        parts.append(additional)
    return "\n".join(parts).strip()


def _epoch_ms_to_iso(ms: int | None) -> str:
    """Converte epoch em milissegundos para ISO 8601 string (UTC)."""
    if ms is None:
        return ""
    try:
        ts = int(ms) / 1000.0
        dt = datetime.fromtimestamp(ts, tz=timezone.utc)
        return dt.isoformat()
    except (ValueError, OSError, OverflowError):
        return str(ms) if ms is not None else ""


def collect_lever(companies: list[dict]) -> list[dict]:
    """
    Coletor: Lever Postings API por empresa.
    companies: lista flat de dicts com name, ats, ats_id (ats == "lever").
    GET postings/{ats_id}?mode=json, filtra por título, monta JD de descriptionPlain + lists.
    Retorna lista de jobs brutos (title, company, location, salary, url, description, date).
    """
    all_raw: list[dict] = []
    if companies:
        print(f"{LOG_PREFIX} 📡 Coletor lever: {len(companies)} empresas...")

    for c in companies:
        ats_id = (c.get("ats_id") or "").strip()
        company_name = (c.get("name") or "").strip()
        if not ats_id:
            continue

        url = f"{LEVER_POSTINGS_BASE}/{ats_id}?mode=json"
        try:
            req = Request(url, headers={"User-Agent": "JobRadar/1.0"})
            with urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except HTTPError as e:
            print(f"{LOG_PREFIX} WARN lever/{ats_id}: {e.code} — slug inválido ou indisponível")
            time.sleep(0.5)
            continue
        except (URLError, json.JSONDecodeError, OSError) as e:
            print(f"{LOG_PREFIX} WARN lever/{ats_id}: {e} — slug inválido ou indisponível")
            time.sleep(0.5)
            continue

        time.sleep(0.5)

        postings = data if isinstance(data, list) else []
        for p in postings:
            if not isinstance(p, dict):
                continue
            title = (p.get("text") or "").strip()
            if not _title_matches(title):
                continue

            categories = p.get("categories") or {}
            location = ""
            if isinstance(categories, dict):
                loc = categories.get("location")
                if isinstance(loc, str):
                    location = loc.strip()
                elif loc is not None:
                    location = str(loc).strip()

            all_raw.append({
                "title": title,
                "company": company_name,
                "location": location,
                "salary": _format_salary(p.get("salaryRange")),
                "url": (p.get("hostedUrl") or "").strip(),
                "description": _build_description(p),
                "date": _epoch_ms_to_iso(p.get("createdAt")),
            })

    if companies:
        print(f"{LOG_PREFIX}   lever: {len(all_raw)} vagas de {len(companies)} empresas.")
    return all_raw
