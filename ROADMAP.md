# ROADMAP - Job Radar

📡 **Status:** Pipeline completo (fetch → filter → score). Épico 5 e Épico 6.1–6.3 (UI mínima) concluídos. Próximo: polimento da UI (Épico 7) ou itens pendentes do 6.

> **Filosofia:** POC → Protótipo → MVP. Validar cada etapa antes de avançar. Qualidade antes de volume.

---

## ✅ Concluído

**Épicos 1–4:** Pipeline fetch multi-fonte, schema único, dedup, filtros (título + localização), scoring em dois estágios, GitHub Actions diário, seed ATS, eval (`src/eval/`), paths (`src/paths.py`). Ver [ARCHITECTURE.md](ARCHITECTURE.md).

**Épico 5 — Qualidade de scoring:** Prompt em 2 chamadas (analyze_job → compute_ceiling → score_with_analysis), validado no seed; ceiling em Python; arquivos scored por data/hora; filter/score com exclusão de `*_discarded.json` e `seed_*`. Pipeline end-to-end validado (fetch → filter → score).

**Épico 6.1–6.3 — UI funcional mínima:** 6.1 `config/linkedin_searches.yaml` com buscas LinkedIn; 6.2 Página Vagas (tabela unificada de `data/scored/`, filtro por data, cards com score/fonte/link); 6.3 Página LinkedIn (links clicáveis + formulário paste-and-score, resultado na tela, persistência em `manual_*.json` e `seen_jobs.json`).

---

## 📍 Próximos Épicos

### ÉPICO 6: UI Funcional Mínima ✅ 6.1–6.3 concluídos

**Objetivo:** Interface com valor imediato — monitorar LinkedIn, avaliar vagas manualmente, visualizar resultados do pipeline automático.

**Dependência:** Épico 5 concluído.

**Critério de aceite:** Usuário consegue: (1) abrir links de busca do LinkedIn direto da UI, (2) colar JD e ver score + gaps, (3) voltar a avaliações salvas, (4) ver vagas scored do pipeline automático.

#### 6.1 Links de busca na sidebar

- `config/linkedin_searches.yaml` com nome + URL + camada (diário / periódico / semanal)
- Sidebar no Streamlit com links clicáveis (abrem no browser)
- Agrupados por camada de prioridade
- Conteúdo dos links: definir na próxima sessão de planejamento

#### 6.2 Paste-and-score

- Formulário na UI:
  - Título da vaga (obrigatório)
  - Empresa (obrigatório)
  - JD — textarea (obrigatório)
  - URL (opcional)
  - Localização (opcional)
  - Salário (opcional)
- Submit → `normalize_job(raw, source="manual")` → `analyze_job` → `compute_ceiling` → `score_with_analysis`
- Resultado na tela: score (badge colorido), ceiling, ceiling_reason, core_requirements com evidências, seniority_comparison, main_gap
- Loading indicator durante scoring (2 chamadas LLM)

#### 6.3 Persistência de avaliações manuais

- Salva resultado em `data/scored/manual_YYYY-MM-DD_HHMMSS.json`
  - Mesmo formato dos scored automáticos (`source: "manual"`)
  - 1 job por arquivo (cada submit gera um arquivo)
- Aba/seção "Minhas avaliações":
  - Lista todos `manual_*.json` de `data/scored/`, ordenados por data (mais recente primeiro)
  - Card: título, empresa, score (badge), data da avaliação, link para URL original
  - Clique expande: gaps, core_requirements, justification, ceiling_reason

#### 6.4 Tabela de vagas scored (pipeline automático)

- Leitura de `data/scored/` excluindo `manual_*.json`
- Lista ordenada por score (maior primeiro)
- Card: título, empresa, score (badge colorido), localização, link direto
- Cores: verde (≥ 85), amarelo (70–84), cinza (< 70)
- Seletor de data para filtrar por dia

---

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
