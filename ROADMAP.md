# ROADMAP - Job Radar

📡 **Status:** Infraestrutura Base (Scaffolding) concluída. Perfil e stubs configurados. Fetch funcional via OpenAI.

> **Filosofia:** POC → Protótipo → MVP. Validar cada etapa antes de avançar.

---

## ✅ Concluído
- **Validação de Fontes:** Definição da stack (OpenAI web search + Claude Haiku).
- **Scaffolding:** Estrutura de pastas, stubs de código, `profile.md` real.
- **Épico 1.1:** Perfil condensado em `config/profile.md`.
- **Épico 1.2:** Prompt de busca (fetch) refinado em `src/fetch.py`.
- **Épico 1.3:** Script `src/fetch.py` funcional usando `gpt-4o-mini-search-preview`.
- **Épico 4.1:** Workflow `daily.yml` configurado para GitHub Actions.

---

## 📍 Próximos Passos (Plano Detalhado)

### ÉPICO 1: Fetch + Score (POC) - ⏳ EM PROGRESSO

**Objetivo:** Validar que busca via OpenAI web search + scoring via Claude Haiku retorna vagas relevantes e bem pontuadas.

**Critério de sucesso:** Rodar 3 dias consecutivos. Scoring com concordância ≥ 80% vs avaliação manual.

#### 1.4 Prompt de scoring (PENDENTE)
- System prompt com perfil + critérios de scoring.
- Input: vagas do fetch.
- Output por vaga: score 0-100, justificativa (1 linha), flag PERFECT_MATCH.
- Pesos explícitos: localização (eliminatório), salário (≥ $5k USD), fit de responsabilidades, red flags.

#### 1.5 Script score.py (PENDENTE - STUB)
- Lê `data/raw/YYYY-MM-DD.json`.
- Chama Claude Haiku com batch de vagas.
- Salva em `data/scored/YYYY-MM-DD.json` (top vagas, score ≥ 80).

#### 1.6 Calibração manual (PENDENTE)
- Candidato avalia 20-30 vagas manualmente.
- Compara com scores do LLM.
- Ajusta prompt/pesos até concordância ≥ 80%.

---

### ÉPICO 2: Interface Streamlit (Protótipo) - ⏳ PENDENTE

**Objetivo:** Interface local para visualizar vagas, gerar materiais de aplicação, e dar feedback.
**Dependência:** Épico 1 validado.
**Critério de sucesso:** Jornada completa funcional — ver vagas → gerar currículo → download PDF → feedback.

#### 2.1 Tela principal — vagas do dia (STUB em app.py)
- Lista de vagas pontuadas, ordenadas por score.
- Card por vaga: título, empresa, score (badge colorido), salário, justificativa, link direto.
- Cores: verde (≥ 90), amarelo (80-89).
- Seletor de data para ver dias anteriores.

#### 2.2 Botão "Preparar aplicação" (PENDENTE)
- Ao clicar: chama `generate.py` com dados da vaga + perfil.
- Loading indicator enquanto gera (~5-10 segundos).
- Exibe preview do currículo e cover letter gerados.
- Botão de download PDF para cada um.

#### 2.3 Feedback por vaga (PENDENTE)
- Botões "👍 Bom match" / "👎 Não relevante" em cada card.
- Salva em `data/feedback/YYYY-MM-DD.json`.
- Visual: vaga fica marcada após feedback.

#### 2.4 Histórico (PENDENTE)
- Sidebar ou aba com lista de dias passados.
- Vagas marcadas como "aplicado".
- Contadores: vagas vistas, aplicações geradas, feedbacks dados.

---

### ÉPICO 3: Geração de Materiais (POC) - ⏳ PENDENTE

**Objetivo:** Gerar currículo e cover letter personalizados por vaga, com qualidade de aplicação real.
**Dependência:** Pode rodar em paralelo com Épico 2 (script independente).
**Critério de sucesso:** Materiais gerados para 5 vagas reais. Candidato considera ≥ 4 prontos para enviar com mínima edição.

#### 3.1 & 3.2 Estrutura e Templates
- **Resume Base:** Criar `config/resume_base.md` modular (seções Resume/CV, seções reorganizáveis).
- **Template Cover Letter:** Criar `config/cover_letter_template.md` com voz do candidato.

#### 3.3 Script generate.py (PENDENTE - STUB)
- Input: dados da vaga (do scored JSON) + resume_base + cover_letter_template.
- LLM: Claude Sonnet (qualidade de escrita).
- Regra: reorganizar e enfatizar, sem inventar experiência.
- Output: Markdown intermediário + PDF final em `data/output/`.

#### 3.4 Geração de PDF (PENDENTE)
- Markdown → PDF com formatação limpa (weasyprint ou reportlab).
- Layout profissional, 1 página (currículo), 0.5-1 página (cover letter).

---

### ÉPICO 4: Pipeline Automatizado (MVP) - ⏳ PARCIAL

**Objetivo:** Fetch + Score rodando automaticamente via GitHub Actions.
**Critério de sucesso:** 5 dias consecutivos rodando sem intervenção, dados disponíveis para Streamlit via git pull.

#### 4.2 Tratamento de falhas (PENDENTE)
- Retry 1x se API falhar. Commit log de erro, pipeline não quebra.
- Badge no README com status.

#### 4.3 Alertas por email (PERFECT_MATCH) (PENDENTE - STUB)
- Script notify.py roda após score.
- Envia email se alguma vaga tem score ≥ 95.
- Via Gmail SMTP (App Password).

---

### ÉPICO 5: Feedback Loop (Melhoria) - ⏳ PENDENTE

**Objetivo:** Feedback do usuário alimenta o scoring das próximas rodadas.
**Critério de sucesso:** Scoring melhora visivelmente após 2 semanas de feedback.

#### 5.1 & 5.2 Agregação e Integração
- Script que lê todos `data/feedback/*.json` e gera resumo de padrões.
- Inclui resumo de feedback como contexto adicional no prompt do score.py.

#### 5.3 Persistência
- Decidir se feedback fica local ou sobe pro repo (via commit).

---

## 💡 Ideias Futuras
- **Deduplicação cross-dia:** Detectar mesma vaga em dias diferentes.
- **DOCX e texto puro:** Formatos alternativos de saída.
- **Cover letter por plataforma:** Adaptar para formulários específicos.
- **Tracking de aplicações:** Status (aplicado → entrevista → oferta → rejeitado).
- **Analytics:** Vagas/dia, score médio, tendências de mercado.
- **Múltiplos perfis:** Posicionamentos diferentes (PM vs TPM vs hybrid).

---

**Última atualização:** 22 Fev 2026
