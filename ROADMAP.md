# ROADMAP - Job Radar

📡 **Status:** Épico 1 concluído. Épico 2 em andamento: 2.1 e 2.2 concluídos (refatoração multi-fonte + conector Remotive). Próximos: 2.3 We Work Remotely, 2.4 Jobicy, 2.5 Quality Guard, 2.6 métricas.

> **Filosofia:** POC → Protótipo → MVP. Validar cada etapa antes de avançar.

---

## ✅ Concluído

### ÉPICO 1: Fetch + Score (Arquitetura Base)

**Objetivo:** Validar a arquitetura fetch → score → commit com dados reais.

**O que foi construído:**
- `src/fetch.py` — busca via OpenAI web search (gpt-4o-mini-search-preview)
- `src/score.py` — scoring via Claude Haiku com filtros eliminatórios e pesos
- `daily.yml` — pipeline no GitHub Actions (seg-sex 9h UTC)
- `config/profile.md`, `config/search.yaml` — configuração do candidato e parâmetros de busca
- Deduplicação intra-run e cross-7-dias por título+empresa
- Filtros eliminatórios: localização, nível, tipo de cargo, idioma

**Por que foi encerrado:**
A arquitetura está validada. O problema identificado é a estratégia de coleta: OpenAI web search retorna volume baixo, duplicatas e JDs rasos. Não é um problema de scoring — é de input.

**Decisão:** OpenAI web search desativado como fonte primária. Mantido como camada futura de descoberta (exploração semanal de novas empresas), não de coleta diária.

---

### ÉPICO 2 (parcial): Fetch Multi-Fonte — 2.1 e 2.2 concluídos

**O que foi construído:**
- **2.1 Refatoração:** Pipeline com coletores independentes; schema único em `src/job_schema.py` (`id_hash`, `source`, `title`, `company`, `location`, `salary`, `jd_full`, `url`, `collected_at`, `date`); dedupe cross-fonte por `id_hash`; componentização em `src/job_schema.py`, `src/collectors/`, `src/fetch_pipeline.py`, `src/fetch.py` (CLI).
- **2.2 Conector Remotive:** `src/collectors/remotive.py` — API Remotive, categorias `product` e `project-management`, filtro últimas 48h por `publication_date`.
- Execução validada com venv; correção de encoding UTF-8 no console Windows para logs com emoji.

**Lições aprendidas (evitar repetir):**
- **Ambiente:** Sempre rodar com **venv** (ex.: `python -m venv .venv`); instalar deps antes de validar. Evita `ModuleNotFoundError` e garante reprodutibilidade.
- **Windows:** Console cp1252 não imprime emojis → `UnicodeEncodeError`. Em `fetch.py` foi configurado stdout/stderr para UTF-8 quando o encoding não for utf-8. Em novos scripts CLI, preferir UTF-8 no início ou evitar emojis em logs.
- **Testes:** Projeto ainda sem suíte de testes (pytest/test_*.py). Recomendação: adicionar pelo menos smoke test (ex.: `python src/fetch.py --dry-run`) ou testes unitários para `job_schema`, `filter_old_jobs`, `remove_duplicates` antes de seguir para 2.3+.
- **Componentização:** Foi feita após 2.2. Na próxima vez, componentizar no primeiro épico que introduz múltiplas fontes (ex.: no 2.1) para não mover código duas vezes.

---

## 📍 Próximos Épicos

---

### ÉPICO 2: Fetch Multi-Fonte — APIs e RSS Públicos (restante)

**Objetivo:** Substituir o fetch atual por fontes estruturadas gratuitas, garantindo volume e diversidade reais de vagas diárias.

**Dependência:** Épico 1 concluído.

**Critério de aceite:**
- Mínimo 20 vagas únicas por dia (empresas distintas)
- Zero duplicatas intra-run
- 100% dos jobs com JD ≥ 500 caracteres antes de chegar no scoring
- Campo `source` preenchido em cada job
- `fetch.py` refatorado para arquitetura multi-fonte com coletores independentes

#### ~~2.1 Refatoração do fetch.py~~ ✅

- Arquitetura: coletores independentes por fonte, agregados em um pipeline único
- Normalização obrigatória: todo job vira o mesmo schema independente da fonte
- Schema mínimo: `id_hash`, `source`, `title`, `company`, `location`, `salary`, `jd_full`, `url`, `collected_at`, `date`
- `id_hash` baseado em `company + title` (case insensitive) para dedupe cross-fonte

#### ~~2.2 Conector Remotive~~ ✅

- Endpoint: `https://remotive.com/api/remote-jobs?category=product&limit=100`
- Categorias: `product`, `project-management`
- Filtro de recência: últimas 48h (usar campo `publication_date`)

#### 2.3 Conector We Work Remotely

- Fonte: RSS feed público (`https://weworkremotely.com/categories/remote-management-and-finance-jobs.rss`)
- Parser RSS com `feedparser` ou `urllib` nativo
- Filtro por keywords no título: product manager, program manager, TPM

#### 2.4 Conector Jobicy

- Endpoint: `https://jobicy.com/api/v2/remote-jobs?industry=product&count=50`
- API pública, sem key
- Filtro de recência: últimas 48h

#### 2.5 Quality Guard (pré-scoring)

- JD < 500 caracteres → descartado com log
- Título vazio ou genérico (ex: "Opportunity", "Job Opening") → descartado com log
- Empresa não detectada → descartado com log
- Log de descartados salvo em `data/raw/YYYY-MM-DD_discarded.json`

#### 2.6 Métricas de cobertura (no output do fetch)

Adicionar ao JSON de saída:
```json
"coverage": {
  "sources": ["remotive", "weworkremotely", "jobicy"],
  "total_raw": 85,
  "total_after_recent_filter": 42,
  "total_after_dedup": 38,
  "total_after_quality_guard": 35,
  "companies_distinct": 31,
  "discarded_low_quality": 3
}
```

---

### ÉPICO 3: Fetch Estratégico — Greenhouse + Empresas-Alvo

**Objetivo:** Adicionar cobertura direta de empresas tech sérias via ATS (Greenhouse/Lever), sem depender de boards agregadores.

**Dependência:** Épico 2 rodando e estável.

**Critério de aceite:**
- Lista curada de ≥ 20 empresas-alvo em `config/companies.yaml`
- Conector Greenhouse funcional para pelo menos 10 empresas da lista
- Vagas de ATS chegando no pipeline com mesmo schema do Épico 2
- Empresas novas podem ser adicionadas à lista sem alterar código

#### 3.1 config/companies.yaml

Arquivo de configuração com empresas-alvo por setor e ATS:
```yaml
companies:
  healthtech:
    - name: "Alma"
      ats: "greenhouse"
      ats_id: "alma"
    - name: "Cerebral"
      ats: "greenhouse"
      ats_id: "cerebral"
  edtech:
    - name: "Duolingo"
      ats: "greenhouse"
      ats_id: "duolingo"
  fintech:
    - name: "Nubank"
      ats: "lever"
      ats_id: "nubank"
    - name: "Lemon Cash"
      ats: "ashby"
      ats_id: "lemoncash"
```

#### 3.2 Conector Greenhouse

- Endpoint público: `https://boards-api.greenhouse.io/v1/boards/{company_id}/jobs`
- Sem API key necessária
- Filtro por título no lado do cliente (keywords: product manager, TPM, program manager)
- Fetch do JD completo via `GET /jobs/{id}` (endpoint separado)

#### 3.3 Conector Lever

- Endpoint público: `https://api.lever.co/v0/postings/{company_id}?mode=json`
- Mesma lógica de filtro por título
- Integração com mesmo schema de normalização

#### 3.4 Conector Ashby

- Endpoint público: `https://jobs.ashbyhq.com/api/non-user-facing/job-board/job-posting/list`
- Body JSON: `{"organizationHostedJobsPageName": "{company_id}"}`
- Prioridade igual ao Greenhouse — startups série A/B usam Ashby com frequência
- Mesma lógica de filtro por título e normalização

#### 3.5 Descoberta manual (src/discover.py)

- Script separado, sem integração com o pipeline diário
- Uso: rodar manualmente quando quiser prospectar novas empresas
- Estratégia: queries Google `site:boards.greenhouse.io`, `site:jobs.lever.co`, `site:jobs.ashbyhq.com` com filtros de localização e título
- Output: lista de sugestões com empresa + ATS + ID para adicionar ao `companies.yaml`
- Nenhuma saída do `discover.py` entra no pipeline automaticamente — revisão manual obrigatória

---

### ÉPICO 4: Calibração de Scoring

**Objetivo:** Garantir que o scoring reflete fit real, usando dados reais do Épico 2 como base.

**Dependência:** Épico 2 rodando com volume ≥ 20 vagas/dia por pelo menos 5 dias.

**Critério de aceite:**
- Concordância ≥ 80% entre score do LLM e avaliação manual em amostra de 30 vagas
- Distribuição de scores saudável (não concentrada em 85-92)
- Falsos positivos (score alto, vaga ruim) < 20%

#### 4.1 Avaliação manual de amostra

- Candidato avalia 30 vagas manualmente (fit 0-100 + motivo)
- Comparação com scores do LLM
- Identificação de padrões de erro

#### 4.2 Ajuste de pesos e prompt

- Revisar pesos em `config/search.yaml`
- Ajustar prompt de scoring com base nos padrões identificados
- Re-rodar scoring na mesma amostra para validar melhora

#### 4.3 Critérios eliminatórios revisados

- Validar se filtros atuais (localização, nível, idioma, tipo de cargo) estão corretos
- Adicionar red flags identificados na avaliação manual

---

### ÉPICO 5: Interface Streamlit

**Objetivo:** Interface local para visualizar vagas, gerar materiais de aplicação e dar feedback.

**Dependência:** Épico 4 concluído (scoring calibrado).

**Critério de aceite:** Jornada completa funcional — ver vagas → gerar currículo → download PDF → feedback.

#### 5.1 Tela principal — vagas do dia

- Lista de vagas pontuadas, ordenadas por score
- Card por vaga: título, empresa, score (badge colorido), salário, justificativa, link direto
- Cores: verde (≥ 90), amarelo (80-89)
- Seletor de data para ver dias anteriores

#### 5.2 Botão "Preparar aplicação"

- Chama `generate.py` com dados da vaga + perfil
- Loading indicator enquanto gera
- Preview do currículo e cover letter gerados
- Botão de download PDF

#### 5.3 Feedback por vaga

- Botões "👍 Bom match" / "👎 Não relevante" em cada card
- Salva em `data/feedback/YYYY-MM-DD.json`

#### 5.4 Histórico

- Lista de dias anteriores na sidebar
- Contadores: vagas vistas, aplicações geradas, feedbacks dados

---

### ÉPICO 6: Geração de Materiais

**Objetivo:** Gerar currículo e cover letter personalizados por vaga, com qualidade de aplicação real.

**Dependência:** Pode rodar em paralelo com Épico 5.

**Critério de aceite:** Materiais gerados para 5 vagas reais. Candidato considera ≥ 4 prontos para enviar com mínima edição.

#### 6.1 Currículo base modular

- `config/resume_base.md` com seções organizadas por relevância
- Seções: Summary (adaptável), Experience (bullets selecionáveis), Skills, Education

#### 6.2 Template de cover letter

- `config/cover_letter_template.md`
- Voz do candidato: direto, sem clichês, conecta experiência com a vaga
- Estrutura: abertura (por que essa empresa), fit (o que trago), fechamento

#### 6.3 Script generate.py

- Input: vaga (scored JSON) + resume_base + cover_letter_template + profile
- LLM: Claude Sonnet (qualidade de escrita)
- Output: currículo adaptado + cover letter adaptada em Markdown + PDF
- Regra: reorganizar e enfatizar, nunca inventar experiência

#### 6.4 Geração de PDF

- Markdown → PDF com layout limpo e profissional
- 1 página (currículo), 0.5-1 página (cover letter)
- Biblioteca: weasyprint

---

### ÉPICO 7: Pipeline Automatizado

**Objetivo:** Fetch + Score rodando automaticamente via GitHub Actions com o novo fetch multi-fonte.

**Dependência:** Épicos 2, 3 e 4 concluídos.

**Critério de aceite:** 5 dias consecutivos rodando sem intervenção. Cobertura ≥ 20 vagas/dia consistente.

#### 7.1 Atualização do daily.yml

- Remover dependência de `OPENAI_API_KEY` do step de fetch
- Timeout: aumentar para 10 min (múltiplas fontes)
- Step de fetch agora roda coletores em paralelo

#### 7.2 Tratamento de falhas

- Se uma fonte falhar, pipeline continua com as demais
- Retry 1x por fonte se timeout
- Commit de log de erro se todas as fontes falharem

#### 7.3 Alertas por email (PERFECT_MATCH)

- `notify.py` envia email se score ≥ 95
- Máximo 1 email/dia (agrupa todos os PERFECT_MATCH)
- Via Gmail SMTP (App Password)

---

### ÉPICO 8: Feedback Loop

**Objetivo:** Feedback do usuário alimenta o scoring das próximas rodadas.

**Dependência:** Épicos 5 e 7 rodando.

**Critério de aceite:** Scoring melhora visivelmente após 2 semanas de feedback (menos falsos positivos/negativos).

#### 8.1 Agregação de feedback

- Script lê todos `data/feedback/*.json`
- Gera resumo de padrões: que tipo de vaga o candidato rejeita? que tipo aceita?

#### 8.2 Feedback no prompt de scoring

- Resumo de feedback incluído como contexto no prompt do `score.py`
- Atualização manual (v1) — candidato revisa resumo antes de incluir

#### 8.3 Persistência no repositório

- Feedback sobe pro repo via commit
- GitHub Actions consegue ler feedback para calibrar scoring automaticamente

---

## 💡 Ideias Futuras

- **Tracking de aplicações:** Status (aplicado → entrevista → oferta → rejeitado)
- **Analytics:** Vagas/dia, score médio, tendências, taxa de aplicação
- **Cover letter por plataforma:** Adaptar para formulários específicos ("Why this company?")
- **Múltiplos perfis:** PM puro vs TPM vs hybrid
- **DOCX e texto puro:** Formatos alternativos de saída
- **VPS/Cloud:** Migrar Streamlit para acesso remoto (Hetzner, Streamlit Cloud)
- **discover.py semanal via Actions:** Automação da descoberta de novas empresas-alvo

---

**Última atualização:** Fev 2026