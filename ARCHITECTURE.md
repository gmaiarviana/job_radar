# Arquitetura - Job Radar

Este documento descreve o design técnico e a organização do sistema.

## 🏗️ Visão Geral

O sistema é dividido em um pipeline de dados (nuvem/Actions) e uma interface de consumo (local/Streamlit).

### Fluxo de Dados
1. **Fetch:** Busca vagas via OpenAI Search (`src/fetch.py`).
2. **Score:** Pontua vagas contra o perfil (`src/score.py`).
3. **Notify:** Alerta sobre matches perfeitos (`src/notify.py`).
4. **App:** Interface para revisão e geração de materiais (`app.py`).
5. **Generate:** Cria currículos/cover letters personalizados (`src/generate.py`).

### Organização de Diretórios
- `config/`: Fontes de verdade (Perfil, Narrativa, Templates).
- `src/`: Lógica principal do pipeline e ferramentas.
- `data/`: Três camadas de dados (`raw`, `scored`, `feedback`) + `output` de PDFs.
- `.github/workflows/`: Automação e cronogramas.

### Decisões Técnicas
- **Storage:** JSON local e controle de versão (Git) para persistência simples.
- **LLMs:** Multi-model pipeline (GPT-4o para busca, Claude Haiku para score, Claude Sonnet para escrita).
- **Interface:** Streamlit para prototipagem rápida e funcionalidade local.

---
**Última atualização:** 22 de Fevereiro de 2026
