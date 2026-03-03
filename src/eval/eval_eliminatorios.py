"""
Avaliação dos eliminatórios contra gabarito (PROMPT 9 — 4.3.2).

Aplica hard filters + LLM eliminatórios ao seed, compara com o gabarito e gera relatório.
Modelo parametrizável via --model para comparar Haiku 3 vs 3.5.
"""

from __future__ import annotations

import json
import os
import re
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from anthropic import Anthropic

from src.fetch_pipeline import load_config
from src.filter import (
    apply_title_filter,
    apply_location_blocklist,
    apply_location_filter,
    apply_quality_guard,
)
from src.score import load_profile

load_dotenv()

# Prompt e parsing idênticos a score.check_eliminatorios; aqui o modelo é parametrizável
def _run_eliminatorios_llm(client: Anthropic, jobs: list[dict], profile_content: str, model: str) -> tuple[list[dict], list[dict]]:
    """Executa critérios eliminatórios via LLM com modelo informado. Retorna (passed, eliminated)."""
    if not jobs:
        return [], []

    reduced = []
    for j in jobs:
        jd_full = (j.get("jd_full") or j.get("description") or "")
        reduced.append({
            "title": j.get("title", ""),
            "company": j.get("company", ""),
            "location": j.get("location", ""),
            "jd_full": jd_full,
        })

    system_prompt = f"""
Você é um recrutador técnico. Analise a lista de vagas abaixo e verifique se atendem aos critérios eliminatórios do candidato.
Cada vaga inclui a descrição completa (jd_full) da posição para você avaliar.

# PERFIL DO CANDIDATO (CRITÉRIOS)
{profile_content}

# CRITÉRIOS ELIMINATÓRIOS:
1. Localização (LOCATION): O candidato é brasileiro, trabalha remotamente do Brasil, SEM autorização de trabalho em US, Canada, UK, EU ou Austrália.
   - ELIMINAR se a vaga exigir: residência, work authorization ou presença física em US, Canada, UK, EU, Austrália ou Israel.
   - PERMITIR se for: worldwide, global, LATAM, ou países onde brasileiro pode trabalhar remotamente (Brazil, Mexico, Colombia, Argentina, Chile, etc.).
   - PERMITIR se location estiver vazia ou ambígua — em caso de dúvida, beneficie o candidato.
2. Nível: Sênior, Staff, Principal ou Lead apenas. (Junior, Pleno, Mid, Estágio = ELIMINADO)
3. Tipo de Cargo: PM, TPM ou Híbrido PM/Tech. (Engenheiro puro, EM, Marketing puro = ELIMINADO)
4. Idioma: Vaga deve ser em Inglês (vagas apenas em PT ou ES = ELIMINADO)

# FORMATO DE SAÍDA (JSON)
Retorne APENAS um objeto JSON com:
- "results": lista de objetos contendo:
    - "title": título original
    - "status": "passa" ou "eliminada"
    - "reason": se eliminada, qual o motivo (localização, nível, tipo de cargo, idioma). Se passa, deixe vazio.

Responda APENAS o JSON.
"""

    user_content = "Avalie as seguintes vagas:\n" + json.dumps(reduced, indent=2, ensure_ascii=False)

    try:
        response = client.messages.create(
            model=model,
            max_tokens=4000,
            system=system_prompt,
            messages=[{"role": "user", "content": user_content}],
        )
        content = response.content[0].text
        start_idx = content.find("{")
        end_idx = content.rfind("}") + 1
        data = json.loads(content[start_idx:end_idx])
        results = data.get("results", [])

        passed = []
        eliminated = []
        job_map = {j["title"]: j for j in jobs}

        for res in results:
            title = res.get("title")
            job = job_map.get(title)
            if job:
                if res.get("status") == "passa":
                    passed.append(job)
                else:
                    job_copy = job.copy()
                    job_copy["filter_reason"] = res.get("reason", "eliminado LLM")
                    eliminated.append(job_copy)
        return passed, eliminated
    except Exception as e:
        print(f"[eval_eliminatorios] [ERR] Erro no LLM eliminatórios: {e}")
        return jobs, []


def _job_id_hash(job: dict) -> str:
    return (job.get("id_hash") or job.get("id") or "").strip()


def _model_slug(model: str) -> str:
    """Nome seguro para arquivo (substitui caracteres inválidos)."""
    return re.sub(r"[^\w\-.]", "_", model)


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(
        description="Avalia eliminatórios (hard filters + LLM) contra gabarito.",
    )
    parser.add_argument("--seed", required=True, metavar="path", help="JSON do seed (ex: data/raw/seed_2026-02-24_123007.json)")
    parser.add_argument("--gabarito", required=True, metavar="path", help="JSON do gabarito (ex: data/eval/gabarito_seed_2026-02-24.json)")
    parser.add_argument("--model", required=True, metavar="model", help="Modelo Anthropic (ex: claude-3-haiku-20240307)")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[2]
    seed_path = Path(args.seed)
    if not seed_path.is_absolute():
        seed_path = repo_root / seed_path
    gabarito_path = Path(args.gabarito)
    if not gabarito_path.is_absolute():
        gabarito_path = repo_root / gabarito_path

    if not seed_path.exists():
        raise FileNotFoundError(f"Seed não encontrado: {seed_path}")
    if not gabarito_path.exists():
        raise FileNotFoundError(f"Gabarito não encontrado: {gabarito_path}")

    seed_data = json.loads(seed_path.read_text(encoding="utf-8"))
    jobs = seed_data.get("jobs", [])
    seed_total = len(jobs)
    if seed_total == 0:
        print("[eval_eliminatorios] Aviso: seed sem vagas.")
        return

    gabarito_data = json.loads(gabarito_path.read_text(encoding="utf-8"))
    gabarito_entries = gabarito_data.get("entries", [])
    gabarito_ids = {e["id_hash"] for e in gabarito_entries}
    gabarito_total = len(gabarito_ids)
    gabarito_by_hash = {e["id_hash"]: e for e in gabarito_entries}

    config = load_config()
    filters_config = config.get("filters") or {}
    exclude_title_keywords = filters_config.get("exclude_title_keywords") or []
    location_blocklist_patterns = filters_config.get("location_blocklist_patterns") or []
    location_allowlist_patterns = filters_config.get("location_allowlist_patterns") or []
    jd_rescue_patterns = filters_config.get("jd_rescue_patterns") or []

    # --- Etapa 1: Hard filters ---
    after_title, discarded_title_list = apply_title_filter(jobs, exclude_title_keywords)
    after_blocklist, discarded_blocklist_list = apply_location_blocklist(after_title, location_blocklist_patterns)
    after_location, discarded_location_list = apply_location_filter(
        after_blocklist,
        location_allowlist_patterns,
        jd_rescue_patterns,
    )
    after_quality, discarded_quality_list = apply_quality_guard(after_location)

    def id_hashes(job_list: list[dict]) -> set[str]:
        return {_job_id_hash(j) for j in job_list if _job_id_hash(j)}

    elim_title = id_hashes(discarded_title_list)
    elim_blocklist = id_hashes(discarded_blocklist_list)
    elim_location = id_hashes(discarded_location_list)
    elim_quality = id_hashes(discarded_quality_list)

    in_gab = lambda s: len(s & gabarito_ids)
    n_title, n_blocklist = len(elim_title), len(elim_blocklist)
    n_location, n_quality = len(elim_location), len(elim_quality)
    g_title = in_gab(elim_title)
    g_blocklist = in_gab(elim_blocklist)
    g_location = in_gab(elim_location)
    g_quality = in_gab(elim_quality)

    # --- Etapa 2: LLM eliminatórios (sobre as que passaram nos hard filters) ---
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY não definida.")
    client = Anthropic(api_key=api_key)
    profile_path = repo_root / "config" / "profile.md"
    profile_content = load_profile(str(profile_path))

    passed_llm, eliminated_llm_list = _run_eliminatorios_llm(client, after_quality, profile_content, args.model)
    elim_llm = id_hashes(eliminated_llm_list)
    n_llm = len(elim_llm)
    g_llm = in_gab(elim_llm)

    # --- Comparação com gabarito ---
    all_eliminated_ids = elim_title | elim_blocklist | elim_location | elim_quality | elim_llm
    gabarito_eliminated = gabarito_ids & all_eliminated_ids
    escaparam_hashes = gabarito_ids - all_eliminated_ids
    escaparam_entries = [gabarito_by_hash[h] for h in escaparam_hashes]

    # Falsos positivos: eliminadas pelo pipeline mas NÃO estão no gabarito (vagas “boas” eliminadas)
    falsos_positivos_ids = all_eliminated_ids - gabarito_ids
    # Construir lista título + empresa a partir do seed
    job_by_hash = {_job_id_hash(j): j for j in jobs if _job_id_hash(j)}
    falsos_positivos_list = [
        {"title": job_by_hash[h].get("title", ""), "company": job_by_hash[h].get("company", "")}
        for h in falsos_positivos_ids
        if h in job_by_hash
    ]

    # --- Relatório (print) ---
    print("=== RELATÓRIO ===")
    print(f"Seed: {seed_total} vagas")
    print(f"Gabarito: {gabarito_total} vagas que devem ser eliminadas")
    print()
    print("HARD FILTERS:")
    print(f"  Title filter: {n_title} eliminadas ({g_title} do gabarito)")
    print(f"  Location blocklist: {n_blocklist} eliminadas ({g_blocklist} do gabarito)")
    print(f"  Location allowlist: {n_location} eliminadas ({g_location} do gabarito)")
    print(f"  Quality guard: {n_quality} eliminadas ({g_quality} do gabarito)")
    print()
    print(f"LLM ELIMINATÓRIOS ({args.model}):")
    print(f"  Eliminadas: {n_llm} ({g_llm} do gabarito)")
    print()
    print("RESULTADO FINAL:")
    print(f"  Gabarito eliminado: {len(gabarito_eliminated)}/{gabarito_total} ({100 * len(gabarito_eliminated) / gabarito_total:.0f}%)")
    print(f"  Escaparam: {len(escaparam_entries)} vagas")
    for e in escaparam_entries:
        print(f"    - {e.get('title', '')} @ {e.get('company', '')}")
    print(f"  Falsos positivos: {len(falsos_positivos_list)} vagas boas eliminadas")
    for fp in falsos_positivos_list:
        print(f"    - {fp.get('title', '')} @ {fp.get('company', '')}")

    # --- Salvar JSON ---
    timestamp = datetime.now().astimezone().strftime("%Y%m%d_%H%M%S")
    model_slug = _model_slug(args.model)
    out_name = f"eval_{model_slug}_{timestamp}.json"
    out_dir = repo_root / "data" / "eval"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / out_name

    report = {
        "created_at": datetime.now().astimezone().isoformat(),
        "seed_path": str(seed_path),
        "gabarito_path": str(gabarito_path),
        "model": args.model,
        "seed_total": seed_total,
        "gabarito_total": gabarito_total,
        "hard_filters": {
            "title": {"eliminated": n_title, "from_gabarito": g_title},
            "location_blocklist": {"eliminated": n_blocklist, "from_gabarito": g_blocklist},
            "location_allowlist": {"eliminated": n_location, "from_gabarito": g_location},
            "quality_guard": {"eliminated": n_quality, "from_gabarito": g_quality},
        },
        "llm_eliminatorios": {
            "eliminated": n_llm,
            "from_gabarito": g_llm,
        },
        "result": {
            "gabarito_eliminated": len(gabarito_eliminated),
            "gabarito_total": gabarito_total,
            "escaparam": [{"id_hash": e["id_hash"], "title": e.get("title"), "company": e.get("company")} for e in escaparam_entries],
            "falsos_positivos": falsos_positivos_list,
        },
    }
    out_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print()
    print(f"Relatório salvo em {out_path}")


if __name__ == "__main__":
    main()
