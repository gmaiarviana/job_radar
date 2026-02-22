"""
score.py — Pontua vagas via Claude Haiku contra o perfil do candidato.

Épico 1.5 | Lê data/raw/YYYY-MM-DD.json, salva em data/scored/YYYY-MM-DD.json

Uso:
    python src/score.py
    python src/score.py --date 2026-02-22
"""

import os
import json
import argparse
from datetime import date
from pathlib import Path

# TODO: Épico 1.4 — implementar prompt de scoring
# TODO: Épico 1.5 — implementar chamada Claude Haiku com batch de vagas


def main():
    parser = argparse.ArgumentParser(description="Pontua vagas via Claude Haiku")
    parser.add_argument("--date", default=str(date.today()), help="Data no formato YYYY-MM-DD")
    args = parser.parse_args()

    raw_path = Path("data/raw") / f"{args.date}.json"
    scored_path = Path("data/scored") / f"{args.date}.json"
    scored_path.parent.mkdir(parents=True, exist_ok=True)

    if not raw_path.exists():
        print(f"[score.py] ❌ Arquivo não encontrado: {raw_path}")
        print("[score.py] Execute fetch.py primeiro.")
        return

    print(f"[score.py] Pontuando vagas de {args.date}...")
    print(f"[score.py] Input:  {raw_path}")
    print(f"[score.py] Output: {scored_path}")

    # TODO: Épico 1.5 — implementar scoring
    # api_key = os.environ["ANTHROPIC_API_KEY"]
    # jobs = json.loads(raw_path.read_text())
    # scored = score_jobs(api_key, jobs, profile_path="config/profile.md")
    # top_jobs = [j for j in scored if j["score"] >= 80]
    # scored_path.write_text(json.dumps(top_jobs, indent=2, ensure_ascii=False))

    print("[score.py] ⚠️  Stub — implementação pendente (Épico 1.5)")


if __name__ == "__main__":
    main()
