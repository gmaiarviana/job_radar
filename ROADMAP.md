# ROADMAP - Job Radar

## 📍 Próximos Passos (Estado Futuro)



### ÉPICO 1: Fetch + Score (POC) - ⏳ EM PROGRESSO

**Objetivo:** Validar que busca via OpenAI web search + scoring via Claude Haiku retorna vagas relevantes e bem pontuadas.

**Critério de sucesso:** Rodar 3 dias consecutivos. Scoring com concordância ≥ 80% vs avaliação manual.

#### 1.4 Prompt de scoring - ✅ CONCLUÍDO
- System prompt com perfil + critérios de scoring.
- Input: vagas do fetch.
- Output por vaga: score 0-100, justificativa (1 linha), flag PERFECT_MATCH.
- Pesos explícitos: localização (eliminatório), salário (≥ $5k USD), fit de responsabilidades, red flags.

#### 1.5 Script score.py - ✅ CONCLUÍDO
- Lê `data/raw/YYYY-MM-DD.json`.
- Refatorado para processo de duas etapas:
    1. Eliminatórios (Batch Haiku): Filtra por local, sênior, cargo e idioma.
    2. Scoring Profundo (Haiku Individual): Mapeamento de evidências, gaps e score (0-95).
- Salva em `data/scored/` com campos `jobs` (top), `filtered_jobs` e `eliminated_jobs`.

#### 1.6 Calibração manual (PENDENTE)
- Candidato avalia 20-30 vagas manualmente.
- Compara com scores do LLM.
- Ajusta prompt/pesos até concordância ≥ 80%.
- **Vaga específica:** Verificar manualmente o JD real da Planet Labs (job/7542179) para confirmar se Brasil está incluído no "Work from Anywhere" antes de aplicar. Registrar a decisão no feedback.

#### 1.7 Débito Técnico: Tratamento de Ambiguidade de Localização (PENDENTE)
- O campo `location_confidence: "low"` capturado pelo fetch não está sendo usado no filtro do `score.py`. 
- Vagas com localização ambígua (ex: listas longas de países que incluem "Work from Anywhere") passam pelo filtro sem penalização. 
- **Ação:** Avaliar se `location_confidence: "low"` deve gerar penalização automática no score ou flag de revisão manual.

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

#### 4.4 Tracking de Custos (PENDENTE)
- Calcular custo de cada run (OpenAI Search + Claude Haiku).
- Salvar metadados de custo no JSON de output (`data/scored/`).
- Exibir resumo de custo no log do GitHub Actions e no app Streamlit.

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

### ÉPICO 6: Expansão de Fontes (Planejado)
**Objetivo:** Reduzir dependência exclusiva do OpenAI Search e aumentar volume de vagas relevantes.
- [ ] Integração com Himalayas API.
- [ ] Integração com We Work Remotely RSS feed.
- [ ] Agregação cross-fonte no `fetch.py`.

### ÉPICO 7: Expansão de Busca (Planejado)
**Objetivo:** Cobrir mais variações de cargos no `search.yaml`.
- [ ] Adicionar títulos: Senior PM, AI Product Manager, Product Analyst, Strategy & Operations, Delivery Manager, Program Manager.

---

## 💡 Ideias Futuras
- **DOCX e texto puro:** Formatos alternativos de saída.
- **Cover letter por plataforma:** Adaptar para formulários específicos.
- **Tracking de aplicações:** Status (aplicado → entrevista → oferta → rejeitado).
- **Analytics:** Vagas/dia, score médio, tendências de mercado.
- **Múltiplos perfis:** Posicionamentos diferentes (PM vs TPM vs hybrid).

---

## ✅ CONCLUÍDO RECENTEMENTE

- **Scoring em Duas Etapas (v1.6)**: Refatoração do `score.py` para separar eliminatórios (batch) de scoring profundo (individual). Implementadas regras estritas contra termos genéricos, score máximo de 95, e mapeamento obrigatório de evidências/gaps. (23 Fev 2026)

- **Melhorias no Fetch (v1.5.1)**: Correção da deduplicação em lote no `fetch.py` com adição de logs explícitos e tracking separado para remoções locais/remotas. (23 Fev 2026)
- **Melhorias no Fetch (v1.5)**: Extração literal de localização do JD, deduplicação cross-dia (7 dias) e filtro de vagas antigas (> 14 dias). (23 Fev 2026)
- **Garantia de Não-Sobrescrita (Timestamps)**: Implementação de timestamps em arquivos `data/scored/` e atualização de dependentes (`score`, `generate`, `notify`) para suportar múltiplas execuções manuais. (23 Fev 2026)
- **Filtro de Localização e Refinamento de Prompt**: Implementação de filtro hard de localização antes do LLM (no `score.py`) e refinamento do system prompt para maior rigor em senioridade e local. (23 Fev 2026)
- **Sistema de Protocolos e Closure**: Implementação da Constituição, Mapa de Decisões e Workflow `/finish` para garantir integridade e não-duplicação. (23 Fev 2026)
