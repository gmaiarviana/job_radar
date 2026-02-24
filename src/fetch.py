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

from src.fetch_pipeline import load_config, run_pipeline, remove_duplicates, filter_old_jobs
from src.collectors.remotive import collect_remotive
from src.collectors.openai_search import collect_openai_web_search
from src.collectors.weworkremotely import collect_weworkremotely

load_dotenv()

LOG_PREFIX = "[fetch]"


def main():
    parser = argparse.ArgumentParser(
        description="Pipeline multi-fonte de coleta de vagas (Épico 2.1/2.2)"
    )
    parser.add_argument("--date", default=str(date.today()), help="Data no formato YYYY-MM-DD")
    parser.add_argument("--dry-run", action="store_true", help="Apenas mostra o que seria buscado")
    args = parser.parse_args()

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
        print(f"  Coletores: openai_web_search, remotive, weworkremotely")
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

    if not collectors_config:
        print(f"{LOG_PREFIX} ✗ Nenhum coletor disponível. Abortando.")
        return

    print(f"{LOG_PREFIX} 🚀 Pipeline multi-fonte para {args.date}...")
    jobs = run_pipeline(collectors_config)
    if jobs:
        jobs = filter_old_jobs(jobs)
        jobs = remove_duplicates(jobs, output_dir)

    output_data = {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "date": args.date,
        "config_used": {
            "roles": roles,
            "locations": locations,
            "lookback_hours": lookback_hours,
            "sources": [name for name, _ in collectors_config],
        },
        "total_jobs": len(jobs),
        "jobs": jobs,
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print(f"{LOG_PREFIX} ✅ Sucesso! {len(jobs)} vagas salvas em {output_path}")


if __name__ == "__main__":
    main()
