# Arquitetura - Job Radar

Este documento descreve o design técnico, a organização do sistema e as decisões arquiteturais. Serve como a fonte da verdade para o **estado atual** do projeto. Status e próximos passos: [ROADMAP.md](ROADMAP.md).

## 🏗️ Visão Geral

O sistema é dividido em um pipeline de dados (nuvem/Actions) e uma interface de consumo (local/Streamlit).

### Mapa do Sistema

```mermaid
graph TD
    A[GitHub Actions - Cloud] -->|Cron/Manual| B[fetch.py - Pipeline multi-fonte]
    B -->|coletores| B1[OpenAI Search + Remotive + We Work Remotely + Jobicy + Greenhouse + Lever + Ashby]
    B1 -->|raw| B2[job_schema + fetch_pipeline]
    B2 -->|data/raw/| B3[filter.py - Hard filters]
    B3 -->|location + quality guard| B4[data/filtered/]
    B4 -->|filtered JSON| C[score.py Stage 1 - Eliminatórios]
    C -->|surviving jobs| D[score.py Stage 2 - Deep Score]
    D -->|scored JSON| E[git commit/push]
    
    F[Streamlit - Local] -->|git pull| E
    E -->|Visualiza| F[app.py]
    F -->|Clique: Preparar| G[generate.py - Claude Sonnet]
    G -->|PDFs| H[data/output/]
    F -->|Feedback| I[data/feedback/ JSON]
```

### Componentes e Responsabilidades

| Componente | Script / Módulo | Modelo/Motor | Papel |
| :--- | :--- | :--- | :--- |
| **Search** | `src/fetch.py` (CLI) + `job_schema.py` + `fetch_pipeline.py` + `seen_jobs.py` + `collectors/*` | OpenAI Search, Remotive, We Work Remotely, Jobicy, Greenhouse, Lever, Ashby (Épicos 3.2–3.4) | Orquestra coletores, normaliza para schema único, dedupe persistente (`data/seen_jobs.json`) + throttle 20 novos/run, quality guard, métricas de cobertura no JSON, grava em `data/raw/`. |
| **Filter** | `src/filter.py` | — | Hard filters gratuitos: location (expandido) + quality guard (JD/título/empresa). Lê `data/raw/`, grava `data/filtered/` (mesmo nome; jd_full intacto). CLI: `--input` ou `--date`. `data/filtered/` no .gitignore. |
| **Score** | `src/score.py` | Claude Haiku | Lê de `data/filtered/`. Eliminatórios em batch com payload reduzido (title, company, location, jd_snippet 300 chars). Deep Scoring individual com JD truncado a 3000 chars no prompt (não no armazenamento). Contra `config/profile.md`. |
| **Interface** | `app.py` | Streamlit | UI para revisão, feedback e acionamento de geração. |
| **Writer** | `src/generate.py`| Claude Sonnet | Redação de alta qualidade para CV e Cover Letter. |
| **Notifier** | `src/notify.py` | SMTP | Alertas imediatos para `PERFECT_MATCH` (score > 95). |

### Decisões Técnicas (Rationale)

| Decisão | Escolha | Motivo |
| :--- | :--- | :--- |
| **Busca de vagas** | Pipeline multi-fonte: OpenAI Search, Remotive, We Work Remotely, Jobicy (Épico 2); dedup persistente + throttle (2.7). | Coletores independentes; schema único; dedupe cross-fonte; `seen_jobs.json` evita reprocessar vagas entre runs; throttle limita a 20 novos JDs/run (preparado para ATS). |
| **Scoring** | Claude Haiku | Rápido e barato para análise de texto longo. |
| **Geração de materiais** | Claude Sonnet | Escrita superior e tom profissional. |
| **Interface** | Streamlit Local | Agilidade no desenvolvimento e custo zero de hospedagem. |
| **Pipeline** | GitHub Actions | Gratuito, automatizado e confiável (nuvem). |
| **Persistência** | JSON (Data-as-Code) | Simplicidade; controle de versão serve como banco de dados. |

---

## 📂 Estrutura do Projeto

```text
job-radar/
├── app.py                       # Interface Streamlit principal
├── src/
│   ├── fetch.py                 # CLI: orquestra coletores e grava raw
│   ├── job_schema.py            # Schema único + make_id_hash, normalize_job
│   ├── fetch_pipeline.py        # run_pipeline, apply_seen_jobs_filter, remove_duplicates, filter_old_jobs, apply_quality_guard, load_config
│   ├── seen_jobs.py             # load_seen, is_seen, mark_seen, save_seen (dedup persistente; único acesso a data/seen_jobs.json)
│   ├── collectors/              # Um módulo por fonte de vagas
│   │   ├── __init__.py
│   │   ├── remotive.py          # API Remotive (product, project-management; 48h)
│   │   ├── weworkremotely.py    # RSS We Work Remotely (management/finance; filtro PM/TPM)
│   │   ├── jobicy.py            # API Jobicy (industry=product; 48h)
│   │   ├── greenhouse.py       # Greenhouse Job Board API (Épico 3.2; companies.yaml ats=greenhouse)
│   │   ├── lever.py            # Lever Postings API (Épico 3.3; companies.yaml ats=lever)
│   │   ├── ashby.py            # Ashby Job Board API (Épico 3.4; companies.yaml ats=ashby; POST)
│   │   └── openai_search.py    # OpenAI gpt-4o-mini web search
│   ├── filter.py                # Hard filters (location + quality); raw → filtered
│   ├── score.py                 # Scoring via Claude Haiku (lê filtered)
│   ├── generate.py              # Writer via Claude Sonnet
│   └── notify.py                # Alertas SMTP
├── config/
│   ├── career_narrative.md      # Fonte de verdade da carreira
│   ├── profile.md               # Perfil condensado para LLMs
│   ├── resume_base.md           # Templates modulares de currículo
│   └── search.yaml              # Parâmetros de busca e pesos
├── data/
│   ├── seen_jobs.json           # Dedup persistente (id_hash → first_seen, source, title, company); commitado pelo Actions
│   ├── raw/                     # JSONs brutos (YYYY-MM-DD_HHMMSS.json); inclui "coverage" com métricas por etapa
│   ├── filtered/                 # JSONs após hard filters (mesmo nome do raw); .gitignore
│   ├── scored/                  # JSONs pontuados (YYYY-MM-DD_HHMMSS.json)
│   ├── feedback/                # Feedback 👍/👎 (local)
│   └── output/                  # PDFs gerados
└── .github/workflows/
    └── daily.yml                # Pipeline de automação (Cron)
```

## ⚙️ Infraestrutura e Ambiente

- **Linguagem**: Python 3.11+
- **APIs**: OpenAI (Search Preview), Remotive (pública, sem key), We Work Remotely (RSS público), Anthropic (Claude).
- **Ambiente**: Produção simulada via GitHub Actions; Consumo via Streamlit local. Usar **venv** para desenvolvimento e validação (`python -m venv .venv` ou `venv`).
- **Segurança**: Chaves de API via `.env` (local) e Secrets (GitHub).

---

## 📋 Notas de desenvolvimento

- **Venv:** Sempre rodar com ambiente virtual e `pip install -r requirements.txt` antes de validar; evita `ModuleNotFoundError` em máquinas novas.
- **Windows / encoding:** O console (cp1252) pode gerar `UnicodeEncodeError` em logs com emoji. Em `fetch.py` o stdout/stderr é forçado para UTF-8 quando necessário; em novos scripts CLI, repetir o padrão ou evitar emojis.
- **Testes:** O projeto ainda não tem suíte automatizada (pytest). Recomenda-se adicionar smoke test (`python src/fetch.py --dry-run`) ou testes unitários para `job_schema` e pipeline antes de escalar novos coletores.

---
**Última atualização:** 24 de Fevereiro de 2026


