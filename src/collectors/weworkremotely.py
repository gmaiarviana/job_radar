"""
Coletor We Work Remotely (Épico 2.3).
Fonte: RSS público de vagas remotas em management/finance.
Filtro por keywords no título: product manager, program manager, TPM.
"""

from typing import List, Dict
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
import xml.etree.ElementTree as ET
import html

LOG_PREFIX = "[fetch]"

WWR_RSS_URL = "https://weworkremotely.com/categories/remote-management-and-finance-jobs.rss"
WWR_TITLE_KEYWORDS = ["product manager", "program manager", "tpm"]


def _extract_company_and_title(full_title: str) -> tuple[str, str]:
    """
    Separa "Empresa: Título" em (empresa, título).
    Se não houver ":", assume apenas título.
    """
    full_title = (full_title or "").strip()
    if ":" in full_title:
        company, title = full_title.split(":", 1)
        return company.strip(), title.strip()
    return "", full_title


def collect_weworkremotely() -> List[Dict]:
    """
    Coletor: RSS We Work Remotely (management & finance).
    Retorna lista de jobs brutos para normalização.
    """
    print(f"{LOG_PREFIX} Coletor weworkremotely (RSS)...")

    try:
        req = Request(WWR_RSS_URL, headers={"User-Agent": "JobRadar/1.0"})
        with urlopen(req, timeout=30) as resp:
            content = resp.read()
    except (URLError, HTTPError, OSError) as e:
        print(f"{LOG_PREFIX} Erro WeWorkRemotely RSS: {e}")
        return []

    try:
        root = ET.fromstring(content)
    except ET.ParseError as e:
        print(f"{LOG_PREFIX} Erro parse RSS WeWorkRemotely: {e}")
        return []

    channel = root.find("channel")
    if channel is None:
        print(f"{LOG_PREFIX} RSS WeWorkRemotely sem canal 'channel'.")
        return []

    jobs: List[Dict] = []
    added = 0

    for item in channel.findall("item"):
        raw_title = (item.findtext("title") or "").strip()
        if not raw_title:
            continue

        lower_title = raw_title.lower()
        if not any(k in lower_title for k in WWR_TITLE_KEYWORDS):
            continue

        company, title = _extract_company_and_title(raw_title)
        link = (item.findtext("link") or "").strip()
        description_raw = (item.findtext("description") or "").strip()
        description = html.unescape(description_raw)
        pub_date = (item.findtext("pubDate") or "").strip()

        jobs.append(
            {
                "title": title or raw_title,
                "company": company,
                "location": "",
                "salary": None,
                "url": link,
                "description": description,
                "date": pub_date,
            }
        )
        added += 1

    print(f"{LOG_PREFIX} weworkremotely: {added} vagas apos filtro de titulo.")
    return jobs

