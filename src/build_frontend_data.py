"""
build_frontend_data.py — Consolida data/scored/ em data/jobs.json para o pipeline.
O workflow copia data/jobs.json → docs/data/jobs.json para o GitHub Pages servir.

Épico 8.1 | CLI: python src/build_frontend_data.py

Lógica de leitura replica app.py::_load_scored_jobs e _date_from_filename.
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Garante projeto na path ao rodar como python src/build_frontend_data.py
if __name__ == "__main__":
    _root = Path(__file__).resolve().parent.parent
    if str(_root) not in sys.path:
        sys.path.insert(0, str(_root))

from src.paths import FILTERED_DIR, SCORED_DIR

OUTPUT_DIR = Path("data")
OUTPUT_FILE = OUTPUT_DIR / "jobs.json"
DAYS_WINDOW = 14


def _date_from_filename(name: str) -> str | None:
    """Extrai YYYY-MM-DD do nome do arquivo. Trata prefixo manual_."""
    base = name.replace(".json", "")
    if base.startswith("manual_"):
        base = base[7:]
    match = re.match(r"(\d{4}-\d{2}-\d{2})", base)
    return match.group(1) if match else None


def _load_scored_jobs() -> list[dict]:
    """
    Lê todos os .json de data/scored/ (exceto *_discarded.json e seed_*).
    Retorna lista de jobs com file_date e source.
    """
    if not SCORED_DIR.exists():
        return []

    rows: list[dict] = []
    for path in SCORED_DIR.glob("*.json"):
        name = path.name
        if "_discarded" in name or name.startswith("seed_"):
            continue
        file_date = _date_from_filename(name)
        source = "linkedin" if name.startswith("manual_") else "pipeline"

        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue

        job_list = data.get("jobs") or data.get("scored_jobs") or []
        for job in job_list:
            if isinstance(job, dict):
                job_entry = dict(job)
                job_entry["file_date"] = file_date or ""
                job_entry["source"] = job.get("source", source)
                rows.append(job_entry)
    return rows


def _filter_recent(jobs: list[dict], days: int = DAYS_WINDOW) -> list[dict]:
    """Mantém apenas jobs com file_date nos últimos N dias."""
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")
    return [j for j in jobs if j.get("file_date", "") >= cutoff]


def _load_pipeline_runs() -> list[dict]:
    """Lê data/filtered/ e retorna resumo de cada run do pipeline."""
    if not FILTERED_DIR.exists():
        return []

    runs: list[dict] = []
    for path in sorted(FILTERED_DIR.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue

        summary = data.get("summary") or {}
        filtered_at = data.get("filtered_at") or ""
        source = data.get("source_file", "")
        file_date = _date_from_filename(source)
        if not file_date:
            continue

        runs.append(
            {
                "date": file_date,
                "filtered_at": filtered_at,
                "total_input": summary.get("total_input", 0),
                "total_passed": summary.get("total_passed", 0),
                "discarded_title": summary.get("discarded_title", 0),
                "discarded_blocklist": summary.get("discarded_blocklist", 0),
                "discarded_location": summary.get("discarded_location", 0),
                "discarded_quality": summary.get("discarded_quality", 0),
            }
        )
    return runs


def _filter_recent_runs(runs: list[dict], days: int = DAYS_WINDOW) -> list[dict]:
    """Mantém apenas runs com date nos últimos N dias."""
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")
    return [r for r in runs if r.get("date", "") >= cutoff]


def _sort_jobs(jobs: list[dict]) -> list[dict]:
    """Ordena por file_date desc, depois por score desc."""
    return sorted(
        jobs,
        key=lambda j: (j.get("file_date", ""), j.get("score") or 0),
        reverse=True,
    )


def main() -> None:
    jobs = _load_scored_jobs()
    jobs = _filter_recent(jobs)
    jobs = _sort_jobs(jobs)
    runs = _load_pipeline_runs()
    runs = _filter_recent_runs(runs)

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total": len(jobs),
        "jobs": jobs,
        "pipeline_runs": runs,
    }

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"[build] OK — {len(jobs)} jobs → {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
