"""
fetch.py — CLI do pipeline multi-fonte de coleta de vagas.

Componentes: job_schema, collectors/*, fetch_pipeline.
Uso: python src/fetch.py  |  python src/fetch.py --date 2026-02-22  |  python -m src.fetch
"""

import os
import sys
import io
import json
import argparse
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

# Console Windows: evita UnicodeEncodeError em emojis dos logs
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# Garante projeto na path ao rodar como python src/fetch.py
if __name__ == "__main__":
    _root = Path(__file__).resolve().parent.parent
    if str(_root) not in sys.path:
        sys.path.insert(0, str(_root))

from dotenv import load_dotenv
from openai import OpenAI

from src.fetch_pipeline import (
    load_config,
    load_companies,
    run_pipeline,
    remove_duplicates,
    filter_old_jobs,
    apply_quality_guard,
)
from src.collectors.remotive import collect_remotive
from src.collectors.openai_search import collect_openai_web_search
from src.collectors.weworkremotely import collect_weworkremotely
from src.collectors.jobicy import collect_jobicy

load_dotenv()

LOG_PREFIX = "[fetch]"


def main():
    parser = argparse.ArgumentParser(
        description="Pipeline multi-fonte de coleta de vagas (Épico 2.1/2.2)"
    )
    parser.add_argument("--date", default=str(date.today()), help="Data no formato YYYY-MM-DD")
    parser.add_argument("--dry-run", action="store_true", help="Apenas mostra o que seria buscado")
    parser.add_argument("--validate-companies", action="store_true", help="Valida config/companies.yaml (Épico 3.1) e sai")
    args = parser.parse_args()

    if args.validate_companies:
        try:
            data = load_companies()
            total = sum(len(entries) for entries in data["companies"].values())
            print(f"{LOG_PREFIX} ✅ config/companies.yaml válido: {len(data['companies'])} setores, {total} empresas-alvo")
            return
        except Exception as e:
            print(f"{LOG_PREFIX} ✗ Erro em config/companies.yaml: {e}")
            return

    output_dir = Path("data/raw")
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%H%M%S")
    output_path = output_dir / f"{args.date}_{timestamp}.json"

    try:
        config = load_config()
    except Exception as e:
        print(f"{LOG_PREFIX} ✗ Erro ao carregar config: {e}")
        return

    search_config = config.get("search", {})
    roles = search_config.get("roles", ["Product Manager"])
    locations = search_config.get("locations", ["remote"])
    lookback_hours = search_config.get("lookback_hours", 24)

    if args.dry_run:
        print(f"{LOG_PREFIX} 🧪 MODO DRY-RUN")
        print(f"  Roles: {roles}")
        print(f"  Locations: {locations}")
        print(f"  Coletores: openai_web_search, remotive, weworkremotely, jobicy")
        try:
            companies_data = load_companies()
            n_sectors = len(companies_data["companies"])
            n_companies = sum(len(entries) for entries in companies_data["companies"].values())
            print(f"  Empresas-alvo (3.1): {n_companies} em {n_sectors} setores (config/companies.yaml)")
        except Exception:
            pass  # opcional; não falha dry-run se companies.yaml ausente
        print(f"  Saída: {output_path}")
        return

    collectors_config: list[tuple[str, Any]] = []

    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        client = OpenAI(api_key=api_key)

        def _openai_collector():
            return collect_openai_web_search(client, roles, locations, lookback_hours)

        collectors_config.append(("openai_web_search", _openai_collector))
    else:
        print(f"{LOG_PREFIX} ! OPENAI_API_KEY não definida; coletor openai_web_search omitido.")

    collectors_config.append(("remotive", collect_remotive))
    collectors_config.append(("weworkremotely", collect_weworkremotely))
    collectors_config.append(("jobicy", collect_jobicy))

    if not collectors_config:
        print(f"{LOG_PREFIX} ✗ Nenhum coletor disponível. Abortando.")
        return

    print(f"{LOG_PREFIX} 🚀 Pipeline multi-fonte para {args.date}...")
    jobs = run_pipeline(collectors_config)
    total_raw = len(jobs)

    if jobs:
        jobs = filter_old_jobs(jobs)
    total_after_recent_filter = len(jobs)

    if jobs:
        jobs = remove_duplicates(jobs, output_dir)
    total_after_dedup = len(jobs)

    jobs, discarded = apply_quality_guard(jobs)
    total_after_quality_guard = len(jobs)
    discarded_low_quality = len(discarded)

    if discarded:
        discarded_path = output_dir / f"{args.date}_{timestamp}_discarded.json"
        by_reason: dict[str, int] = {}
        for item in discarded:
            r = item.get("discard_reason", "unknown")
            by_reason[r] = by_reason.get(r, 0) + 1
        with open(discarded_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "date": args.date,
                    "discarded_at": datetime.now(timezone.utc).isoformat(),
                    "total": len(discarded),
                    "by_reason": by_reason,
                    "items": discarded,
                },
                f,
                ensure_ascii=False,
                indent=2,
            )
        parts = [f"{v} {k}" for k, v in sorted(by_reason.items())]
        print(f"{LOG_PREFIX} 🛡️ Quality guard: {len(discarded)} descartados ({', '.join(parts)}). Log em {discarded_path}")

    companies_distinct = len(
        {s for s in ((j.get("company") or "").strip() for j in jobs) if s}
    )
    coverage = {
        "sources": [name for name, _ in collectors_config],
        "total_raw": total_raw,
        "total_after_recent_filter": total_after_recent_filter,
        "total_after_dedup": total_after_dedup,
        "total_after_quality_guard": total_after_quality_guard,
        "companies_distinct": companies_distinct,
        "discarded_low_quality": discarded_low_quality,
    }

    output_data = {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "date": args.date,
        "config_used": {
            "roles": roles,
            "locations": locations,
            "lookback_hours": lookback_hours,
            "sources": [name for name, _ in collectors_config],
        },
        "coverage": coverage,
        "total_jobs": len(jobs),
        "jobs": jobs,
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print(f"{LOG_PREFIX} ✅ Sucesso! {len(jobs)} vagas salvas em {output_path}")


if __name__ == "__main__":
    main()
