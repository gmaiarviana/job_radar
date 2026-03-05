"""
app.py — Interface Streamlit do Job Radar.

Épico 6 + 9 + 10 | UI funcional: tabela unificada de vagas + Resumo + Busca Manual
com persistência remota via GitHub API no Streamlit Cloud.

Uso:
    streamlit run app.py
"""

from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

import streamlit as st
import yaml
from anthropic import Anthropic
from dotenv import load_dotenv

# Bridge: Streamlit Cloud secrets → os.environ (para Anthropic client e outros)
try:
    for key in ("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GITHUB_TOKEN", "GITHUB_REPO", "AUTHORIZED_EMAIL"):
        if key in st.secrets:
            os.environ[key] = st.secrets[key]
except Exception:
    pass

load_dotenv()

from src import github_api
from src.job_schema import normalize_job
from src.paths import SCORED_DIR, ensure_dirs
from src.score import analyze_job, compute_ceiling, load_profile, score_with_analysis
from src.seen_jobs import load_seen, mark_seen, save_seen

# --- Config da página ---
st.set_page_config(
    page_title="Job Radar",
    page_icon="📡",
    layout="wide",
)

# --- Helpers: leitura de dados scored ---
def _date_from_filename(name: str) -> str | None:
    """Extrai YYYY-MM-DD do nome do arquivo. Trata prefixo manual_: manual_2026-02-26_153000.json → 2026-02-26."""
    base = name.replace(".json", "")
    if base.startswith("manual_"):
        base = base[7:]  # manual_YYYY-MM-DD_HHMMSS → YYYY-MM-DD_HHMMSS
    match = re.match(r"(\d{4}-\d{2}-\d{2})", base)
    return match.group(1) if match else None


def _load_scored_jobs() -> list[dict]:
    """
    Lê todos os .json de data/scored/ (exceto *_discarded.json e seed_*).
    Retorna lista unificada de jobs com metadados: job (dict), file_date (str), source.
    """
    if not SCORED_DIR.exists():
        return []

    rows: list[dict] = []
    for path in SCORED_DIR.glob("*.json"):
        name = path.name
        if "_discarded" in name or name.startswith("seed_"):
            continue
        file_date = _date_from_filename(name)
        source = "manual" if name.startswith("manual_") else "pipeline"

        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue

        job_list = data.get("jobs") or data.get("scored_jobs") or []
        for job in job_list:
            if isinstance(job, dict):
                # 9.5: use real source from job; fallback to file-level source
                job_source = job.get("source", source)
                # For manual jobs, always show "manual"
                if name.startswith("manual_"):
                    job_source = "manual"
                rows.append({
                    "job": job,
                    "file_date": file_date or "",
                    "source": job_source,
                })
    return rows


def _score_badge_style(score: int) -> tuple[str, str]:
    """(background, text_color): verde ≥85, amarelo 70–84, cinza <70."""
    if score >= 85:
        return ("#2e7d32", "white")   # verde
    if score >= 70:
        return ("#f9a825", "black")   # amarelo
    return ("#616161", "white")       # cinza


def get_verdict(score: int | None, main_gap: str | None) -> tuple[str, str, str]:
    """Retorna (label, color, emoji): APLICAR/AVALIAR/PULAR com cor e emoji."""
    if score is None:
        return ("—", "gray", "⚪")
    if score >= 85:
        return ("APLICAR", "green", "🟢")
    if score >= 70:
        return ("AVALIAR", "orange", "🟡")
    return ("PULAR", "gray", "⚪")


def _verdict_reason_phrase(score: int | None, main_gap: str | None) -> str:
    """Frase de motivo: main_gap ou 'Fit direto...' quando score ≥ 85 e main_gap vazio/genérico (curto)."""
    gap = (main_gap or "").strip()
    if score is not None and score >= 85 and (not gap or len(gap) < 20):
        return "Fit direto — domínio e seniority compatíveis"
    return gap or "—"


def _format_report(job: dict) -> str:
    """Gera texto markdown de relatório para uma vaga (botão Copiar Relatório)."""
    score = job.get("score")
    main_gap = job.get("main_gap") or ""
    verdict_label, _, verdict_emoji = get_verdict(score, main_gap)
    reason = _verdict_reason_phrase(score, main_gap)

    lines = []
    lines.append(f"# {job.get('title', '(Sem título)')}")
    lines.append(f"**Empresa:** {job.get('company', '(Sem empresa)')}")
    lines.append(f"**Score:** {score if score is not None else '—'}")
    lines.append(f"**Veredito:** {verdict_emoji} {verdict_label} — {reason}")
    if job.get("justification"):
        lines.append(f"**Justificativa:** {job['justification']}")
    if job.get("main_gap"):
        lines.append(f"**Principal gap:** {job['main_gap']}")

    core_req = job.get("core_requirements")
    if core_req and isinstance(core_req, list):
        lines.append("**Requisitos principais:**")
        for req in core_req:
            if isinstance(req, dict):
                rq = req.get("requirement") or req.get("requirement_text") or "(requisito)"
                has_ev = req.get("has_evidence", "full")
                if has_ev == "full" or has_ev is True:
                    icon = "✓"
                elif has_ev == "partial":
                    icon = "⚠️"
                else:
                    icon = "✗"
                ev = req.get("evidence") or ""
                lines.append(f"- {rq} — {icon} {ev}")
            else:
                lines.append(f"- {req}")

    sr = job.get("seniority_comparison")
    if sr and isinstance(sr, dict):
        lines.append("**Seniority:**")
        lines.append(f"- JD pede: {sr.get('jd_asks', '—')}")
        lines.append(f"- Candidato tem: {sr.get('candidate_has', '—')}")
        if sr.get("gap"):
            lines.append(f"- Gap: {sr['gap']}")

    return "\n".join(lines)


# --- Sidebar: seletor de data (único, compartilhado entre Vagas e Resumo) ---
def _render_sidebar(all_rows: list[dict]) -> str | None:
    dates = sorted({r["file_date"] for r in all_rows if r["file_date"]}, reverse=True)
    if not dates:
        st.sidebar.caption("Nenhuma data disponível.")
        return None
    selected = st.sidebar.selectbox(
        "Data dos resultados",
        options=dates,
        index=0,
        format_func=lambda d: d or "(sem data)",
        key="shared_date_selector",
    )
    return selected


# --- Renderização de detalhes expandidos (reutilizado em Vagas, Resumo e Busca Manual) ---
def _render_expanded_details(job: dict, key_suffix: str) -> None:
    """
    9.1: Renderiza conteúdo expandido na ordem:
    veredito + frase de motivo → justification → main_gap → core_requirements → seniority_comparison → link.
    Sem campos ceiling visíveis.
    9.2: Botões de cópia (JD + Relatório) com toggle via session_state.
    """
    score = job.get("score")
    main_gap = job.get("main_gap") or ""
    url = job.get("url") or ""
    verdict_label, _vcolor, verdict_emoji = get_verdict(score, main_gap)
    reason_phrase = _verdict_reason_phrase(score, main_gap)

    # Veredito no topo
    st.markdown(f"**{verdict_emoji} {verdict_label}** — {reason_phrase}")
    st.markdown("---")

    # Justification
    if job.get("justification"):
        st.markdown(f"**Justificativa:** {job['justification']}")

    # Main gap
    if job.get("main_gap"):
        st.markdown(f"**Principal gap:** {job['main_gap']}")

    # Core requirements
    core_req = job.get("core_requirements")
    if core_req and isinstance(core_req, list):
        st.markdown("**Requisitos principais:**")
        for req in core_req:
            if isinstance(req, dict):
                rq = req.get("requirement") or req.get("requirement_text") or "(requisito)"
                has_ev = req.get("has_evidence", "full")
                if has_ev == "full" or has_ev is True:
                    icon = "✓"
                elif has_ev == "partial":
                    icon = "⚠️"
                else:
                    icon = "✗"
                ev = req.get("evidence") or ""
                st.markdown(f"- {rq} — {icon} {ev}")
            else:
                st.markdown(f"- {req}")
    elif job.get("evidence"):
        st.markdown("**Evidências:**")
        st.markdown(job["evidence"])

    # Seniority comparison
    sr = job.get("seniority_comparison")
    if sr and isinstance(sr, dict):
        st.markdown("**Seniority:**")
        st.markdown(f"- JD pede: {sr.get('jd_asks', '—')}")
        st.markdown(f"- Candidato tem: {sr.get('candidate_has', '—')}")
        if sr.get("gap"):
            st.markdown(f"- Gap: {sr['gap']}")

    # Link
    if url:
        st.markdown(f"**Link:** [Abrir vaga]({url})")

    # 9.2: Botões de cópia
    st.markdown("---")
    col_jd, col_report = st.columns(2)

    jd_key = f"show_jd_{key_suffix}"
    report_key = f"show_report_{key_suffix}"

    with col_jd:
        if st.button("Copiar JD", key=f"btn_jd_{key_suffix}"):
            st.session_state[jd_key] = not st.session_state.get(jd_key, False)
    with col_report:
        if st.button("Copiar Relatório", key=f"btn_report_{key_suffix}"):
            st.session_state[report_key] = not st.session_state.get(report_key, False)

    if st.session_state.get(jd_key, False):
        jd_full = job.get("jd_full") or job.get("description") or "(JD não disponível)"
        st.code(jd_full, language=None)

    if st.session_state.get(report_key, False):
        report_text = _format_report(job)
        st.code(report_text, language=None)


# --- Renderização de cards (reutilizado em Vagas e Resumo) ---
def _render_job_cards(jobs_with_meta: list[dict], key_prefix: str = "") -> None:
    """Renderiza lista de cards de vagas com expander."""
    for idx, item in enumerate(jobs_with_meta):
        job = item["job"]
        source = item["source"]
        score = job.get("score")
        title = job.get("title") or "(Sem título)"
        company = job.get("company") or "(Sem empresa)"
        url = job.get("url") or ""
        main_gap = job.get("main_gap") or ""
        salary = job.get("salary")

        score_label = str(score) if score is not None else "—"
        bg, fg = _score_badge_style(score) if score is not None else ("#616161", "white")
        verdict_label, verdict_color, verdict_emoji = get_verdict(score, main_gap)

        with st.container():
            c1, c2, c3, c4, c5 = st.columns([3, 2, 1, 1, 1])
            with c1:
                st.markdown(f"**{title}**")
            with c2:
                st.markdown(company)
                if salary is not None and str(salary).strip():
                    st.caption(str(salary).strip())
            with c3:
                st.markdown(f'<span style="background:{bg};color:{fg};padding:2px 8px;border-radius:4px;">{score_label}</span> {verdict_emoji} {verdict_label}', unsafe_allow_html=True)
            with c4:
                st.caption(source)
            with c5:
                if url:
                    st.link_button("Link", url, use_container_width=True)
                else:
                    st.caption("—")

        # 9.1: Expander label "Detalhes"
        with st.expander("Detalhes", expanded=False):
            _render_expanded_details(job, key_suffix=f"{key_prefix}{idx}")


# --- Página 1: Vagas ---
def _render_vagas(all_rows: list[dict], selected_date: str | None):
    if selected_date is not None:
        rows = [r for r in all_rows if r["file_date"] == selected_date]
    else:
        rows = all_rows

    jobs_with_meta = sorted(
        rows,
        key=lambda r: (r["job"].get("score") is None, -(r["job"].get("score") or 0)),
    )

    if not jobs_with_meta:
        st.info("Nenhuma vaga scored encontrada. Execute o pipeline (`python src/fetch.py` e `python src/score.py`) ou use a aba Busca Manual para avaliar vagas manualmente.")
        return

    _render_job_cards(jobs_with_meta, key_prefix="vagas_")


# --- Página 2: Resumo (APLICAR only) ---
def _render_resumo(all_rows: list[dict], selected_date: str | None):
    if selected_date is not None:
        rows = [r for r in all_rows if r["file_date"] == selected_date]
    else:
        rows = all_rows

    # Filter: only APLICAR (score >= 85)
    aplicar_rows = [r for r in rows if (r["job"].get("score") or 0) >= 85]

    # Sort by score descending
    aplicar_rows.sort(key=lambda r: -(r["job"].get("score") or 0))

    if not aplicar_rows:
        st.info("Nenhuma vaga com veredito APLICAR (score >= 85) encontrada para a data selecionada.")
        return

    _render_job_cards(aplicar_rows, key_prefix="resumo_")


# --- Helpers: Busca Manual (links + scoring) ---
def _load_manual_searches() -> list[dict]:
    """Carrega config/manual_searches.yaml; retorna lista de {name, url}."""
    path = Path("config/manual_searches.yaml")
    if not path.exists():
        return []
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        return data.get("searches") or []
    except Exception:
        return []


def _run_manual_scoring(raw: dict) -> tuple[dict | None, str | None]:
    """
    Executa normalize_job → analyze_job → compute_ceiling → score_with_analysis.
    Retorna (result_job, None) em sucesso ou (None, mensagem_erro) em falha.
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return None, "ANTHROPIC_API_KEY não definida. Configure no .env e reinicie o app."

    try:
        job = normalize_job(raw, source="linkedin")
    except Exception as e:
        return None, f"Erro ao normalizar vaga: {e}"

    profile_path = "config/profile.md"
    try:
        profile = load_profile(profile_path)
    except FileNotFoundError as e:
        return None, str(e)
    except Exception as e:
        return None, f"Erro ao carregar perfil: {e}"

    try:
        client = Anthropic()
    except Exception as e:
        return None, f"Erro ao criar cliente Anthropic: {e}"

    analysis = analyze_job(client, job, profile)
    if analysis is None:
        return None, "Falha na análise da vaga (Chamada 1). Tente novamente."

    ceiling_result = compute_ceiling(analysis)
    result = score_with_analysis(client, job, analysis, ceiling_result, profile)
    if result is None:
        return None, "Falha ao atribuir score (Chamada 2). Tente novamente."

    # Montar job completo como no score.py
    result["company"] = job.get("company", "")
    result["location"] = job.get("location", "")
    result["title"] = job.get("title", "")
    result["url"] = job.get("url", "")
    result["id"] = job.get("id") or job.get("id_hash")
    result["id_hash"] = job.get("id_hash") or job.get("id")
    result["core_requirements"] = analysis.get("core_requirements", [])
    result["seniority_comparison"] = analysis.get("seniority_comparison", {})
    result["source"] = "manual"
    result["jd_full"] = raw.get("description", "")
    return result, None


# --- Página 3: Busca Manual — Links + Paste-and-score ---
def _render_busca_manual():
    # Seção 1: Links de busca
    searches = _load_manual_searches()
    if searches:
        st.subheader("Links de busca")
        cols = st.columns(min(len(searches), 5))
        for i, item in enumerate(searches):
            name = item.get("name") or "Link"
            link_url = item.get("url") or "#"
            with cols[i % len(cols)]:
                st.link_button(name, link_url, use_container_width=True)
        st.markdown("---")

    # 9.3: Check if we should show form or result
    if st.session_state.get("manual_result") is not None:
        result = st.session_state["manual_result"]
        st.subheader("Resultado da avaliação")

        # Score badge visible before expander (fix: score was hidden inside details only)
        score = result.get("score")
        main_gap = result.get("main_gap") or ""
        score_label = str(score) if score is not None else "—"
        bg, fg = _score_badge_style(score) if score is not None else ("#616161", "white")
        verdict_label, _, verdict_emoji = get_verdict(score, main_gap)
        st.markdown(
            f'<span style="background:{bg};color:{fg};padding:4px 12px;border-radius:6px;font-size:1.1rem;font-weight:700;">{score_label}</span>'
            f'&nbsp; {verdict_emoji} **{verdict_label}**',
            unsafe_allow_html=True,
        )

        with st.expander("Detalhes", expanded=True):
            _render_expanded_details(result, key_suffix="manual_result")

        if st.button("Avaliar outra vaga", key="btn_avaliar_outra"):
            st.session_state["manual_result"] = None
            st.rerun()
        return

    # Seção 2: Formulário paste-and-score
    # 9.4: Ordem: empresa → título → JD → url → localização
    st.subheader("Avaliar vaga (colar JD)")
    with st.form("paste_and_score_form"):
        company = st.text_input("Empresa *", placeholder="Ex: Acme Inc.")
        title = st.text_input("Título da vaga *", placeholder="Ex: Senior Product Manager")
        jd = st.text_area("JD (descrição da vaga) *", placeholder="Cole a descrição da vaga aqui", height=200)
        url = st.text_input("URL (opcional)", placeholder="https://...")
        location = st.text_input("Localização (opcional)", placeholder="Remote, LATAM, etc.")
        submitted = st.form_submit_button("Avaliar")

    if not submitted:
        return

    if not (title and company and jd):
        st.error("Preencha título, empresa e JD para continuar.")
        return

    raw = {
        "title": title.strip(),
        "company": company.strip(),
        "description": jd.strip(),
        "url": url.strip() if url else "",
        "location": location.strip() if location else "",
    }

    with st.spinner("Analisando vaga..."):
        result, err = _run_manual_scoring(raw)

    if err:
        st.error(err)
        return

    # Store result in session_state for toggle behavior (9.3)
    st.session_state["manual_result"] = result

    # Persistência: manual_*.json + seen_jobs
    now_local = datetime.now()
    ts = now_local.strftime("%Y-%m-%d_%H%M%S")
    filename = f"manual_{ts}.json"
    now_utc = datetime.now(timezone.utc)

    payload = {
        "scored_at": now_utc.isoformat(),
        "source_file": "manual",
        "summary": {
            "total_input": 1,
            "total_scored": 1,
            "total_top": 1 if (result.get("score") or 0) >= 70 else 0,
        },
        "jobs": [result],
    }

    id_hash = result.get("id_hash") or result.get("id")
    persisted_remote = False

    # Tentativa 1: GitHub API (Streamlit Cloud)
    try:
        seen_data = github_api.get_file("data/seen_jobs.json")
        if seen_data:
            seen = json.loads(seen_data["content"])
            seen_sha = seen_data["sha"]
        else:
            seen = {}
            seen_sha = None

        payload_json = json.dumps(payload, indent=2, ensure_ascii=False)
        github_api.put_file(
            f"data/scored/{filename}",
            payload_json,
            sha=None,
            message=f"chore: add {filename} via app",
        )

        if id_hash:
            mark_seen(id_hash, "manual", result.get("title", ""), result.get("company", ""), seen)
            seen_json = json.dumps(seen, ensure_ascii=False, indent=2)
            github_api.put_file(
                "data/seen_jobs.json",
                seen_json,
                sha=seen_sha,
                message="chore: update seen_jobs.json via app",
            )

        persisted_remote = True
        st.success("Vaga avaliada e salva no repositório!")
    except Exception:
        pass

    # Tentativa 2: Fallback filesystem local
    if not persisted_remote:
        try:
            ensure_dirs()
            out_path = SCORED_DIR / filename
            out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

            if id_hash:
                seen = load_seen()
                mark_seen(id_hash, "manual", result.get("title", ""), result.get("company", ""), seen)
                save_seen(seen)

            st.success("Vaga avaliada e salva localmente.")
            st.caption("Persistência remota indisponível.")
        except Exception:
            st.info("Resultado exibido. Persistência indisponível neste ambiente.")


# --- Auth: verificação de email autorizado ---
def _check_auth() -> bool:
    """
    Verifica se o usuário está autorizado (Streamlit Cloud com Google OAuth).
    Retorna True se autorizado ou se auth não está configurada (local).
    """
    authorized_email = os.environ.get("AUTHORIZED_EMAIL")
    if not authorized_email:
        return True

    # st.user (≥ 1.35) com fallback para st.experimental_user
    user_obj = getattr(st, "user", None) or getattr(st, "experimental_user", None)
    if user_obj is None:
        return True

    email = getattr(user_obj, "email", None)
    if email is None:
        return True

    return email == authorized_email


# --- Main ---
def main():
    st.title("📡 Job Radar")
    st.caption("Vagas scored do pipeline + manuais (Busca Manual)")

    if not _check_auth():
        st.error("Acesso não autorizado. Este app é restrito ao proprietário.")
        st.stop()

    # Load data once, render sidebar once (shared by Vagas and Resumo)
    all_rows = _load_scored_jobs()
    selected_date = _render_sidebar(all_rows)

    tab1, tab2, tab3 = st.tabs(["Vagas", "Resumo", "Busca Manual"])
    with tab1:
        _render_vagas(all_rows, selected_date)
    with tab2:
        _render_resumo(all_rows, selected_date)
    with tab3:
        _render_busca_manual()


if __name__ == "__main__":
    main()
