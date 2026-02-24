"""
Hard filters (gratuitos): location + quality guard.
Lê raw de data/raw/, aplica filtros, salva em data/filtered/.
Pipeline: fetch.py → filter.py → score.py
"""

import argparse
import json
from datetime import datetime
from pathlib import Path

# --- Location filter (expandido em relação ao score.py) ---
LOCATION_DISCARD_PATTERNS = [
    "us only", "usa only", "united states only", "north america",
    "eu only", "europe only", "uk only", "on-site",
    "auckland", "london", "new york", "san francisco", "sydney", "berlin", "paris",
]
LOCATION_EXCEPTION_PATTERNS = ["latam", "worldwide", "remote worldwide"]


def apply_location_filter(jobs: list[dict]) -> tuple[list[dict], list[dict]]:
    """
    Descartar se location contiver algum dos padrões de descarte (case insensitive).
    Exceção: se também contiver latam, worldwide ou remote worldwide, não descartar.
    Retorna (passaram, descartados_por_location).
    """
    passed = []
    discarded = []
    for job in jobs:
        location = (job.get("location") or "").strip()
        if not location:
            passed.append(job)
            continue
        loc_lower = location.lower()
        should_discard = any(p in loc_lower for p in LOCATION_DISCARD_PATTERNS)
        if should_discard:
            if any(ex in loc_lower for ex in LOCATION_EXCEPTION_PATTERNS):
                should_discard = False
        if should_discard:
            discarded.append(job)
        else:
            passed.append(job)
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
            print(f"[filter.py] ❌ Arquivo não encontrado: {args.input}")
        else:
            print(f"[filter.py] ❌ Nenhum arquivo raw encontrado para a data: {args.date}")
        return

    try:
        raw_data = json.loads(raw_path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"[filter.py] ✗ Erro ao ler {raw_path}: {e}")
        return

    jobs = raw_data.get("jobs", [])
    total_input = len(jobs)
    if total_input == 0:
        print("[filter.py] ⚠️ Nenhuma vaga no arquivo raw.")
        return

    # 1. Location filter
    after_location, discarded_location_list = apply_location_filter(jobs)
    discarded_location = len(discarded_location_list)

    # 2. Quality guard
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
            "total_passed": total_passed,
            "discarded_location": discarded_location,
            "discarded_quality": discarded_quality,
        },
        "jobs": after_quality,
    }

    out_path.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
    print(
        f"[filter.py] ✅ {total_passed} vagas passaram | "
        f"location: {discarded_location} | quality: {discarded_quality} → {out_path}"
    )


if __name__ == "__main__":
    main()
