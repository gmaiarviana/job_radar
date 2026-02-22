"""
Job Radar — Fetch & Filter (v1)
Busca vagas de Remotive + Arbeitnow (grátis, sem API key).
Filtra últimas 24h, remote, categorias relevantes.
Salva JSON limpo para análise.

Uso: python fetch_jobs.py
Saída: jobs_YYYY-MM-DD.json
"""

import json
import urllib.request
import urllib.error
from datetime import datetime, timedelta, timezone

# ── Config ──────────────────────────────────────────────
HOURS_LOOKBACK = 48  # 48h para primeira rodada (ter mais dados), depois reduz pra 24
OUTPUT_FILE = f"jobs_{datetime.now().strftime('%Y-%m-%d')}.json"

# ── Fetch Remotive ──────────────────────────────────────
def fetch_remotive():
    """Busca vagas das categorias product + project-management"""
    categories = ["product", "project-management"]
    all_jobs = []

    for cat in categories:
        url = f"https://remotive.com/api/remote-jobs?category={cat}&limit=50"
        print(f"  Fetching Remotive [{cat}]...")
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "JobRadar/1.0"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode())
                jobs = data.get("jobs", [])
                print(f"    → {len(jobs)} vagas retornadas")
                for j in jobs:
                    all_jobs.append({
                        "source": "remotive",
                        "title": j.get("title", ""),
                        "company": j.get("company_name", ""),
                        "salary": j.get("salary", ""),
                        "location": j.get("candidate_required_location", ""),
                        "job_type": j.get("job_type", ""),
                        "date": j.get("publication_date", ""),
                        "url": j.get("url", ""),
                        "description": strip_html(j.get("description", ""))[:1500],
                    })
        except Exception as e:
            print(f"    ✗ Erro: {e}")

    return all_jobs


# ── Fetch Arbeitnow ─────────────────────────────────────
def fetch_arbeitnow():
    """Busca vagas remote da Arbeitnow"""
    url = "https://www.arbeitnow.com/api/job-board-api?remote=true"
    print(f"  Fetching Arbeitnow [remote]...")
    all_jobs = []

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "JobRadar/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
            jobs = data.get("data", [])
            print(f"    → {len(jobs)} vagas retornadas (total, antes de filtro)")

            # Filtro por keywords relevantes no título
            keywords = [
                "product manager", "program manager", "project manager",
                "product owner", "delivery manager", "scrum master",
                "technical program", "tpm", "agile lead",
            ]
            for j in jobs:
                title_lower = j.get("title", "").lower()
                if any(kw in title_lower for kw in keywords):
                    all_jobs.append({
                        "source": "arbeitnow",
                        "title": j.get("title", ""),
                        "company": j.get("company_name", ""),
                        "salary": "",  # arbeitnow nem sempre tem
                        "location": j.get("location", ""),
                        "job_type": "full_time" if not j.get("job_types") else ",".join(j.get("job_types", [])),
                        "date": j.get("created_at", ""),
                        "url": j.get("url", ""),
                        "description": strip_html(j.get("description", ""))[:1500],
                    })
            print(f"    → {len(all_jobs)} vagas após filtro de keywords")

    except Exception as e:
        print(f"    ✗ Erro: {e}")

    return all_jobs


# ── Helpers ──────────────────────────────────────────────
def strip_html(text):
    """Remove tags HTML de forma simples"""
    import re
    clean = re.sub(r"<[^>]+>", " ", text)
    clean = re.sub(r"\s+", " ", clean).strip()
    return clean


def is_recent(date_str, hours=HOURS_LOOKBACK):
    """Checa se a data está dentro do lookback"""
    if not date_str:
        return True  # se não tem data, inclui (melhor sobrar que faltar)
    try:
        # Remotive: "2026-02-17T14:23:26"
        # Arbeitnow: timestamp int
        if isinstance(date_str, (int, float)):
            dt = datetime.fromtimestamp(date_str, tz=timezone.utc)
        else:
            # tenta ISO format
            date_str_clean = date_str.replace("Z", "+00:00")
            if "+" not in date_str_clean and "T" in date_str_clean:
                date_str_clean += "+00:00"
            dt = datetime.fromisoformat(date_str_clean)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        return dt >= cutoff
    except Exception:
        return True  # na dúvida, inclui


def deduplicate(jobs):
    """Deduplica por título+empresa (case insensitive)"""
    seen = set()
    unique = []
    for j in jobs:
        key = (j["title"].lower().strip(), j["company"].lower().strip())
        if key not in seen:
            seen.add(key)
            unique.append(j)
    return unique


# ── Main ─────────────────────────────────────────────────
def main():
    print("=" * 50)
    print("Job Radar — Fetch & Filter v1")
    print("=" * 50)

    # Fetch
    print("\n📡 Buscando vagas...")
    remotive_jobs = fetch_remotive()
    arbeitnow_jobs = fetch_arbeitnow()

    all_jobs = remotive_jobs + arbeitnow_jobs
    print(f"\n📦 Total bruto: {len(all_jobs)} vagas")

    # Filter recent
    recent = [j for j in all_jobs if is_recent(j["date"])]
    print(f"⏰ Últimas {HOURS_LOOKBACK}h: {len(recent)} vagas")

    # Deduplicate
    unique = deduplicate(recent)
    print(f"🧹 Após dedup: {len(unique)} vagas")

    # Sort by date (newest first)
    unique.sort(key=lambda x: x["date"] or "", reverse=True)

    # Save
    output = {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "sources": ["remotive", "arbeitnow"],
        "total_jobs": len(unique),
        "jobs": unique,
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Salvo em: {OUTPUT_FILE}")
    print(f"   {len(unique)} vagas prontas para análise")

    # Preview
    print("\n── Preview (top 10) ──")
    for i, j in enumerate(unique[:10], 1):
        salary_info = f" | {j['salary']}" if j["salary"] else ""
        print(f"  {i}. [{j['source']}] {j['title']} @ {j['company']}{salary_info}")

    print(f"\n💡 Próximo passo: cole o conteúdo de {OUTPUT_FILE} no chat para análise de fit.")


if __name__ == "__main__":
    main()