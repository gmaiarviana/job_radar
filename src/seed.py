"""
seed.py — Seed inicial: popula seen_jobs com o histórico de uma ou mais fontes ATS (Épico 3.5).

Roda os coletores indicados, grava o bruto em RAW_DIR/seed_YYYY-MM-DD_HHMMSS.json
e marca todas as vagas em seen_jobs (sem throttle, sem filtro de 7 dias).

Uso recomendado (uma fonte por vez, revisar entre runs):
  python src/seed.py --source greenhouse
  python src/seed.py --source lever
  python src/seed.py --source ashby
Ou de uma vez: python src/seed.py --source all
Dry-run: python src/seed.py --source greenhouse --dry-run
"""

import sys
import io
import json
import argparse
from datetime import date, datetime
from pathlib import Path
from typing import Any

# Console Windows: evita UnicodeEncodeError em emojis dos logs
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

if __name__ == "__main__":
    _root = Path(__file__).resolve().parent.parent
    if str(_root) not in sys.path:
        sys.path.insert(0, str(_root))

from src.fetch_pipeline import load_companies, run_pipeline
from src.fetch_pipeline import get_companies_by_ats
from src.job_schema import normalize_job
from src.seen_jobs import load_seen, mark_seen, save_seen
from src.collectors.greenhouse import collect_greenhouse
from src.collectors.lever import collect_lever
from src.collectors.ashby import collect_ashby
from src.paths import RAW_DIR, ensure_dirs

LOG_PREFIX = "[seed]"

SOURCE_CHOICES = ("greenhouse", "lever", "ashby", "all")


def _mock_jobs_for_test(source: str) -> list[dict]:
    """Retorna 2 jobs normalizados fake para teste sem rede."""
    raw = [
        {"id": "mock-1", "title": "PM Test A", "company": "Company A", "url": "https://example.com/1"},
        {"id": "mock-2", "title": "PM Test B", "company": "Company B", "url": "https://example.com/2"},
    ]
    return [normalize_job(r, source) for r in raw]


def _build_ats_collectors(
    source: str,
    greenhouse_companies: list,
    lever_companies: list,
    ashby_companies: list,
) -> list[tuple[str, Any]]:
    """Monta lista (source_name, collector_fn) apenas para a(s) fonte(s) pedida(s)."""
    collectors: list[tuple[str, Any]] = []
    if source in ("greenhouse", "all") and greenhouse_companies:
        collectors.append(("greenhouse", lambda: collect_greenhouse(greenhouse_companies)))
    if source in ("lever", "all") and lever_companies:
        collectors.append(("lever", lambda: collect_lever(lever_companies)))
    if source in ("ashby", "all") and ashby_companies:
        collectors.append(("ashby", lambda: collect_ashby(ashby_companies)))
    return collectors


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Seed inicial: popula seen_jobs com histórico ATS (Épico 3.5)"
    )
    parser.add_argument(
        "--source",
        choices=SOURCE_CHOICES,
        required=True,
        help="Fonte(s) a coletar: greenhouse, lever, ashby ou all",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Apenas lista fontes e quantidade de vagas; não grava JSON nem atualiza seen_jobs",
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Modo teste: usa 2 vagas fake (sem rede); grava seed_test_*.json e atualiza seen_jobs",
    )
    args = parser.parse_args()

    if args.test:
        _run_test_mode(args)
        return

    try:
        companies_data = load_companies()
        by_ats = get_companies_by_ats(companies_data)
        greenhouse_companies = by_ats["greenhouse"]
        lever_companies = by_ats["lever"]
        ashby_companies = by_ats["ashby"]
    except Exception as e:
        print(f"{LOG_PREFIX} ✗ Erro ao carregar config/companies.yaml: {e}")
        return

    collectors_config = _build_ats_collectors(
        args.source, greenhouse_companies, lever_companies, ashby_companies
    )
    if not collectors_config:
        print(f"{LOG_PREFIX} ✗ Nenhuma empresa configurada para a(s) fonte(s): {args.source}")
        if args.source == "all":
            print(f"  Greenhouse: {len(greenhouse_companies)}, Lever: {len(lever_companies)}, Ashby: {len(ashby_companies)}")
        return

    ensure_dirs()
    output_dir = RAW_DIR
    today = date.today().isoformat()
    timestamp = datetime.now().strftime("%H%M%S")
    output_path = output_dir / f"seed_{today}_{timestamp}.json"

    print(f"{LOG_PREFIX} Coletores: {[n for n, _ in collectors_config]}")
    if args.dry_run:
        print(f"{LOG_PREFIX} 🧪 DRY-RUN (sem rede): não executa coletores")
        print(
            f"  Empresas configuradas | Greenhouse: {len(greenhouse_companies)} | Lever: {len(lever_companies)} | Ashby: {len(ashby_companies)}"
        )
        return

    jobs = run_pipeline(collectors_config)
    total = len(jobs)

    # Gravar bruto no mesmo formato do fetch
    coverage = {
        "sources": [name for name, _ in collectors_config],
        "total_raw": total,
    }
    output_data = {
        "fetched_at": datetime.now().astimezone().isoformat(),
        "date": today,
        "config_used": {"seed_source": args.source, "sources": coverage["sources"]},
        "coverage": coverage,
        "total_jobs": total,
        "jobs": jobs,
    }
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    # Marcar todas como vistas em seen_jobs
    seen = load_seen()
    for job in jobs:
        mark_seen(
            job.get("id_hash") or "",
            job.get("source") or "",
            job.get("title") or "",
            job.get("company") or "",
            seen,
        )
    save_seen(seen)

    print(f"{LOG_PREFIX} ✅ {total} vagas salvas em {output_path} e marcadas em seen_jobs")


def _run_test_mode(args: argparse.Namespace) -> None:
    """Modo teste: jobs mock, grava seed_test_*.json e marca em seen_jobs."""
    source = args.source if args.source != "all" else "greenhouse"
    jobs = _mock_jobs_for_test(source)
    ensure_dirs()
    output_dir = RAW_DIR
    today = date.today().isoformat()
    timestamp = datetime.now().strftime("%H%M%S")
    output_path = output_dir / f"seed_test_{today}_{timestamp}.json"

    if args.dry_run:
        print(f"{LOG_PREFIX} 🧪 DRY-RUN (test): {len(jobs)} vagas mock seriam processadas")
        print(f"  Saída: {output_path}")
        return

    coverage = {"sources": [source], "total_raw": len(jobs)}
    output_data = {
        "fetched_at": datetime.now().astimezone().isoformat(),
        "date": today,
        "config_used": {"seed_source": args.source, "test": True, "sources": [source]},
        "coverage": coverage,
        "total_jobs": len(jobs),
        "jobs": jobs,
    }
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    seen = load_seen()
    for job in jobs:
        mark_seen(
            job.get("id_hash") or "",
            job.get("source") or "",
            job.get("title") or "",
            job.get("company") or "",
            seen,
        )
    save_seen(seen)
    print(f"{LOG_PREFIX} ✅ [TEST] {len(jobs)} vagas mock em {output_path} e marcadas em seen_jobs")


if __name__ == "__main__":
    main()
