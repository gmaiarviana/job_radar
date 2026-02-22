# ROADMAP - Job Radar

Épicos incrementais do sistema de busca automatizada de vagas.

> **Filosofia:** POC → Protótipo → MVP. Validar cada etapa antes de avançar.

---

## ✅ Concluído

### Validação de Fontes (Exploratório)
Testamos APIs gratuitas (Remotive, Arbeitnow) e LLMs com web search (ChatGPT, Grok). APIs gratuitas trouxeram volume baixo e pouca relevância. ChatGPT com web search retornou as melhores vagas. Decisão: OpenAI API com web_search como fonte principal.

---

## 📍 Próximos Passos

### ÉPICO 1: Fetch + Score (POC)

**Objetivo:** Validar que busca via OpenAI web search + scoring via Claude Haiku retorna vagas relevantes e bem pontuadas.

**Critério de sucesso:** Rodar 3 dias consecutivos. Scoring com concordância ≥ 80% vs avaliação manual.

#### 1.1 Perfil condensado
- Criar `config/profile.md` derivado do Career Narrative
- ~800 tokens: experiência, skills, critérios eliminatórios, preferências
- Critérios eliminatórios explícitos: localização (Brasil/LATAM/Worldwide), salário (≥ $5k USD/mês), idioma (inglês obrigatório, outros = red flag)

#### 1.2 Prompt de busca (fetch)
- Prompt para gpt-4o-mini com web_search_preview
- Instruções: buscar vagas PM/TPM remote LATAM/Worldwide, últimas 24h
- Output estruturado: título, empresa, salário, localização, URL, requisitos, data
- Parâmetros em `config/search.yaml`

#### 1.3 Script fetch.py
- Chama OpenAI Responses API com web_search
- Parseia resposta em JSON
- Salva em `data/raw/YYYY-MM-DD.json`
- Tratamento de erro: API indisponível, resposta malformada, zero resultados

#### 1.4 Prompt de scoring
- System prompt com perfil + critérios de scoring
- Input: vagas do fetch
- Output por vaga: score 0-100, justificativa (1 linha), flag PERFECT_MATCH
- Pesos explícitos: localização (eliminatório), salário, fit de responsabilidades, red flags

#### 1.5 Script score.py
- Lê `data/raw/YYYY-MM-DD.json`
- Chama Claude Haiku com batch de vagas
- Salva em `data/scored/YYYY-MM-DD.json` (top vagas, score ≥ 80)

#### 1.6 Calibração manual
- Candidato avalia 20-30 vagas manualmente
- Compara com scores do LLM
- Ajusta prompt/pesos até concordância ≥ 80%

---

### ÉPICO 2: Interface Streamlit (Protótipo)

**Objetivo:** Interface local para visualizar vagas, gerar materiais de aplicação, e dar feedback.

**Dependência:** Épico 1 validado.

**Critério de sucesso:** Jornada completa funcional — ver vagas → gerar currículo → download PDF → feedback.

#### 2.1 Tela principal — vagas do dia
- Lista de vagas pontuadas, ordenadas por score
- Card por vaga: título, empresa, score (badge colorido), salário, justificativa, link direto
- Cores: verde (≥ 90), amarelo (80-89)
- Seletor de data para ver dias anteriores

#### 2.2 Botão "Preparar aplicação"
- Ao clicar: chama `generate.py` com dados da vaga + perfil
- Loading indicator enquanto gera (~5-10 segundos)
- Exibe preview do currículo e cover letter gerados
- Botão de download PDF para cada um

#### 2.3 Feedback por vaga
- Botões "👍 Bom match" / "👎 Não relevante" em cada card
- Salva em `data/feedback/YYYY-MM-DD.json`
- Visual: vaga fica marcada após feedback

#### 2.4 Histórico
- Sidebar ou aba com lista de dias passados
- Vagas marcadas como "aplicado" (se usou "Preparar aplicação")
- Contadores: vagas vistas, aplicações geradas, feedbacks dados

---

### ÉPICO 3: Geração de Materiais (POC)

**Objetivo:** Gerar currículo e cover letter personalizados por vaga, com qualidade de aplicação real.

**Dependência:** Pode rodar em paralelo com Épico 2 (script independente).

**Critério de sucesso:** Materiais gerados para 5 vagas reais. Candidato considera ≥ 4 prontos para enviar com mínima edição.

#### 3.1 Currículo base modular
- Criar `config/resume_base.md` com seções do Career Narrative
- Formato: Markdown estruturado com marcadores de seção
- Seções: Summary (adaptável), Experience (bullets selecionáveis por role), Skills (modulares), Education

#### 3.2 Template de cover letter
- Criar `config/cover_letter_template.md`
- Voz do candidato: direto, sem clichês, conecta experiência com a vaga
- Estrutura: abertura (por que essa empresa), fit (o que trago), fechamento

#### 3.3 Script generate.py
- Input: dados da vaga (do scored JSON) + resume_base + cover_letter_template
- LLM: Claude Sonnet (qualidade de escrita)
- Output: currículo adaptado + cover letter adaptada
- Regra: reorganizar e enfatizar, sem inventar experiência
- Salva Markdown intermediário + PDF final em `data/output/`

#### 3.4 Geração de PDF
- Markdown → PDF com formatação limpa
- Biblioteca: weasyprint ou reportlab
- Layout profissional, 1 página (currículo), 0.5-1 página (cover letter)

---

### ÉPICO 4: Pipeline Automatizado (MVP)

**Objetivo:** Fetch + Score rodando automaticamente via GitHub Actions.

**Dependência:** Épicos 1-3 validados localmente.

**Critério de sucesso:** 5 dias consecutivos rodando sem intervenção, dados disponíveis para Streamlit via git pull.

#### 4.1 Workflow daily.yml
- Cron: `0 9 * * 1-5` (9h UTC = 6h BRT)
- Steps: fetch → score → commit + push
- Secrets: `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`
- Timeout: 5 min

#### 4.2 Tratamento de falhas
- Retry 1x se API falhar
- Se falhar: commit log de erro, pipeline não quebra
- Badge no README com status

#### 4.3 Alertas por email (PERFECT_MATCH)
- Script notify.py roda após score
- Envia email se alguma vaga tem score ≥ 95
- Máximo 1 email/dia (agrupa PERFECT_MATCH)
- Via Gmail SMTP (App Password)

---

### ÉPICO 5: Feedback Loop (Melhoria)

**Objetivo:** Feedback do usuário alimenta o scoring das próximas rodadas.

**Dependência:** Épicos 2 e 4 rodando.

**Critério de sucesso:** Scoring melhora visivelmente após 2 semanas de feedback (menos falsos positivos/negativos).

#### 5.1 Agregação de feedback
- Script que lê todos `data/feedback/*.json`
- Gera resumo: padrões de concordância/discordância
- Identifica: que tipo de vaga o candidato rejeita? que tipo aceita?

#### 5.2 Feedback no prompt de scoring
- Inclui resumo de feedback como contexto adicional no prompt do score.py
- Exemplo: "Candidato rejeitou vagas de startup early-stage sem salário listado"
- Atualização manual (v1) — candidato revisa resumo antes de incluir

#### 5.3 Persistência no repositório
- Decide: feedback fica local ou sobe pro repo (via commit)?
- Se repo: Actions consegue ler feedback para calibrar scoring automaticamente
- Se local: candidato precisa rodar script de sync manual

---

## 💡 Ideias Futuras

Aguardando validação do MVP (Épicos 1-5).

- **Deduplicação cross-dia:** Detectar mesma vaga em dias diferentes
- **DOCX e texto puro:** Formatos alternativos de saída
- **Cover letter por plataforma:** Adaptar para formulários específicos ("Why this company?")
- **Tracking de aplicações:** Status (aplicado → entrevista → oferta → rejeitado)
- **Analytics:** Vagas/dia, score médio, tendências de mercado, taxa de aplicação
- **Múltiplos perfis:** Posicionamentos diferentes (PM puro vs TPM vs hybrid)
- **VPS/Cloud:** Migrar Streamlit para acesso remoto (Hetzner, Streamlit Cloud)
- **Fonte adicional (JSearch):** Fallback se OpenAI web search perder cobertura

---

## 📝 Observações

- Épicos 1 e 3 são os mais críticos — validam busca e geração de materiais
- Épico 2 conecta tudo na interface — é onde a experiência se materializa
- Épico 4 é automação do que já funciona manualmente
- Épico 5 é refinamento contínuo — valor cresce com o tempo
- Cada épico entrega valor isolado (posso usar fetch+score+generate via terminal antes do Streamlit existir)

**Última atualização:** Fev 2026