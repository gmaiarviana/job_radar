"""
paths.py — Centraliza paths do pipeline (Épico 4.4.3).

Este é o único módulo que lê a seção `output` do config/search.yaml.
"""

from __future__ import annotations

from pathlib import Path

from src.fetch_pipeline import load_config

_DEFAULTS: dict[str, str] = {
    "raw_dir": "data/raw",
    "filtered_dir": "data/filtered",
    "scored_dir": "data/scored",
    "feedback_dir": "data/feedback",
    "output_dir": "data/output",
    "seen_jobs_path": "data/seen_jobs.json",
}


def _read_output_config() -> dict:
    """
    Lê config/search.yaml e retorna o dict da seção `output`.
    Em qualquer falha, retorna {} e usa defaults.
    """
    try:
        cfg = load_config()
    except Exception:
        return {}
    if not isinstance(cfg, dict):
        return {}
    out = cfg.get("output") or {}
    return out if isinstance(out, dict) else {}


_OUTPUT = _read_output_config()

RAW_DIR = Path(_OUTPUT.get("raw_dir") or _DEFAULTS["raw_dir"])
FILTERED_DIR = Path(_OUTPUT.get("filtered_dir") or _DEFAULTS["filtered_dir"])
SCORED_DIR = Path(_OUTPUT.get("scored_dir") or _DEFAULTS["scored_dir"])
FEEDBACK_DIR = Path(_OUTPUT.get("feedback_dir") or _DEFAULTS["feedback_dir"])
OUTPUT_DIR = Path(_OUTPUT.get("output_dir") or _DEFAULTS["output_dir"])
SEEN_JOBS_PATH = Path(_OUTPUT.get("seen_jobs_path") or _DEFAULTS["seen_jobs_path"])


def ensure_dirs() -> None:
    """
    Cria os diretórios do pipeline (e o parent do seen_jobs) se não existirem.
    """
    for d in (RAW_DIR, FILTERED_DIR, SCORED_DIR, FEEDBACK_DIR, OUTPUT_DIR):
        d.mkdir(parents=True, exist_ok=True)
    SEEN_JOBS_PATH.parent.mkdir(parents=True, exist_ok=True)
