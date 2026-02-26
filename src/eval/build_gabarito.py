"""
Build machine-readable gabarito for filter/elimination evaluation (PROMPT 8 — 4.3.1).

Uses make_id_hash(company, title) from job_schema; outputs data/eval/gabarito_seed_2026-02-24.json.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from src.job_schema import make_id_hash

# ---------------------------------------------------------------------------
# Lista 1 — Principal/Staff/VP/Director/Head of (reason: "title")
# ---------------------------------------------------------------------------
LIST_1_TITLE: list[tuple[str, str]] = [
    ("Principal Product Manager, AI Control Plane and Guardrails", "GitLab"),
    ("Principal Product Manager, Security & Compliance", "GitLab"),
    ("Staff Product Manager, AI Developer Tools", "GitLab"),
    ("Staff Product Manager, Software Supply Chain Security", "GitLab"),
    ("Principal Product Manager", "Samsara"),
    ("Senior/Principal Product Manager - Safety AI", "Samsara"),
    ("Staff Product Manager", "Brex"),
    ("Principal Marketing Program Manager", "Samsara"),
    ("Principal Product Manager - Platform", "Samsara"),
    ("Principal Product Manager, Reporting Platform", "Samsara"),
    ("Sr. Staff Technical Program Manager - GenAI", "Databricks"),
    ("Sr. Staff Technical Program Manager - Reliability", "Databricks"),
    ("Staff Product Manager", "Databricks"),
    ("Staff Product Manager, AI Platform", "Databricks"),
    ("Staff Product Manager, Content Experience", "Databricks"),
    ("Staff Product Manager, Databricks Notebooks", "Databricks"),
    ("Staff Product Manager, Security", "Databricks"),
    ("Staff Product Manager, Serverless Workspaces", "Databricks"),
    ("Staff Product Manager - Technical", "Databricks"),
    ("Staff Project Manager (TPM)", "Databricks"),
    ("Staff Technical Program Manager - CPQ", "Databricks"),
    ("Staff Technical Program Manager – GenAI Ops", "Databricks"),
    ("Staff Technical Program Manager, Streaming", "Databricks"),
    ("Staff Product Manager - AI Discovery", "Faire"),
    ("Staff Product Manager - Brand", "Faire"),
    ("Staff Product Manager - FinTech & Ops", "Faire"),
    ("Staff Product Manager - Search Algorithms", "Faire"),
    ("Staff Product Manager", "Duolingo"),
    ("Staff Technical Program Manager", "Duolingo"),
    ("Staff Product Manager, Agentic Platform", "Scale AI"),
]

# ---------------------------------------------------------------------------
# Lista 2 — US-only / restrição geográfica (reason: "location"), excl. já em Lista 1
# ---------------------------------------------------------------------------
LIST_2_LOCATION: list[tuple[str, str]] = [
    ("Senior Technical Program Manager, Infrastructure", "Planet Labs"),
    ("AI Self-Service Program Manager", "Samsara"),
    ("Program Manager II - Customer Success", "Samsara"),
    ("Education & Research PM & Evangelist", "Planet Labs"),
    ("Senior Product Manager, Crypto Brokerage", "Paxos"),
    ("Senior Product Manager, Custody & Blockchain", "Paxos"),
    ("Sr. Product Manager, Ads AI/ML", "Disney"),
    ("Product Manager, LATAM", "Airbnb"),
    ("Senior Enablement PM, AI Transformation", "Databricks"),
    ("Customer Education Program Manager", "Klaviyo"),
    ("Lead Product Manager", "Klaviyo"),
    ("Program Manager, Business Transformation", "Amplitude"),
    ("Product Manager - Accounts", "Vercel"),
]

# Vagas que aparecem nas duas listas → reason "both"
IN_BOTH: set[tuple[str, str]] = {
    ("Principal Product Manager, AI Control Plane and Guardrails", "GitLab"),
    ("Staff Product Manager, AI Developer Tools", "GitLab"),
}


def _build_entries() -> list[dict]:
    seen_hash: dict[str, dict] = {}  # id_hash -> entry (evita duplicata)

    for title, company in LIST_1_TITLE:
        reason = "both" if (title, company) in IN_BOTH else "title"
        id_hash = make_id_hash(company, title)
        entry = {
            "id_hash": id_hash,
            "title": title,
            "company": company,
            "expected_action": "eliminate",
            "reason": reason,
        }
        seen_hash[id_hash] = entry

    for title, company in LIST_2_LOCATION:
        id_hash = make_id_hash(company, title)
        if id_hash in seen_hash:
            continue  # já coberto por Lista 1 (ex.: "both")
        seen_hash[id_hash] = {
            "id_hash": id_hash,
            "title": title,
            "company": company,
            "expected_action": "eliminate",
            "reason": "location",
        }

    return list(seen_hash.values())


def _check_seed_coverage(entries: list[dict], repo_root: Path) -> None:
    raw_dir = repo_root / "data" / "raw"
    if not raw_dir.is_dir():
        return
    seed_files = list(raw_dir.glob("seed_2026-02-24_*.json"))
    if not seed_files:
        return
    seed_hashes: set[str] = set()
    for path in seed_files:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            for job in data.get("jobs", []):
                h = job.get("id_hash")
                if h:
                    seed_hashes.add(h)
        except (json.JSONDecodeError, OSError):
            continue
    missing = [e for e in entries if e["id_hash"] not in seed_hashes]
    if missing:
        print(f"Warning: {len(missing)} gabarito entries have no match in data/raw/seed_2026-02-24_*.json")
        for e in missing[:5]:
            print(f"  - {e['title']} @ {e['company']}")
        if len(missing) > 5:
            print(f"  ... and {len(missing) - 5} more.")


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    entries = _build_entries()

    # Deduplica por id_hash (já feito em _build_entries)
    total = len(entries)
    if total != 42:
        print(f"Total de entradas após dedup: {total} (referência 42; diferença por dedup por id_hash ou contagem das listas).")

    by_reason: dict[str, int] = {}
    for e in entries:
        r = e["reason"]
        by_reason[r] = by_reason.get(r, 0) + 1

    out = {
        "description": "Gabarito de eliminação — 42 vagas que devem ser descartadas (título ou localização)",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "total": total,
        "entries": entries,
    }

    out_path = repo_root / "data" / "eval" / "gabarito_seed_2026-02-24.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Wrote {out_path}")
    print(f"Total: {total}")
    print("Por reason:", by_reason)

    _check_seed_coverage(entries, repo_root)


if __name__ == "__main__":
    main()
