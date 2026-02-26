"""
Camada de dedup persistente: lê, checa e persiste o arquivo de "vagas já vistas".
Nenhum outro módulo deve acessar o arquivo diretamente.
"""

import json
from datetime import date
from pathlib import Path
from typing import Any

from src.paths import SEEN_JOBS_PATH

LOG_PREFIX = "[seen_jobs]"

DEFAULT_PATH = SEEN_JOBS_PATH


def load_seen(path: str | Path = DEFAULT_PATH) -> dict[str, Any]:
    """
    Lê o arquivo JSON de vagas já vistas.
    Retorna {} se não existir. Cria o diretório data/ se necessário.
    """
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    if not p.exists():
        p.write_text("{}", encoding="utf-8")
        return {}
    with open(p, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data if isinstance(data, dict) else {}


def is_seen(id_hash: str, seen: dict) -> bool:
    """Retorna True se id_hash já está no dict de vagas vistas."""
    return id_hash in seen


def mark_seen(
    id_hash: str,
    source: str,
    title: str,
    company: str,
    seen: dict,
) -> None:
    """
    Adiciona entrada ao dict em memória (não persiste).
    Formato: { id_hash: { "first_seen": "YYYY-MM-DD", "source", "title", "company" } }
    """
    today = date.today().isoformat()
    seen[id_hash] = {
        "first_seen": today,
        "source": source,
        "title": title,
        "company": company,
    }


def save_seen(seen: dict, path: str | Path = DEFAULT_PATH) -> None:
    """Persiste o dict como JSON (ensure_ascii=False, indent=2)."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(seen, f, ensure_ascii=False, indent=2)
