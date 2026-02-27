"""
app.py — Interface Streamlit do Job Radar.

Épico 6 | UI funcional mínima: tabela unificada de vagas + LinkedIn paste-and-score.

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

load_dotenv()

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
    """Extrai YYYY-MM-DD do nome do arquivo (ex: 2026-02-24_120958.json ou manual_2026-02-24_120958.json)."""
    base = name.replace(".json", "")
    if base.startswith("manual_"):
        base = base[7:]
    match = re.match(r"(\d{4}-\d{2}-\d{2})", base)
    return match.group(1) if match else None


def _load_scored_jobs() -> list[dict]:
    """
    Lê todos os .json de data/scored/ (exceto *_discarded.json e seed_*).
    Retorna lista unificada de jobs com metadados: job (dict), file_date (str), source ("pipeline" | "linkedin").
    """
    if not SCORED_DIR.exists():
        return []

    rows: list[dict] = []
    for path in SCORED_DIR.glob("*.json"):
        name = path.name
        if "_discarded" in name or name.startswith("seed_"):
            continue
        file_date = _date_from_filename(name)
        source = "linkedin" if name.startswith("manual_") else "pipeline"

        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue

        job_list = data.get("jobs") or data.get("scored_jobs") or []
        for job in job_list:
            if isinstance(job, dict):
                rows.append({
                    "job": job,
                    "file_date": file_date or "",
                    "source": job.get("source", source),
                })
    return rows


def _score_badge_style(score: int) -> tuple[str, str]:
    """(background, text_color): verde ≥85, amarelo 70–84, cinza <70."""
    if score >= 85:
        return ("#2e7d32", "white")   # verde
    if score >= 70:
        return ("#f9a825", "black")   # amarelo
    return ("#616161", "white")       # cinza


# --- Sidebar: seletor de data ---
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
    )
    return selected


# --- Página 1: Vagas ---
def _render_vagas():
    all_rows = _load_scored_jobs()
    selected_date = _render_sidebar(all_rows)

    if selected_date is not None:
        rows = [r for r in all_rows if r["file_date"] == selected_date]
    else:
        rows = all_rows

    jobs_with_meta = sorted(
        rows,
        key=lambda r: (r["job"].get("score") is None, -(r["job"].get("score") or 0)),
    )

    if not jobs_with_meta:
        st.info("Nenhuma vaga scored encontrada. Execute o pipeline (`python src/fetch.py` e `python src/score.py`) ou use a aba LinkedIn para avaliar vagas manualmente.")
        return

    for item in jobs_with_meta:
        job = item["job"]
        source = item["source"]
        score = job.get("score")
        title = job.get("title") or "(Sem título)"
        company = job.get("company") or "(Sem empresa)"
        url = job.get("url") or ""

        score_label = str(score) if score is not None else "—"
        bg, fg = _score_badge_style(score) if score is not None else ("#616161", "white")

        # Card: compacto (container) + expandido (expander)
        with st.container():
            c1, c2, c3, c4, c5 = st.columns([3, 2, 1, 1, 1])
            with c1:
                st.markdown(f"**{title}**")
            with c2:
                st.markdown(company)
            with c3:
                st.markdown(f'<span style="background:{bg};color:{fg};padding:2px 8px;border-radius:4px;">{score_label}</span>', unsafe_allow_html=True)
            with c4:
                st.caption(source)
            with c5:
                if url:
                    st.link_button("Link", url, use_container_width=True)
                else:
                    st.caption("—")

        with st.expander("Ver detalhes (ceiling, requisitos, seniority, gap)", expanded=False):
            # Expandido: ceiling, ceiling_reason, core_requirements, seniority_comparison, main_gap, justification, link
            if job.get("score_ceiling") is not None:
                st.markdown(f"**Teto:** {job.get('score_ceiling')}")
            if job.get("ceiling_reason"):
                st.markdown(f"**Motivo do teto:** {job['ceiling_reason']}")

            core_req = job.get("core_requirements")
            if core_req and isinstance(core_req, list):
                st.markdown("**Requisitos principais:**")
                for req in core_req:
                    if isinstance(req, dict):
                        rq = req.get("requirement") or req.get("requirement_text") or "(requisito)"
                        has_ev = req.get("has_evidence", True)
                        ev = req.get("evidence") or ""
                        st.markdown(f"- {rq} — {'✓' if has_ev else '✗'} {ev}")
                    else:
                        st.markdown(f"- {req}")
            elif job.get("evidence"):
                st.markdown("**Evidências:**")
                st.markdown(job["evidence"])

            sr = job.get("seniority_comparison")
            if sr and isinstance(sr, dict):
                st.markdown("**Seniority:**")
                st.markdown(f"- JD pede: {sr.get('jd_asks', '—')}")
                st.markdown(f"- Candidato tem: {sr.get('candidate_has', '—')}")
                if sr.get("gap"):
                    st.markdown(f"- Gap: {sr['gap']}")

            if job.get("main_gap"):
                st.markdown(f"**Principal gap:** {job['main_gap']}")
            if job.get("justification"):
                st.markdown(f"**Justificativa:** {job['justification']}")

            if url:
                st.markdown(f"**Link:** [Abrir vaga]({url})")


# --- Helpers: LinkedIn (links + scoring) ---
def _load_linkedin_searches() -> list[dict]:
    """Carrega config/linkedin_searches.yaml; retorna lista de {name, url}."""
    path = Path("config/linkedin_searches.yaml")
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
    result["source"] = "linkedin"
    return result, None


def _render_job_result_detail(job: dict) -> None:
    """Exibe score (badge), ceiling, core_requirements, seniority, main_gap, justification."""
    score = job.get("score")
    score_label = str(score) if score is not None else "—"
    bg, fg = _score_badge_style(score) if score is not None else ("#616161", "white")
    st.markdown(f'**Score:** <span style="background:{bg};color:{fg};padding:4px 10px;border-radius:4px;">{score_label}</span>', unsafe_allow_html=True)
    if job.get("score_ceiling") is not None:
        st.markdown(f"**Teto:** {job.get('score_ceiling')} — {job.get('ceiling_reason', '')}")
    core_req = job.get("core_requirements")
    if core_req and isinstance(core_req, list):
        st.markdown("**Requisitos principais:**")
        for req in core_req:
            if isinstance(req, dict):
                rq = req.get("requirement") or req.get("requirement_text") or "(requisito)"
                has_ev = req.get("has_evidence", True)
                ev = req.get("evidence") or ""
                st.markdown(f"- {rq} — {'✓' if has_ev else '✗'} {ev}")
            else:
                st.markdown(f"- {req}")
    sr = job.get("seniority_comparison")
    if sr and isinstance(sr, dict):
        st.markdown("**Seniority:**")
        st.markdown(f"- JD pede: {sr.get('jd_asks', '—')}")
        st.markdown(f"- Candidato tem: {sr.get('candidate_has', '—')}")
        if sr.get("gap"):
            st.markdown(f"- Gap: {sr['gap']}")
    if job.get("main_gap"):
        st.markdown(f"**Principal gap:** {job['main_gap']}")
    if job.get("justification"):
        st.markdown(f"**Justificativa:** {job['justification']}")


# --- Página 2: LinkedIn — Links + Paste-and-score ---
def _render_linkedin():
    # Seção 1: Links LinkedIn
    searches = _load_linkedin_searches()
    if searches:
        st.subheader("Links de busca (LinkedIn Jobs)")
        cols = st.columns(min(len(searches), 5))
        for i, item in enumerate(searches):
            name = item.get("name") or "Link"
            url = item.get("url") or "#"
            with cols[i % len(cols)]:
                st.markdown(f'<a href="{url}" target="_blank" rel="noopener noreferrer">{name}</a>', unsafe_allow_html=True)
        st.markdown("---")

    # Seção 2: Formulário paste-and-score
    st.subheader("Avaliar vaga (colar JD)")
    with st.form("paste_and_score_form"):
        title = st.text_input("Título da vaga *", placeholder="Ex: Senior Product Manager")
        company = st.text_input("Empresa *", placeholder="Ex: Acme Inc.")
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

    _render_job_result_detail(result)

    # Persistência: manual_*.json + seen_jobs
    ensure_dirs()
    now = datetime.now(timezone.utc)
    ts = now.strftime("%Y-%m-%d_%H%M%S")
    filename = f"manual_{ts}.json"
    out_path = SCORED_DIR / filename

    payload = {
        "scored_at": now.isoformat(),
        "source_file": "manual",
        "summary": {"total_input": 1, "total_scored": 1, "total_top": 1 if (result.get("score") or 0) >= 70 else 0},
        "jobs": [result],
    }
    try:
        out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    except Exception as e:
        st.warning(f"Resultado exibido, mas falha ao salvar arquivo: {e}")
        return

    id_hash = result.get("id_hash") or result.get("id")
    if id_hash:
        try:
            seen = load_seen()
            mark_seen(id_hash, "linkedin", result.get("title", ""), result.get("company", ""), seen)
            save_seen(seen)
        except Exception:
            pass

    st.success("Vaga avaliada e salva!")


# --- Main ---
def main():
    st.title("📡 Job Radar")
    st.caption("Vagas scored do pipeline + manuais (LinkedIn)")

    tab1, tab2 = st.tabs(["Vagas", "LinkedIn"])
    with tab1:
        _render_vagas()
    with tab2:
        _render_linkedin()


if __name__ == "__main__":
    main()
