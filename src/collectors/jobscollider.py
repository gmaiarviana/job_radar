"""
Coletor JobsCollider (Épico 7.7). RSS público, dois feeds (product + project management).
Filtro client-side: título com keywords PM/TPM. Recência: 7 dias por pubDate.
"""

from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
import xml.etree.ElementTree as ET
import html

from . import TITLE_KEYWORDS

JOBSCOLLIDER_FEEDS = [
    "https://jobscollider.com/rss/product-management",
    "https://jobscollider.com/rss/project-management",
]
JOBSCOLLIDER_RECENT_HOURS = 168
LOG_PREFIX = "[fetch]"


def _parse_pub_date(date_str: str) -> datetime | None:
    """Interpreta pubDate RFC 2822 (ex: Mon, 03 Mar 2026 12:00:00 GMT)."""
    if not date_str:
        return None
    try:
        dt = parsedate_to_datetime(date_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except (ValueError, TypeError):
        return None


def _matches_title(title: str) -> bool:
    """True se o título contém alguma keyword PM/TPM."""
    if not title:
        return False
    lower = title.lower()
    return any(kw in lower for kw in TITLE_KEYWORDS)


def collect_jobscollider() -> list[dict]:
    """
    Coletor: RSS JobsCollider (product-management + project-management).
    Retorna lista de jobs brutos para normalização (últimas 7 dias).
    """
    now_local = datetime.now().astimezone()
    cutoff = now_local - timedelta(hours=JOBSCOLLIDER_RECENT_HOURS)
    all_raw: list[dict] = []
    seen_urls: set[str] = set()

    print(f"{LOG_PREFIX} 📡 Coletor jobscollider (RSS)...")

    for feed_url in JOBSCOLLIDER_FEEDS:
        try:
            req = Request(feed_url, headers={"User-Agent": "JobRadar/1.0"})
            with urlopen(req, timeout=30) as resp:
                content = resp.read()
        except (URLError, HTTPError, OSError) as e:
            print(f"{LOG_PREFIX} ✗ Erro JobsCollider ({feed_url}): {e}")
            continue

        try:
            root = ET.fromstring(content)
        except ET.ParseError as e:
            print(f"{LOG_PREFIX} ✗ Erro parse RSS JobsCollider ({feed_url}): {e}")
            continue

        channel = root.find("channel")
        if channel is None:
            continue

        for item in channel.findall("item"):
            raw_title = (item.findtext("title") or "").strip()
            if not raw_title:
                continue
            if not _matches_title(raw_title):
                continue

            link = (item.findtext("link") or "").strip()

            # Dedupe interno por URL (feeds podem ter sobreposição)
            if link and link in seen_urls:
                continue
            if link:
                seen_urls.add(link)

            # Filtro de recência por pubDate
            pub_date_str = (item.findtext("pubDate") or "").strip()
            pub_dt = _parse_pub_date(pub_date_str)
            if pub_dt is not None:
                pub_local = pub_dt.astimezone()
                if pub_local < cutoff:
                    continue

            description_raw = (item.findtext("description") or "").strip()
            description = html.unescape(description_raw)

            all_raw.append({
                "title": raw_title,
                "company": "",
                "location": "",
                "salary": None,
                "url": link,
                "description": description,
                "date": pub_date_str,
            })

    print(f"{LOG_PREFIX}   jobscollider: {len(all_raw)} vagas (PM/TPM, últimas {JOBSCOLLIDER_RECENT_HOURS}h).")
    return all_raw
