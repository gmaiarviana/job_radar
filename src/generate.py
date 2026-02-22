"""
generate.py — Gera currículo e cover letter personalizados para uma vaga.

Épico 3.3 | Input: vaga do scored JSON + perfil + templates.
             Output: PDF em data/output/YYYY-MM-DD_empresa_titulo/

Uso:
    python src/generate.py --job-id JOB_ID [--date 2026-02-22]
"""

import os
import json
import argparse
from datetime import date
from pathlib import Path

# TODO: Épico 3.1 — integrar resume_base.md
# TODO: Épico 3.2 — integrar cover_letter_template.md
# TODO: Épico 3.3 — implementar chamada Claude Sonnet
# TODO: Épico 3.4 — geração de PDF (weasyprint ou reportlab)


def main():
    parser = argparse.ArgumentParser(description="Gera currículo e cover letter por vaga")
    parser.add_argument("--job-id", required=True, help="ID ou índice da vaga no scored JSON")
    parser.add_argument("--date", default=str(date.today()), help="Data no formato YYYY-MM-DD")
    args = parser.parse_args()

    scored_path = Path("data/scored") / f"{args.date}.json"
    if not scored_path.exists():
        print(f"[generate.py] ❌ Arquivo não encontrado: {scored_path}")
        print("[generate.py] Execute score.py primeiro.")
        return

    print(f"[generate.py] Gerando materiais para job-id={args.job_id} ({args.date})...")

    # TODO: Épico 3.3 — implementar geração
    # api_key = os.environ["ANTHROPIC_API_KEY"]
    # jobs = json.loads(scored_path.read_text())
    # job = next(j for j in jobs if str(j["id"]) == args.job_id)
    # resume_md = generate_resume(api_key, job, ...)
    # cover_md = generate_cover_letter(api_key, job, ...)
    # save_pdfs(resume_md, cover_md, output_dir=...)

    print("[generate.py] ⚠️  Stub — implementação pendente (Épico 3.3)")


if __name__ == "__main__":
    main()
