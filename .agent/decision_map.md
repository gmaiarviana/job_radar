# Decision Map - Job Radar

Este documento mapeia onde cada informação "mora" para evitar duplicação.

| Informação | Localização (Source of Truth) |
| :--- | :--- |
| **Narrativa de Carreira** | `config/career_narrative.md` |
| **Perfil Condensado (Scoring)** | `config/profile.md` |
| **Parâmetros de Busca (Pesos)** | `config/search.yaml` |
| **Prompt de Scoring** | `src/score.py` |
| **Prompt de Geração (CV/CL)** | `src/generate.py` |
| **Voz do Usuário (Templates)** | `config/cover_letter_template.md` & `config/resume_base.md` |
| **Pipeline de Automação** | `.github/workflows/daily.yml` |
| **Status do Projeto** | `ROADMAP.md` |
| **Design Técnico** | `ARCHITECTURE.md` |
| **Como fazer commit (sintaxe shell)** | `.agent/workflows/commit.md` |

> [!TIP]
> **Antigravity**: Antes de assumir um valor ou prompt, consulte o arquivo mapeado acima.
