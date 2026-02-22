"""
fetch.py — Busca vagas via OpenAI Responses API com web_search_preview.

Épico 1.3 | Salva em data/raw/YYYY-MM-DD.json

Uso:
    python src/fetch.py
    python src/fetch.py --date 2026-02-22
"""

import os
import json
import argparse
from datetime import date
from pathlib import Path

# TODO: Épico 1.2 — implementar prompt de busca


def main():
    parser = argparse.ArgumentParser(description="Busca vagas via OpenAI web search")
    parser.add_argument("--date", default=str(date.today()), help="Data no formato YYYY-MM-DD")
    args = parser.parse_args()

    output_path = Path("data/raw") / f"{args.date}.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"[fetch.py] Buscando vagas para {args.date}...")
    print(f"[fetch.py] Saída: {output_path}")

    # TODO: Épico 1.3 — chamar OpenAI Responses API com web_search
    # api_key = os.environ["OPENAI_API_KEY"]
    # jobs = call_openai_web_search(api_key, ...)
    # output_path.write_text(json.dumps(jobs, indent=2, ensure_ascii=False))

    print("[fetch.py] ⚠️  Stub — implementação pendente (Épico 1.3)")


if __name__ == "__main__":
    main()
