"""
github_api.py — Persistência via GitHub Contents API.

Épico 10.1 | Duas operações: get_file (GET) e put_file (PUT/CREATE).
Usa apenas stdlib (urllib, base64, json). Sem dependências externas.
"""

from __future__ import annotations

import base64
import json
import os
from urllib.error import HTTPError
from urllib.request import Request, urlopen

_COMMIT_AUTHOR = {"name": "Job Radar App", "email": "app@jobradar"}


def _get_config() -> tuple[str, str]:
    """Retorna (token, owner/repo). Lança RuntimeError se ausentes."""
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise RuntimeError("GITHUB_TOKEN não configurado")
    repo = os.environ.get("GITHUB_REPO")
    if not repo:
        raise RuntimeError("GITHUB_REPO não configurado")
    return token, repo


def _make_url(repo: str, path: str) -> str:
    return f"https://api.github.com/repos/{repo}/contents/{path}"


def _headers(token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def get_file(path: str) -> dict | None:
    """
    GET contents/{path} via GitHub API.
    Retorna {"content": str (decoded), "sha": str} ou None se arquivo não existir (404).
    Lança RuntimeError em outros erros HTTP.
    """
    token, repo = _get_config()
    url = _make_url(repo, path)
    req = Request(url, headers=_headers(token), method="GET")

    try:
        with urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except HTTPError as e:
        if e.code == 404:
            return None
        body = e.read().decode("utf-8", errors="replace") if e.fp else str(e)
        raise RuntimeError(f"GitHub API GET {path} falhou ({e.code}): {body}") from e

    raw_content = data.get("content", "")
    decoded = base64.b64decode(raw_content).decode("utf-8")
    return {"content": decoded, "sha": data["sha"]}


def put_file(
    path: str,
    content: str,
    sha: str | None = None,
    message: str | None = None,
) -> None:
    """
    PUT contents/{path} via GitHub API.
    Cria (sha=None) ou atualiza (sha obrigatório) um arquivo.
    content: string UTF-8 — o módulo faz o encode para base64 internamente.
    Lança RuntimeError em falha (conflito, auth, rede).
    """
    token, repo = _get_config()
    url = _make_url(repo, path)

    commit_msg = message or f"chore: update {path} via app"
    encoded = base64.b64encode(content.encode("utf-8")).decode("ascii")

    body: dict = {
        "message": commit_msg,
        "content": encoded,
        "committer": _COMMIT_AUTHOR,
    }
    if sha is not None:
        body["sha"] = sha

    payload = json.dumps(body).encode("utf-8")
    req = Request(
        url,
        data=payload,
        headers={**_headers(token), "Content-Type": "application/json"},
        method="PUT",
    )

    try:
        with urlopen(req) as resp:
            status = resp.status
            if status not in (200, 201):
                resp_body = resp.read().decode("utf-8", errors="replace")
                raise RuntimeError(
                    f"GitHub API PUT {path} retornou status {status}: {resp_body}"
                )
    except HTTPError as e:
        resp_body = e.read().decode("utf-8", errors="replace") if e.fp else str(e)
        raise RuntimeError(
            f"GitHub API PUT {path} falhou ({e.code}): {resp_body}"
        ) from e
