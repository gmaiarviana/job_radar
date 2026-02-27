# Decision Map - Job Radar

Este documento mapeia onde cada informação "mora" para evitar duplicação.

| Informação | Localização (Source of Truth) |
| :--- | :--- |
| **Narrativa de Carreira** | `config/career_narrative.md` |
| **Perfil Condensado (Scoring)** | `config/profile.md` |
| **Parâmetros de Busca (Pesos)** | `config/search.yaml` |
| **Links de busca (Busca Manual)** | `config/manual_searches.yaml` |
| **Prompt de Scoring** | `src/score.py` |
| **Prompt de Geração (CV/CL)** | `src/generate.py` |
| **Voz do Usuário (Templates)** | `config/cover_letter_template.md` & `config/resume_base.md` |
| **Pipeline de Automação** | `.github/workflows/daily.yml` |
| **Landing Page (GitHub Pages)** | `docs/` |
| **Status do Projeto** | `ROADMAP.md` |
| **Backlog, postergado e ideias futuras** | `docs/governance/backlog.md` |
| **Design Técnico** | `ARCHITECTURE.md` |
| **Processo de refinamento / Governança** | `docs/governance/CONSTITUTION.md` |
| **Avaliação de dados (corpus pesado)** | CONSTITUTION.md §4 (NotebookLM; cópias TXT em `data/raw/copy txt/` e `data/scored/copy txt/`) |
| **Templates e critérios de épicos** | `docs/governance/planning_guidelines.md` |
| **Como fazer commit (sintaxe shell)** | `.agent/workflows/commit.md` |

> [!TIP]
> **Cursor**: Antes de assumir um valor ou prompt, consulte o arquivo mapeado acima.
