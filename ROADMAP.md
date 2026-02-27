# ROADMAP - Job Radar

📡 **Status:** Pipeline completo (fetch → filter → score). Épico 6 concluído. Próximo: Épico 7 (UX completa).

> **Filosofia:** POC → Protótipo → MVP. Validar cada etapa antes de avançar. Qualidade antes de volume.

---

## ✅ Concluído

**Épicos 1–4:** Pipeline fetch multi-fonte, schema único, dedup, filtros (título + localização), scoring em dois estágios, GitHub Actions diário, seed ATS, eval (`src/eval/`), paths (`src/paths.py`). Ver [ARCHITECTURE.md](ARCHITECTURE.md).

**Épico 5 — Qualidade de scoring:** Prompt em 2 chamadas (analyze_job → compute_ceiling → score_with_analysis), validado no seed; ceiling em Python; arquivos scored por data/hora; filter/score com exclusão de `*_discarded.json` e `seed_*`. Pipeline end-to-end validado (fetch → filter → score).

**Épico 6 — UI Funcional Mínima:** Streamlit com duas abas. Aba "Vagas": tabela unificada (pipeline + manuais) com score, veredito (APLICAR/AVALIAR/PULAR), badge de fonte, filtro por data, expand com análise completa. Aba "LinkedIn": links de busca + paste-and-score (analyze_job → compute_ceiling → score_with_analysis) com persistência em `data/scored/manual_*.json` e `seen_jobs.json`. Config: `config/linkedin_searches.yaml`.

---

## 📍 Próximos Épicos

### ÉPICO 7: UX Completa

**Objetivo:** Polimento da UI — feedback, histórico consolidado, integração com geração de materiais.

**Dependência:** Épico 6 rodando.

**Critério de aceite:** Jornada completa funcional — ver vagas → feedback → gerar materiais → download.

#### 7.1 Feedback por vaga (👍/👎)

- Botões em cada card (manual e automático)
- Salva em `data/feedback/YYYY-MM-DD.json`

#### 7.2 Histórico com contadores

- Lista de dias anteriores na sidebar
- Contadores: vagas vistas, feedbacks dados, avaliações manuais

#### 7.3 Botão "Preparar aplicação" → generate.py

- Em cada card com score ≥ 70
- Loading → preview → download PDF

---

### ÉPICO 8: Expansão de Coleta

**Objetivo:** Aumentar volume e qualidade das vagas coletadas.

**Dependência:** Épico 6 rodando (UX funcional, feedback como sinal de qualidade).

#### 8.1 Análise exploratória de títulos e expansão de busca

- Análise exploratória de títulos (ex.: via NotebookLM): extrair títulos únicos do seed por fonte; identificar títulos relevantes fora do filtro atual (ex: "Product Lead", "Associate PM", "Group PM")
- Decisão: expandir `TITLE_KEYWORDS` nos coletores ou centralizar em `config/search.yaml`

#### 8.2 Novos conectores

- Identificar boards relevantes ainda não cobertos
- Priorizar fontes com vagas LATAM/Worldwide confirmadas

#### 8.3 Revalidar empresas comentadas no companies.yaml

- Empresas com "404 no seed" — revalidar slugs ou ATS atual

---

### ÉPICO 9: Pipeline Automatizado Estável

**Objetivo:** Fetch + Score rodando de forma confiável via GitHub Actions.

**Dependência:** Épicos 5 e 6 concluídos.

**Critério de aceite:** 5 dias consecutivos sem intervenção. Cobertura ≥ 10 vagas novas/dia.

#### 9.1 Tratamento de falhas por coletor

- Se uma fonte falhar, pipeline continua com as demais
- Retry 1x por fonte se timeout
- Commit de log de erro se todas falharem

---

### ÉPICO 10: Geração de Materiais

**Objetivo:** Gerar currículo e cover letter personalizados por vaga.

**Dependência:** Épico 7 concluído (botão na UI) e scoring estável por ≥ 2 semanas.

**Critério de aceite:** Materiais gerados para 5 vagas reais. ≥ 4 prontos para enviar com mínima edição.

#### 10.1 Currículo base modular (`config/resume_base.md`)
#### 10.2 Template de cover letter (`config/cover_letter_template.md`)
#### 10.3 Script generate.py (Claude Sonnet)
#### 10.4 Geração de PDF (weasyprint)

---

### ÉPICO 11: Feedback Loop

**Objetivo:** Feedback do usuário alimenta o scoring.

**Dependência:** Épicos 7 e 9 rodando com dados de ≥ 2 semanas.

**Critério de aceite:** Scoring melhora visivelmente após 2 semanas de feedback.

#### 11.1 Agregação de feedback (padrões de aceite/rejeição)
#### 11.2 Feedback no prompt de scoring (contexto extra)
#### 11.3 Persistência no repositório (Actions lê feedback)

---

Backlog, itens postergados e ideias futuras → [docs/governance/backlog.md](docs/governance/backlog.md)

---

**Última atualização:** Fev 2026
