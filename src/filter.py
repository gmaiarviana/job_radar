"""
Hard filters (gratuitos): location + quality guard.
Lê raw de data/raw/, aplica filtros, salva em data/filtered/.
Pipeline: fetch.py → filter.py → score.py
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

from src.fetch_pipeline import load_config


def _ensure_console_utf8() -> None:
    """Evita UnicodeEncodeError no Windows (console cp1252)."""
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except (AttributeError, OSError):
            pass

# Allowlist: passa se location contiver pelo menos um destes termos (case insensitive)
# Location vazia também passa (sem info suficiente para descartar; LLM decide)
def apply_title_filter(jobs: list[dict], exclude_keywords: list[str]) -> tuple[list[dict], list[dict]]:
    """Descartar vagas cujo título contém qualquer keyword (case insensitive). Retorna (passaram, descartados)."""
    if not exclude_keywords:
        return jobs, []
    keywords_lower = [k.strip().lower() for k in exclude_keywords if k]
    passed = []
    discarded = []
    for job in jobs:
        title = (job.get("title") or "").strip()
        title_lower = title.lower()
        if any(kw in title_lower for kw in keywords_lower):
            discarded.append(job)
        else:
            passed.append(job)
    return passed, discarded


def apply_location_blocklist(jobs: list[dict], blocklist_patterns: list[str]) -> tuple[list[dict], list[dict]]:
    """Descartar vagas cujo location ou jd_full contém qualquer padrão US-only (case insensitive). Retorna (passaram, descartados)."""
    if not blocklist_patterns:
        return jobs, []
    patterns_lower = [p.strip().lower() for p in blocklist_patterns if p]
    passed = []
    discarded = []
    for job in jobs:
        location = (job.get("location") or "").strip().lower()
        jd_full = (job.get("jd_full") or job.get("description") or "").strip().lower()
        if any(pat in location or pat in jd_full for pat in patterns_lower):
            discarded.append(job)
        else:
            passed.append(job)
    return passed, discarded


# Allowlist: passa se location contiver pelo menos um destes termos (case insensitive)
# Location vazia também passa (sem info suficiente para descartar; LLM decide)
LOCATION_ALLOW_PATTERNS = [
    "latam",
    "latin america",
    "south america",
    "worldwide",
    "remote worldwide",
    "brazil",
    "brasil",
    "colombia",
    "mexico",
    "argentina",
    "chile",
    "peru",
    "remote",
]


def apply_location_filter(jobs: list[dict]) -> tuple[list[dict], list[dict]]:
    passed = []
    discarded = []
    for job in jobs:
        location = (job.get("location") or "").strip()
        if not location:
            passed.append(job)
            continue
        loc_lower = location.lower()
        if any(p in loc_lower for p in LOCATION_ALLOW_PATTERNS):
            passed.append(job)
        else:
            discarded.append(job)
    return passed, discarded


# --- Quality guard (mesma lógica de fetch_pipeline.apply_quality_guard) ---
MIN_JD_LENGTH = 500
GENERIC_TITLES = frozenset(
    s.strip().lower()
    for s in (
        "opportunity", "job opening", "job", "position",
        "remote", "new job", "open position",
    )
)


def _quality_guard_reason(job: dict) -> str | None:
    """Motivo de descarte ou None se passar."""
    jd = (job.get("jd_full") or job.get("description") or "").strip()
    if len(jd) < MIN_JD_LENGTH:
        return "quality"
    title = (job.get("title") or "").strip()
    if not title:
        return "quality"
    if title.lower() in GENERIC_TITLES:
        return "quality"
    company = (job.get("company") or "").strip()
    if not company:
        return "quality"
    return None


def apply_quality_guard(jobs: list[dict]) -> tuple[list[dict], list[dict]]:
    """Descartar JD < 500 chars, título vazio/genérico, empresa vazia. Retorna (passaram, descartados)."""
    passed = []
    discarded = []
    for job in jobs:
        if _quality_guard_reason(job) is None:
            passed.append(job)
        else:
            discarded.append(job)
    return passed, discarded


def resolve_input_path(input_path: str | None, date_str: str | None) -> Path | None:
    """Retorna Path do raw: por --input ou por --date (mais recente da data)."""
    if input_path:
        p = Path(input_path)
        return p if p.exists() else None
    if date_str:
        raw_dir = Path("data/raw")
        if not raw_dir.exists():
            return None
        candidates = sorted(raw_dir.glob(f"{date_str}*.json"), reverse=True)
        return candidates[0] if candidates else None
    return None


def main() -> None:
    _ensure_console_utf8()
    parser = argparse.ArgumentParser(
        description="Aplica hard filters (location + quality) em arquivo raw; salva em data/filtered/."
    )
    parser.add_argument(
        "--input",
        metavar="path",
        help="Caminho direto para o arquivo raw (ex: data/raw/seed_2026-02-24_153218.json)",
    )
    parser.add_argument(
        "--date",
        metavar="YYYY-MM-DD",
        help="Alternativa ao --input: usa o raw mais recente desta data",
    )
    args = parser.parse_args()

    if not args.input and not args.date:
        parser.error("Informe --input <path> ou --date YYYY-MM-DD.")

    raw_path = resolve_input_path(args.input, args.date)
    if not raw_path:
        if args.input:
            print(f"[filter.py] Erro: arquivo nao encontrado: {args.input}")
        else:
            print(f"[filter.py] Erro: nenhum arquivo raw para a data: {args.date}")
        return

    try:
        raw_data = json.loads(raw_path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"[filter.py] Erro ao ler {raw_path}: {e}")
        return

    jobs = raw_data.get("jobs", [])
    total_input = len(jobs)
    if total_input == 0:
        print("[filter.py] Aviso: nenhuma vaga no arquivo raw.")
        return

    config = load_config()
    filters_config = config.get("filters") or {}
    exclude_title_keywords = filters_config.get("exclude_title_keywords") or []
    location_blocklist_patterns = filters_config.get("location_blocklist_patterns") or []

    # 1. Title filter (exclude_title_keywords)
    after_title, discarded_title_list = apply_title_filter(jobs, exclude_title_keywords)
    discarded_title = len(discarded_title_list)

    # 2. Location blocklist (US-only patterns in location or jd_full)
    after_blocklist, discarded_blocklist_list = apply_location_blocklist(after_title, location_blocklist_patterns)
    discarded_blocklist = len(discarded_blocklist_list)

    # 3. Location allowlist
    after_location, discarded_location_list = apply_location_filter(after_blocklist)
    discarded_location = len(discarded_location_list)

    # 4. Quality guard
    after_quality, discarded_quality_list = apply_quality_guard(after_location)
    discarded_quality = len(discarded_quality_list)
    total_passed = len(after_quality)

    out_dir = Path("data/filtered")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / raw_path.name

    # Jobs salvos com dados intactos (jd_full sem truncamento)
    output = {
        "filtered_at": datetime.now().isoformat(),
        "source_file": raw_path.name,
        "summary": {
            "total_input": total_input,
            "discarded_title": discarded_title,
            "discarded_blocklist": discarded_blocklist,
            "discarded_location": discarded_location,
            "discarded_quality": discarded_quality,
            "total_passed": total_passed,
        },
        "jobs": after_quality,
    }

    out_path.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
    print(
        f"[filter.py] OK {total_passed} vagas passaram | "
        f"title: {discarded_title} | blocklist: {discarded_blocklist} | location: {discarded_location} | quality: {discarded_quality} -> {out_path}"
    )


if __name__ == "__main__":
    main()
