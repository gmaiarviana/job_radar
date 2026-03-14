"""
Diagnóstico sob demanda dos coletores Remote OK + Get on Board.

- Sem efeitos colaterais: não salva em data/, não atualiza seen_jobs.
- Output: console, com seções claras e tabelas.

Uso:
  python src/eval/diagnose_collectors.py
  python src/eval/diagnose_collectors.py --source remoteok
  python src/eval/diagnose_collectors.py --source getonboard
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

# Permite rodar como: python src/eval/diagnose_collectors.py
if __name__ == "__main__":
    _root = Path(__file__).resolve().parents[2]  # .../job_radar
    if str(_root) not in sys.path:
        sys.path.insert(0, str(_root))

from src.collectors import (
    TITLE_KEYWORDS,
    TITLE_KEYWORDS_LATAM,
    getonboard as getonboard_collector,
    remoteok as remoteok_collector,
    remotive as remotive_collector,
)

LOG_PREFIX = "[diagnose]"


def _http_get_json(url: str, headers: dict[str, str] | None = None, timeout_s: int = 30) -> tuple[int | None, Any]:
    """
    GET JSON com urllib, retornando (status_http, payload).
    Em caso de erro HTTP, tenta ler body para ajudar no diagnóstico.
    """
    try:
        req = Request(url, headers=headers or {})
        with urlopen(req, timeout=timeout_s) as resp:
            status = getattr(resp, "status", None)
            body = resp.read().decode("utf-8", errors="replace")
            return status, json.loads(body)
    except HTTPError as e:
        try:
            body = e.read().decode("utf-8", errors="replace")
        except Exception:
            body = ""
        payload: Any = {"_error": "HTTPError", "code": e.code, "reason": str(e.reason), "body": body[:2000]}
        return e.code, payload
    except (URLError, OSError, json.JSONDecodeError) as e:
        return None, {"_error": type(e).__name__, "detail": str(e)}


def _remoteok_match_reason(job: dict) -> tuple[str, bool, bool]:
    """
    Retorna (match_reason, matched_by_tag, matched_by_position_keyword).
    match_reason segue o spec: tag:{tag} | position:{keyword} | NONE
    """
    # Para diagnóstico, ainda inspecionamos tags comuns de Remote OK
    remoteok_tags_for_diag = {"product", "management", "exec"}

    tags = job.get("tags") or []
    if isinstance(tags, str):
        tags_list = [t.strip().lower() for t in tags.split(",") if t.strip()]
    else:
        tags_list = [str(t).strip().lower() for t in tags]

    tag_set = set(tags_list)
    tag_hit = sorted(tag_set & remoteok_tags_for_diag)
    if tag_hit:
        return f"tag:{tag_hit[0]}", True, False

    position = (job.get("position") or "").lower()
    for kw in TITLE_KEYWORDS:
        if kw in position:
            return f"position:{kw}", False, True
    return "NONE", False, False


def _print_table(rows: list[list[str]], headers: list[str]) -> None:
    if not rows:
        print(f"{LOG_PREFIX} (nenhuma linha)")
        return
    widths = [len(h) for h in headers]
    for r in rows:
        for i, cell in enumerate(r):
            widths[i] = max(widths[i], len(cell))

    def _fmt_row(r: list[str]) -> str:
        return " | ".join((r[i] if i < len(r) else "").ljust(widths[i]) for i in range(len(headers)))

    print(_fmt_row(headers))
    print("-+-".join("-" * w for w in widths))
    for r in rows:
        print(_fmt_row(r))


def diagnose_remoteok() -> None:
    print("\n" + "=" * 80)
    print("REMOTE OK — Diagnóstico")
    print("=" * 80)

    now_local = datetime.now().astimezone()
    cutoff = now_local - timedelta(hours=remoteok_collector.REMOTEOK_RECENT_HOURS)

    status, data = _http_get_json(
        remoteok_collector.REMOTEOK_API_URL,
        headers={"User-Agent": remoteok_collector.REMOTEOK_USER_AGENT},
    )
    print(f"{LOG_PREFIX} GET {remoteok_collector.REMOTEOK_API_URL} -> HTTP {status}")

    if not isinstance(data, list):
        print(f"{LOG_PREFIX} Resposta não é list. Tipo={type(data).__name__}")
        print(f"{LOG_PREFIX} Payload (truncado): {str(data)[:2000]}")
        return

    if not data:
        print(f"{LOG_PREFIX} Lista vazia.")
        return

    # Item 0 é metadata (ignorar)
    jobs = data[1:] if len(data) > 1 else []

    total_recent = 0
    total_passed = 0
    passed_by_tag_but_not_position = 0
    suspicious_examples: list[str] = []

    rows: list[list[str]] = []
    for j in jobs:
        if not isinstance(j, dict):
            continue

        pub_dt = remoteok_collector._parse_remoteok_date(j.get("date"))  # type: ignore[attr-defined]
        if pub_dt is None:
            continue
        pub_local = pub_dt.astimezone()
        if pub_local < cutoff:
            continue
        total_recent += 1

        match_reason, matched_by_tag, matched_by_position_kw = _remoteok_match_reason(j)
        passed = bool(remoteok_collector._matches_filter(j))  # type: ignore[attr-defined]
        if passed:
            total_passed += 1
            if matched_by_tag and not matched_by_position_kw:
                passed_by_tag_but_not_position += 1
                if len(suspicious_examples) < 5:
                    suspicious_examples.append(f"{j.get('company','')} — {j.get('position','')}")

        tags = j.get("tags") or []
        if isinstance(tags, list):
            tags_str = ", ".join(str(t) for t in tags)
        else:
            tags_str = str(tags)

        rows.append(
            [
                str(j.get("position") or ""),
                str(j.get("company") or ""),
                tags_str,
                match_reason,
                str(passed),
            ]
        )

    print(f"{LOG_PREFIX} Cutoff: {cutoff.isoformat()} (últimas {remoteok_collector.REMOTEOK_RECENT_HOURS}h)")
    _print_table(
        rows,
        headers=["position", "company", "tags", "match_reason", "passed_filter"],
    )

    print("\n" + "-" * 80)
    print("Resumo")
    print("-" * 80)
    print(f"{LOG_PREFIX} Total recentes ({remoteok_collector.REMOTEOK_RECENT_HOURS}h): {total_recent}")
    print(f"{LOG_PREFIX} Total que passaram no filtro: {total_passed}")
    print(f"{LOG_PREFIX} Passaram por TAG mas não por título (suspeitas): {passed_by_tag_but_not_position}")
    if suspicious_examples:
        print(f"{LOG_PREFIX} Exemplos suspeitos (até 5):")
        for ex in suspicious_examples:
            print(f"  - {ex}")


def diagnose_remotive() -> None:
    print("\n" + "=" * 80)
    print("REMOTIVE — Diagnóstico")
    print("=" * 80)

    now_local = datetime.now().astimezone()
    cutoff = now_local - timedelta(hours=remotive_collector.REMOTIVE_RECENT_HOURS)

    categories = ["product", "project-management"]
    for category in categories:
        url = f"{remotive_collector.REMOTIVE_BASE_URL}?category={category}&limit=10"
        status, payload = _http_get_json(url, headers={"User-Agent": "JobRadar/1.0"})
        print(f"{LOG_PREFIX} GET {url} -> HTTP {status}")

        if not isinstance(payload, dict):
            print(f"{LOG_PREFIX} Resposta não é dict para categoria {category}. Tipo={type(payload).__name__}")
            continue

        jobs = payload.get("jobs") or []
        if not isinstance(jobs, list):
            print(f"{LOG_PREFIX} payload['jobs'] não é list (tipo={type(jobs).__name__}).")
            continue

        total = len(jobs)
        recent = 0
        latest_dt = None
        latest_raw = ""
        rows: list[list[str]] = []

        for j in jobs:
            if not isinstance(j, dict):
                continue
            pub_raw = j.get("publication_date")
            pub_dt = remotive_collector._parse_remotive_date(pub_raw)  # type: ignore[attr-defined]
            if pub_dt is not None:
                if latest_dt is None or pub_dt > latest_dt:
                    latest_dt = pub_dt
                    latest_raw = str(pub_raw)
                pub_local = pub_dt.astimezone()
                is_recent = pub_local >= cutoff
            else:
                is_recent = False

            if is_recent:
                recent += 1
                if len(rows) < 5:
                    rows.append(
                        [
                            str(j.get("title") or ""),
                            str(j.get("company_name") or ""),
                            str(pub_raw or ""),
                            pub_dt.isoformat() if pub_dt else "",
                            str(j.get("candidate_required_location") or ""),
                        ]
                    )

        print(f"{LOG_PREFIX} Categoria={category} | total jobs={total} | recentes({remotive_collector.REMOTIVE_RECENT_HOURS}h)={recent}")
        if rows:
            _print_table(
                rows,
                headers=["title", "company", "publication_date_raw", "publication_date_parsed", "candidate_required_location"],
            )
        if recent == 0 and latest_dt is not None:
            print(
                f"{LOG_PREFIX} Nenhuma vaga nas últimas {remotive_collector.REMOTIVE_RECENT_HOURS}h para categoria {category}. "
                f"Mais recente: {latest_raw} (parsed={latest_dt.isoformat()})"
            )


def _getonboard_extract_company_like_collector(item: dict) -> str:
    attrs = item.get("attributes") or {}
    # Diagnóstico segue a mesma lógica simplificada do coletor:
    return str((attrs.get("company") or ""))


def _getonboard_print_structure(data: dict) -> None:
    items = data.get("data") or []
    if not items:
        print(f"{LOG_PREFIX} data.data está vazio; nada para inspecionar.")
        return

    first = items[0]
    if not isinstance(first, dict):
        print(f"{LOG_PREFIX} data[0] não é dict (tipo={type(first).__name__}).")
        return

    print(f"{LOG_PREFIX} keys(data[0]): {sorted(first.keys())}")
    attrs = first.get("attributes") or {}
    if isinstance(attrs, dict):
        print(f"{LOG_PREFIX} keys(data[0].attributes): {sorted(attrs.keys())}")
    else:
        print(f"{LOG_PREFIX} data[0].attributes não é dict (tipo={type(attrs).__name__}).")

    company = first.get("company")
    if company is None:
        print(f"{LOG_PREFIX} data[0].company: (não existe)")
    elif isinstance(company, dict):
        print(f"{LOG_PREFIX} keys(data[0].company): {sorted(company.keys())}")
        if isinstance(company.get("data"), dict):
            print(f"{LOG_PREFIX} keys(data[0].company.data): {sorted(company['data'].keys())}")
    else:
        print(f"{LOG_PREFIX} data[0].company não é dict (tipo={type(company).__name__}).")


def diagnose_getonboard() -> None:
    print("\n" + "=" * 80)
    print("GET ON BOARD — Diagnóstico")
    print("=" * 80)

    page = 1
    total_pages = 1
    pages_fetched = 0
    all_items: list[dict] = []

    while page <= total_pages:
        params = {
            "query": "product manager",
            "remote": "true",
            "per_page": getonboard_collector.GETONBOARD_PER_PAGE,
            "page": page,
        }
        url = f"{getonboard_collector.GETONBOARD_BASE}?{urlencode(params)}"
        status, payload = _http_get_json(url, headers={"User-Agent": "JobRadar/1.0"})
        print(f"{LOG_PREFIX} GET {url} -> HTTP {status}")

        if not isinstance(payload, dict):
            print(f"{LOG_PREFIX} payload inesperado (tipo={type(payload).__name__}).")
            break

        if page == 1:
            meta = payload.get("meta") or {}
            if isinstance(meta, dict):
                print(f"{LOG_PREFIX} meta: { {k: meta.get(k) for k in sorted(meta.keys())} }")
                total_pages = int(meta.get("total_pages", 1) or 1)
                total_pages = min(total_pages, 5)
            else:
                print(f"{LOG_PREFIX} meta não é dict (tipo={type(meta).__name__}).")
                total_pages = 1

            _getonboard_print_structure(payload)

        items = payload.get("data") or []
        if not isinstance(items, list):
            print(f"{LOG_PREFIX} data não é list (tipo={type(items).__name__}).")
            break

        all_items.extend(items)
        pages_fetched += 1

        page += 1

    print(f"{LOG_PREFIX} Páginas lidas: {pages_fetched} (máx 5) | total items acumulados: {len(all_items)}")

    rows: list[list[str]] = []
    for item in all_items[:10]:
        if not isinstance(item, dict):
            continue
        attrs = item.get("attributes") or {}
        if not isinstance(attrs, dict):
            continue
        title = str(attrs.get("title") or "")
        company = _getonboard_extract_company_like_collector(item)
        pub_raw = attrs.get("published_at")
        pub_parsed = getonboard_collector._parse_published_at(pub_raw)  # type: ignore[attr-defined]
        remote = bool(attrs.get("remote"))
        passed_title = bool(getonboard_collector._matches_title(title))  # type: ignore[attr-defined]
        rows.append(
            [
                title,
                company,
                str(pub_raw),
                (pub_parsed.isoformat() if pub_parsed else ""),
                str(remote),
                str(passed_title),
            ]
        )

    print("\n" + "-" * 80)
    print("Amostra (até 10)")
    print("-" * 80)
    _print_table(rows, headers=["title", "company", "published_at_raw", "published_at_parsed", "remote", "passed_title_filter"])


def main() -> None:
    parser = argparse.ArgumentParser(description="Diagnóstico de coletores Remote OK + Get on Board (sem side effects)")
    parser.add_argument(
        "--source",
        default="all",
        choices=["all", "both", "remoteok", "getonboard", "remotive"],
        help="Qual fonte diagnosticar (default: all).",
    )
    args = parser.parse_args()

    if args.source in ("all", "both", "remoteok"):
        diagnose_remoteok()
    if args.source in ("all", "both", "getonboard"):
        diagnose_getonboard()
    if args.source in ("all", "both", "remotive"):
        diagnose_remotive()


if __name__ == "__main__":
    main()

