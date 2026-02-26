# ROADMAP - Job Radar

📡 **Status:** Pipeline completo (fetch → filter → score). Scoring calibrado (5.1 concluído). Próximo: **Épico 5.2+ → Épico 6 (UI Funcional)**.

> **Filosofia:** POC → Protótipo → MVP. Validar cada etapa antes de avançar. Qualidade antes de volume.

---

## ✅ Concluído

**Épicos 1–4:** Pipeline fetch multi-fonte (Remotive, We Work Remotely, Jobicy, OpenAI Search, Greenhouse, Lever, Ashby), schema único (`job_schema.py`), dedup persistente (`seen_jobs.json`), throttle 20/run, quality guard, hard filters (título + localização em duas camadas: blocklist + allowlist), scoring em dois estágios (eliminatórios batch + deep score via Claude Haiku), GitHub Actions diário, seed ATS (`seed.py`), eval infrastructure (`src/eval/`), paths centralizados (`src/paths.py`). Detalhes em [ARCHITECTURE.md](ARCHITECTURE.md).

**Épico 5.1 — Correção do prompt de scoring:** Pipeline de 2 chamadas (analyze_job → compute_ceiling → score_with_analysis) calibrado e validado 5/5 no seed. Penalties como booleans; ceiling calculado em Python; early return para ceiling ≤ 50 (sem LLM). `score_single_job` removido. Arquivos scored nomeados por data/hora de execução; lote de origem em `source_file`.

---

## 📍 Próximos Épicos

---

### ÉPICO 5: Qualidade de Scoring

**Objetivo:** Garantir que o score reflita fit real.

**Critério de aceite:** Vagas com gap de domínio core recebem score ≤ 60. Vagas Senior sem evidência ≤ 65. Top 5 vagas de maior score fazem sentido em avaliação manual.

#### 5.1 Correção do prompt de scoring ✅ CONCLUÍDO

#### 5.2 Análise exploratória de títulos (via NotebookLM)

- Extrair títulos únicos do seed por fonte
- Identificar títulos relevantes fora do filtro atual (ex: "Product Lead", "Associate PM", "Group PM")
- Decisão: expandir `TITLE_KEYWORDS` nos coletores ou centralizar em `config/search.yaml`

#### 5.3 Validação com avaliação manual

- Avaliar top 5 vagas de maior score
- Comparar avaliação manual com score do sistema
- Ajustar prompt ou rubrica conforme padrões identificados

#### 5.4 Enriquecimento do profile.md

- Sinais positivos de contexto: product company (vs consultoria) como boost
- Seção `mission_alignment_keywords` no profile.md (sustainability, climate, education, open source). Boost leve (+3-5 pontos), nunca eliminatório

**Fora de escopo (decisões documentadas):**
- Flexibility signals (ex: "do apply even if...") — boilerplate; risco de inflar scores sistematicamente
- Pesos altos em mission alignment — decisão de aplicar por missão é melhor feita manualmente na UI
- Decomposição granular de skills individuais — evidence mapping por requirement já captura

---

### ÉPICO 6: UI Funcional Mínima

**Objetivo:** Interface com valor imediato — monitorar LinkedIn, avaliar vagas manualmente, visualizar resultados do pipeline automático.

**Dependência:** Épico 5.1 concluído.

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

#### 8.1 Expansão de títulos de busca

- Usar resultado da análise exploratória (5.2) para ampliar `TITLE_KEYWORDS`

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

## 💡 Ideias Futuras

- **Tracking de aplicações:** Status por vaga (aplicado → entrevista → oferta → rejeitado)
- **Analytics:** Vagas/dia, score médio, tendências, taxa de aplicação, fontes mais produtivas
- **Cover letter por plataforma:** Adaptar para formulários específicos ("Why this company?", "Why this role?")
- **Múltiplos perfis:** PM puro vs TPM vs hybrid — scoring e geração adaptados
- **DOCX e texto puro:** Formatos alternativos de saída
- **VPS/Cloud:** Migrar Streamlit para acesso remoto
- **discover.py:** Prospectar novas empresas-alvo via queries em boards ATS
- **Notificação mobile:** Push via Telegram Bot para PERFECT_MATCH
- **Alertas por email:** notify.py envia email se score ≥ 95

---

**Última atualização:** Fev 2026
