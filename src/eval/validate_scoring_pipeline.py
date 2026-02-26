"""
Validação do pipeline de 2 chamadas no seed (Épico 5.1.5).
Roda analyze_job → compute_ceiling → score_with_analysis para 5 vagas específicas
e imprime tabela de resultados. Requer ANTHROPIC_API_KEY no .env.

Uso: python src/eval/validate_scoring_pipeline.py --seed <path>
Ex.: python src/eval/validate_scoring_pipeline.py --seed data/filtered/seed_2026-02-24_123007.json
"""
import sys
import json
import argparse
from pathlib import Path

_root = Path(__file__).resolve().parent.parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from dotenv import load_dotenv
load_dotenv()

from src.score import analyze_job, compute_ceiling, score_with_analysis, load_profile
from anthropic import Anthropic

TEST_CASES = [
    {"title": "Principal Product Manager, AI Control Plane and Guardrails", "company": "GitLab", "expected_max": 65, "reason": "seniority_gap"},
    {"title": "AI Self-Service Program Manager", "company": "Samsara", "expected_max": 60, "reason": "domain_gap_core"},
    {"title": "Data Collection Program Manager, Robotics", "company": "Scale AI", "expected_max": 60, "reason": "domain_gap_core"},
    {"title": "Senior Technical Program Manager, Infrastructure", "company": "Planet Labs", "expected_max": 65, "reason": "seniority_gap + domain"},
    {"title": "Technical Program Manager - Product Operations", "company": "Nubank", "expected_max": 65, "reason": "seniority_gap + domain_gap_core (Legal Tech niche)"},
]


def find_job_in_seed(jobs, title: str, company: str):
    """Case-insensitive match por título e empresa. Retorna o job ou None."""
    title_l = title.strip().lower()
    company_l = company.strip().lower()
    for j in jobs:
        j_title = (j.get("title") or "").strip().lower()
        j_company = (j.get("company") or "").strip().lower()
        if j_title == title_l and j_company == company_l:
            return j
    return None


def main():
    parser = argparse.ArgumentParser(description="Valida pipeline de 2 chamadas em vagas do seed")
    parser.add_argument("--seed", required=True, help="Caminho para o JSON do seed (raw ou filtered)")
    args = parser.parse_args()

    seed_path = Path(args.seed)
    if not seed_path.exists():
        print(f"[validate_scoring_pipeline.py] [ERR] Arquivo não encontrado: {seed_path}")
        sys.exit(1)

    data = json.loads(seed_path.read_text(encoding="utf-8"))
    jobs = data.get("jobs", [])
    if not jobs:
        print("[validate_scoring_pipeline.py] [ERR] Nenhuma vaga no seed.")
        sys.exit(1)

    api_key = __import__("os").environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("[validate_scoring_pipeline.py] [ERR] ANTHROPIC_API_KEY não encontrada no .env")
        sys.exit(1)

    profile_path = _root / "config" / "profile.md"
    if not profile_path.exists():
        profile_path = Path("config/profile.md")
    profile = load_profile(str(profile_path))
    client = Anthropic(api_key=api_key)

    # Cabeçalho da tabela
    col_vaga = 32
    col_empresa = 12
    col_ceiling = 7
    col_score = 6
    col_esperado = 8
    col_ok = 5
    sep = f"| {'Vaga'.ljust(col_vaga)} | {'Empresa'.ljust(col_empresa)} | {'Ceiling'.rjust(col_ceiling)} | {'Score'.rjust(col_score)} | {'Esperado'.ljust(col_esperado)} | {'OK?'.ljust(col_ok)} |"
    hline = "-" * len(sep)
    print(hline)
    print(sep)
    print(hline)

    results = []
    for tc in TEST_CASES:
        job = find_job_in_seed(jobs, tc["title"], tc["company"])
        if job is None:
            print(f"| (nao encontrada: {tc['title'][:col_vaga-4]}...) | {tc['company'].ljust(col_empresa)} | {'-'.rjust(col_ceiling)} | {'-'.rjust(col_score)} | <={tc['expected_max']} |  -  |")
            results.append(None)
            continue

        analysis = analyze_job(client, job, profile)
        if analysis is None:
            print(f"| (analyze_job falhou) {tc['title'][:col_vaga-20]}... | {tc['company'].ljust(col_empresa)} | {'-'.rjust(col_ceiling)} | {'-'.rjust(col_score)} | <={tc['expected_max']} |  -  |")
            results.append(None)
            continue

        ceiling_result = compute_ceiling(analysis)
        result = score_with_analysis(client, job, analysis, ceiling_result, profile)
        if result is None:
            print(f"| (score_with_analysis falhou) {tc['title'][:col_vaga-28]}... | {tc['company'].ljust(col_empresa)} | {'-'.rjust(col_ceiling)} | {'-'.rjust(col_score)} | <={tc['expected_max']} |  -  |")
            results.append(None)
            continue

        ceiling = ceiling_result.get("ceiling", 0)
        score = result.get("score", 0)
        expected_max = tc["expected_max"]
        if expected_max >= 80:
            ok = score >= 80
        else:
            ok = score <= expected_max
        results.append(ok)
        ok_str = "  ok  " if ok else "  --  "
        esperado_str = f"<={expected_max}" if expected_max < 80 else ">=80"
        title_short = (tc["title"][:col_vaga-2] + "..") if len(tc["title"]) > col_vaga else tc["title"]
        print(f"| {title_short.ljust(col_vaga)} | {tc['company'].ljust(col_empresa)} | {str(ceiling).rjust(col_ceiling)} | {str(score).rjust(col_score)} | {esperado_str.ljust(col_esperado)} | {ok_str} |")

    print(hline)
    ok_count = sum(1 for r in results if r is True)
    total_ran = sum(1 for r in results if r is not None)
    print(f"\n{ok_count}/5 dentro do esperado.")
    if total_ran < 5:
        print(f"[i] {5 - total_ran} vaga(s) do teste nao encontrada(s) no seed.")


if __name__ == "__main__":
    main()
