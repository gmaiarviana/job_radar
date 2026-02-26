"""
notify.py — Envia email quando há vagas com PERFECT_MATCH (score >= 95).

Épico 4.3 | Roda após score.py no pipeline do GitHub Actions.

Uso:
    python src/notify.py --date 2026-02-22
"""

import os
import json
import argparse
import sys
import smtplib
from datetime import date
from email.mime.text import MIMEText
from pathlib import Path

# Garante projeto na path ao rodar como python src/notify.py
if __name__ == "__main__":
    _root = Path(__file__).resolve().parent.parent
    if str(_root) not in sys.path:
        sys.path.insert(0, str(_root))

from src.paths import SCORED_DIR, ensure_dirs

# TODO: Épico 4.3 — implementar envio de email via Gmail SMTP
PERFECT_MATCH_THRESHOLD = 95


def main():
    parser = argparse.ArgumentParser(description="Envia email para vagas PERFECT_MATCH")
    parser.add_argument("--date", default=str(date.today()), help="Data no formato YYYY-MM-DD")
    args = parser.parse_args()

    ensure_dirs()
    scored_dir = SCORED_DIR
    scored_files = sorted(scored_dir.glob(f"{args.date}*.json"), reverse=True)

    if not scored_files:
        print(f"[notify.py] Nenhum arquivo scored encontrado para a data: {args.date}")
        return

    scored_path = scored_files[0]

    data = json.loads(scored_path.read_text(encoding="utf-8"))
    jobs = data.get("jobs", [])
    perfect_matches = [j for j in jobs if j.get("score", 0) >= PERFECT_MATCH_THRESHOLD]

    if not perfect_matches:
        print(f"[notify.py] Nenhum PERFECT_MATCH encontrado (score >= {PERFECT_MATCH_THRESHOLD})")
        return

    print(f"[notify.py] {len(perfect_matches)} PERFECT_MATCH(es) encontrado(s)!")

    # TODO: Épico 4.3 — implementar envio real
    # smtp_user = os.environ["SMTP_USER"]
    # smtp_pass = os.environ["SMTP_PASS"]
    # notify_email = os.environ["NOTIFY_EMAIL"]
    # send_email(smtp_user, smtp_pass, notify_email, perfect_matches)

    print("[notify.py] ⚠️  Stub — implementação pendente (Épico 4.3)")


if __name__ == "__main__":
    main()
