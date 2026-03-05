# Arquitetura - Job Radar

Este documento descreve o design técnico, a organização do sistema e as decisões arquiteturais. Serve como a fonte da verdade para o **estado atual** do projeto. Status e próximos passos: [ROADMAP.md](ROADMAP.md).

## 🏗️ Visão Geral

O sistema é dividido em um pipeline de dados (nuvem/Actions), uma interface de consumo (local/Streamlit) e um dashboard estático (GitHub Pages).

### Mapa do Sistema

```mermaid
graph TD
    A[GitHub Actions - Cloud] -->|Cron/Manual| B[fetch.py - Pipeline multi-fonte]
    B -->|coletores| B1[OpenAI Search + Remotive + We Work Remotely + Jobicy + Remote OK + Get on Board + Himalayas + Working Nomads + JobsCollider + Greenhouse + Lever + Ashby]
    B1 -->|raw| B2[job_schema + fetch_pipeline]
    B2 -->|data/raw/| B3[filter.py - Hard filters]
    B3 -->|title + location + quality guard| B4[data/filtered/]
    B4 -->|filtered JSON| C[score.py Stage 1 - Eliminatórios]
    C -->|surviving jobs| D[score.py Stage 2 - Deep Score]
    D -->|scored JSON| E[git commit/push]
    E -->|data/jobs.json → docs/data/| J[GitHub Pages - Dashboard]

    F[Streamlit - Local] -->|git pull| E
    F2[Streamlit Cloud] -->|git clone| E
    E -->|Visualiza + Scoring| F2
    E -->|Visualiza| F[app.py]
    F -->|Clique: Preparar| G[generate.py - Claude Sonnet]
    G -->|PDFs| H[data/output/]
    F -->|Feedback| I[data/feedback/ JSON]
```

### Componentes e Responsabilidades

| Componente | Script / Módulo | Modelo/Motor | Papel |
| :--- | :--- | :--- | :--- |
| **Search** | `src/fetch.py` (CLI) + `job_schema.py` + `fetch_pipeline.py` + `seen_jobs.py` + `collectors/*` | OpenAI Search, Remotive, We Work Remotely, Jobicy, Remote OK, Get on Board, Himalayas, Working Nomads, JobsCollider, Greenhouse, Lever, Ashby (Épicos 3.2–3.4, 7.2, 7.7) | Orquestra coletores, normaliza para schema único, dedupe persistente (`data/seen_jobs.json`) + throttle 50 novos/run, quality guard, métricas de cobertura no JSON, grava em `RAW_DIR` (`src/paths.py`). Janela de coleta de 7 dias nos coletores com filtro de recência (Remotive, Jobicy, Remote OK, Get on Board, Himalayas, Working Nomads, JobsCollider); fontes sem recorte client-side (WWR feed master, ATS) trazem todas as vagas abertas. |
| **Paths** | `src/paths.py` | — | Single source of truth para diretórios do projeto. Lê output de search.yaml, expõe RAW_DIR, FILTERED_DIR, SCORED_DIR, etc. como Path objects. |
| **Filter** | `src/filter.py` | — | Hard filters gratuitos: title (exclude_title_keywords de search.yaml) + location (blocklist + allowlist) + quality guard (JD/título/empresa). Lê `data/raw/`, grava `data/filtered/` (mesmo nome; jd_full intacto). CLI: `--input` ou `--date`. `data/filtered/` no .gitignore. |
| **Score** | `src/score.py` | Claude Haiku | Lê de `data/filtered/`. Eliminatórios em batch com payload completo (title, company, location, jd_full). Deep Scoring individual com JD truncado a 3000 chars no prompt (não no armazenamento). Chamada 1 (analyze_job) retorna `penalties` como dict de bools (seniority_gap, domain_gap_core); compute_ceiling calcula teto em Python; Chamada 2 (score_with_analysis) recebe análise + ceiling e atribui score final (early return se ceiling ≤ 50, senão Haiku com teto explícito). main() executa esse pipeline por vaga; output por vaga inclui score_ceiling, ceiling_reason, core_requirements, seniority_comparison. Contra `config/profile.md`. |
| **Interface** | `app.py` | Streamlit | Três abas: **Vagas** (tabela unificada de `data/scored/`: pipeline + manual_*.json; filtro por data; cards com score, veredito APLICAR/AVALIAR/PULAR, badge de coletor real, salário, link; expander "Detalhes" sem ceiling, com veredito no topo, botões "Copiar JD"/"Copiar Relatório" via `st.code`), **Resumo** (filtra apenas APLICAR score ≥ 85, ordenado por score desc, filtro de data) e **Busca Manual** (links de `config/manual_searches.yaml` + paste-and-score com formulário empresa→título→JD→url→localização; botão "Avaliar outra vaga" para reset; salva em `data/scored/manual_YYYY-MM-DD_HHMMSS.json`; atualiza `seen_jobs.json`). Funciona local e em Streamlit Cloud. Depende de `src/score.py`, `src/job_schema.py`, `src/seen_jobs.py`, `src/paths.py`. |
| **Writer** | `src/generate.py`| Claude Sonnet | Redação de alta qualidade para CV e Cover Letter. |
| **Notifier** | `src/notify.py` | SMTP | Alertas imediatos para `PERFECT_MATCH` (score > 95). |
| **GitHub API** | `src/github_api.py` | GitHub Contents API | Persistência remota via API: `get_file(path)` retorna conteúdo + SHA; `put_file(path, content, sha)` cria ou atualiza arquivo no repo. Usado pelo `app.py` no Streamlit Cloud para gravar `manual_*.json` e `seen_jobs.json` diretamente no repositório. Fallback: filesystem local quando token ausente. |
| **Frontend Data** | `src/build_frontend_data.py` | — | Consolida `data/scored/` em `data/jobs.json`. O workflow copia para `docs/data/jobs.json` para o GitHub Pages servir. Filtra últimos 14 dias, ordena por data e score. Roda no pipeline diário (Actions) e como CLI. |
| **Eval** | `src/eval/build_gabarito.py`, `eval_eliminatorios.py`, `test_scoring.py`, `validate_scoring_pipeline.py` | — | Infraestrutura de avaliação: gabarito machine-readable, eval parametrizado por modelo; testes de scoring (compute_ceiling); validação do pipeline de 2 chamadas no seed (5.1.5) via `--seed <path>`. |

### Decisões Técnicas (Rationale)

| Decisão | Escolha | Motivo |
| :--- | :--- | :--- |
| **Busca de vagas** | Pipeline multi-fonte: OpenAI Search, Remotive, We Work Remotely, Jobicy (Épico 2); dedup persistente + throttle (2.7). | Coletores independentes; schema único; dedupe cross-fonte; `seen_jobs.json` evita reprocessar vagas entre runs; throttle limita a 20 novos JDs/run (preparado para ATS). |
| **Scoring** | Claude Haiku | Rápido e barato para análise de texto longo. |
| **Geração de materiais** | Claude Sonnet | Escrita superior e tom profissional. |
| **Interface** | Streamlit Local | Agilidade no desenvolvimento e custo zero de hospedagem. |
| **Pipeline** | GitHub Actions | Gratuito, automatizado e confiável (nuvem). |
| **Persistência** | JSON (Data-as-Code) | Simplicidade; controle de versão serve como banco de dados. |
| **Eval / Gabarito** | Gabarito JSON + script parametrizado por modelo | Permite medir impacto de cada mudança (filtro, prompt, modelo) de forma repetível. Reutilizável para scoring (Épico 5). |

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
│   │   ├── remotive.py          # API Remotive (product, project-management; janela 7d)
│   │   ├── weworkremotely.py    # RSS We Work Remotely (feed master; filtro PM/TPM por título)
│   │   ├── jobicy.py            # API Jobicy (industry=product; janela 7d)
│   │   ├── remoteok.py          # API Remote OK (Épico 7.2; tags/position PM; janela 7d; Source: Remote OK)
│   │   ├── getonboard.py        # API Get on Board (Épico 7.2; LATAM, product manager remote; paginação até 5 páginas)
│   │   ├── himalayas.py         # API Himalayas (Épico 7.7; JSON paginado até 5 páginas; PM/TPM; janela 7d)
│   │   ├── workingnomads.py     # API Working Nomads (Épico 7.7; JSON sem paginação; PM/TPM; janela 7d)
│   │   ├── jobscollider.py      # RSS JobsCollider (Épico 7.7; product + project management; PM/TPM; janela 7d)
│   │   ├── greenhouse.py       # Greenhouse Job Board API (Épico 3.2; companies.yaml ats=greenhouse)
│   │   ├── lever.py            # Lever Postings API (Épico 3.3; companies.yaml ats=lever)
│   │   ├── ashby.py            # Ashby Job Board API (Épico 3.4; companies.yaml ats=ashby; POST)
│   │   └── openai_search.py    # OpenAI gpt-4o-mini web search
│   ├── github_api.py            # Persistência remota via GitHub Contents API (GET/PUT)
│   ├── build_frontend_data.py   # Consolida scored → data/jobs.json (workflow copia para docs/data/)
│   ├── filter.py                # Hard filters (location + quality); raw → filtered
│   ├── score.py                 # Scoring via Claude Haiku (lê filtered)
│   ├── generate.py              # Writer via Claude Sonnet
│   ├── notify.py                # Alertas SMTP
│   ├── eval/                    # Scripts de avaliação e benchmarking
│   │   ├── __init__.py
│   │   ├── build_gabarito.py    # Gera gabarito machine-readable a partir de lista curada
│   │   ├── eval_eliminatorios.py  # Eval reutilizável: hard filters + LLM vs gabarito
│   │   └── test_scoring.py     # Testes de compute_ceiling (4 cenários); rodar: python src/eval/test_scoring.py
├── config/
│   ├── career_narrative.md      # Fonte de verdade da carreira
│   ├── profile.md               # Perfil condensado para LLMs
│   ├── resume_base.md           # Templates modulares de currículo
│   ├── search.yaml              # Parâmetros de busca e pesos
│   └── manual_searches.yaml     # Links de busca manual (UI: aba Busca Manual)
├── data/
│   ├── seen_jobs.json           # Dedup persistente (id_hash → first_seen, source, title, company); commitado pelo Actions
│   ├── jobs.json                # Consolidado para frontend (build_frontend_data.py); workflow copia para docs/data/
│   ├── raw/                     # JSONs brutos (YYYY-MM-DD_HHMMSS.json); inclui "coverage" com métricas por etapa
│   ├── filtered/                 # JSONs após hard filters (mesmo nome do raw); .gitignore
│   ├── scored/                  # JSONs pontuados (YYYY-MM-DD_HHMMSS.json = data/hora da execução; lote em source_file)
│   ├── feedback/                # Feedback 👍/👎 (local)
│   └── output/                  # PDFs gerados
├── docs/
│   ├── index.html               # Dashboard GitHub Pages (HTML+CSS+JS inline; fetch em data/jobs.json)
│   └── data/
│       └── jobs.json            # Cópia de data/jobs.json para o Pages servir (gerada no workflow)
└── .github/workflows/
    └── daily.yml                # Pipeline de automação (Cron)
```

## ⚙️ Infraestrutura e Ambiente

- **Linguagem**: Python 3.11+
- **APIs**: OpenAI (Search Preview), Remotive (pública, sem key), We Work Remotely (RSS público), Himalayas (pública, sem key), Working Nomads (pública, sem key), JobsCollider (RSS público), Anthropic (Claude).
- **Ambiente**: Produção simulada via GitHub Actions; Consumo via Streamlit local. Usar **venv** para desenvolvimento e validação (`python -m venv .venv` ou `venv`).
- **Streamlit Cloud**: App hospedado em share.streamlit.io. Secrets via `st.secrets` (bridge para `os.environ` no `app.py`). Filesystem efêmero — persistência de scoring manual via GitHub Contents API (`src/github_api.py`) quando `GITHUB_TOKEN` disponível; fallback para filesystem local. Autenticação via Google OAuth ("Viewer authentication" no painel do Streamlit Cloud) com verificação de email autorizado (`AUTHORIZED_EMAIL`). Repo clonado automaticamente; `data/scored/` commitado pelo Actions fica disponível.
- **GitHub Pages**: Dashboard read-only em `docs/` (source: branch `main`, pasta `/docs/`). `build_frontend_data.py` gera `data/jobs.json`; o workflow copia para `docs/data/jobs.json`; `docs/index.html` consome via fetch em `data/jobs.json`.
- **Segurança**: Chaves de API via `.env` (local) e Secrets (GitHub).

---

## 📋 Notas de desenvolvimento

- **Venv:** Sempre rodar com ambiente virtual e `pip install -r requirements.txt` antes de validar; evita `ModuleNotFoundError` em máquinas novas.
- **Windows / encoding:** O console (cp1252) pode gerar `UnicodeEncodeError` em logs com emoji. Em `fetch.py` o stdout/stderr é forçado para UTF-8 quando necessário; em novos scripts CLI, repetir o padrão ou evitar emojis.
- **Testes:** O projeto ainda não tem suíte automatizada (pytest). Recomenda-se adicionar smoke test (`python src/fetch.py --dry-run`) ou testes unitários para `job_schema` e pipeline antes de escalar novos coletores.
 - **Streamlit Cloud / secrets:** O `app.py` inclui bridge que copia `st.secrets` para `os.environ` na inicialização. Funciona tanto local (`.env` via `load_dotenv`) quanto em cloud (`st.secrets`). Se adicionar nova env var, incluir no bridge e no `.streamlit/secrets.toml.example`.

---
**Última atualização:** Mar 2026


