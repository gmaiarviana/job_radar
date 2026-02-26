# ROADMAP - Job Radar

📡 **Status:** Pipeline completo. Épico 4 (Qualidade de Filtragem) concluído. Próximo: **Épico 5 — Qualidade de Scoring**.

> **Filosofia:** POC → Protótipo → MVP. Validar cada etapa antes de avançar. Qualidade antes de volume.

---

## ✅ Concluído

Pipeline completo: fetch multi-fonte (Remotive, We Work Remotely, Jobicy, OpenAI Search, Greenhouse, Lever, Ashby), schema único, dedup persistente (`seen_jobs.json`), throttle, quality guard, filter com hard filters de títulos e localização em duas camadas (blocklist + JD completo no eliminatório), scoring em dois estágios (eliminatórios + deep score via Claude Haiku), GitHub Actions diário, seed ATS. Qualidade de filtragem fechada: eval em `src/eval/`, paths em `src/paths.py`, companies por ATS em `fetch_pipeline.get_companies_by_ats`, score ignora `seed_*.json`, seed `--dry-run` sem rede. Estrutura em [ARCHITECTURE.md](ARCHITECTURE.md).

---

## 📍 Próximos Épicos

---

### ÉPICO 5: Qualidade de Scoring

**Objetivo:** Garantir que o score reflita fit real. O LLM deve aplicar as penalizações da rubrica — não apenas identificar o gap no `main_gap`. (Motivação: no seed, vagas com gaps críticos de domínio/seniority ainda recebiam score ~90.)

**Dependência:** Épico 4 concluído.

**Critério de aceite:** Vagas com gap de domínio no core recebem score ≤ 60. Vagas Senior sem evidência de nível equivalente recebem score ≤ 65. As 5 vagas de maior aderência avaliadas manualmente fazem sentido.

#### 5.1 Correção do prompt de scoring

- Reescrever prompt para forçar aplicação das penalizações antes de atribuir o score (já existente)
- Estrutura proposta: (1) identificar penalizações aplicáveis → (2) definir teto de score → (3) atribuir score dentro do teto (já existente)
- Validar no seed: vagas que hoje têm score 90 com gaps críticos devem cair para ≤ 60 (já existente)
- Evidence mapping estruturado: forçar o LLM a listar top 3-5 requirements da JD e mapear evidência do perfil para cada um (ou marcar "sem evidência"). Substitui o campo evidence texto-livre atual
- Must-have vs nice-to-have: instruir o LLM a classificar requirements da JD antes de pontuar. Gap em nice-to-have penaliza pouco; gap em must-have penaliza forte
- Comparação explícita de seniority: se a JD pede X+ anos de experiência, o LLM deve comparar com o perfil do candidato e declarar se há gap
- Output format expandido: adicionar apply_recommendation (boolean) e adherence_pct (0-100) ao JSON de saída. Regra: score ≥ 70 + nenhum gap em must-have = true

#### 5.2 Análise exploratória de títulos (via NotebookLM)

- Extrair títulos únicos do seed por fonte via NotebookLM
- Identificar títulos relevantes fora do filtro atual (ex: "Product Lead", "Associate PM", "Group PM")
- Decisão: expandir `TITLE_KEYWORDS` nos coletores ou centralizar em `config/search.yaml`
- Realizado antes do Streamlit — é insumo para melhorar a coleta

#### 5.3 Validação com avaliação manual

- Avaliar as 5 vagas de maior score pós-Épico 4 (maior aderência ao perfil)
- Comparar avaliação manual com score do sistema
- Ajustar prompt ou rubrica conforme padrões identificados

#### 5.4 Enriquecimento do profile.md

- Adicionar sinais positivos de contexto: vaga em product company (vs consultoria) como sinal positivo, complementando a penalização de outsourcing já existente
- Adicionar seção mission_alignment_keywords no profile.md (ex: sustainability, climate, education, open source). Tratamento: boost leve (+3-5 pontos), nunca eliminatório
- Critério de aceite: profile.md atualizado com as novas seções; prompt de scoring referencia esses sinais

**Fora de escopo (decisões documentadas):**
- Flexibility signals (ex: "do apply even if...") — boilerplate de inclusão; risco de inflar scores de empresas grandes sistematicamente
- Pesos altos em mission alignment — decisão de aplicar por missão é melhor feita manualmente na UI, não pelo scoring automático
- Decomposição granular de skills individuais — LLMs são imprecisos em matching de listas de skills; evidence mapping por requirement já captura indiretamente

---

### ÉPICO 6: Interface Streamlit (UX end-to-end)

**Objetivo:** Fluxo completo funcionando — ver novas vagas todos os dias pela UI, com score confiável.

**Dependência:** Épico 5 concluído (scoring confiável).

**Critério de aceite:** Jornada completa funcional — ver vagas do dia → score + justificativa → link direto para candidatura → feedback.

#### 6.1 Tela principal — vagas do dia

- Lista de vagas pontuadas, ordenadas por score
- Card: título, empresa, score (badge colorido), salário, justificativa, link direto
- Cores: verde (≥ 85), amarelo (70–84)
- Seletor de data para dias anteriores

#### 6.2 Feedback por vaga

- Botões 👍 / 👎 em cada card
- Salva em `data/feedback/YYYY-MM-DD.json`

#### 6.3 Histórico

- Lista de dias anteriores na sidebar
- Contadores: vagas vistas, feedbacks dados

---

### ÉPICO 7: Expansão de Coleta

**Objetivo:** Aumentar volume e qualidade das vagas encontradas. ATS muda pouco dia a dia — o ganho vem de novos conectores e títulos mais abrangentes.

**Dependência:** Épico 6 rodando (UX funcionando, feedback disponível como sinal de qualidade).

#### 7.1 Expansão de títulos de busca

- Usar resultado da análise exploratória (5.2) para ampliar `TITLE_KEYWORDS`
- Adicionar variantes relevantes sem aumentar ruído

#### 7.2 Novos conectores

- Identificar e implementar conectores para boards relevantes ainda não cobertos
- Priorizar fontes com vagas LATAM/Worldwide confirmadas

#### 7.3 Revalidar empresas comentadas no companies.yaml

- Diversas empresas estão comentadas com "404 no seed" — revalidar slugs ou ATS atual
- Candidatas: Deel, Rippling, Miro, Grafana Labs, Hugging Face, dbt Labs, entre outras

---

### ÉPICO 8: Pipeline Automatizado Estável

**Objetivo:** Fetch + Score rodando de forma confiável via GitHub Actions.

**Dependência:** Épicos 4 e 5 concluídos.

**Critério de aceite:** 5 dias consecutivos sem intervenção. Cobertura ≥ 10 vagas novas/dia consistente.

#### 8.1 Tratamento de falhas por coletor

- Se uma fonte falhar, pipeline continua com as demais
- Retry 1x por fonte se timeout
- Commit de log de erro se todas as fontes falharem

---

### ÉPICO 9: Geração de Materiais

**Objetivo:** Gerar currículo e cover letter personalizados por vaga. Implementar após sistema maduro e UX funcionando.

**Dependência:** Épico 6 concluído e scoring estável por pelo menos 2 semanas.

**Critério de aceite:** Materiais gerados para 5 vagas reais. Candidato considera ≥ 4 prontos para enviar com mínima edição.

#### 9.1 Currículo base modular

- `config/resume_base.md` com seções organizadas por relevância e bullets selecionáveis

#### 9.2 Template de cover letter

- `config/cover_letter_template.md` com voz do candidato: direto, sem clichês

#### 9.3 Script generate.py

- Input: vaga (scored JSON) + resume_base + cover_letter_template + profile
- LLM: Claude Sonnet (qualidade de escrita)
- Regra: reorganizar e enfatizar, nunca inventar experiência
- Output: currículo + cover letter em Markdown + PDF (weasyprint)

#### 9.4 Integração com Streamlit

- Botão "Preparar aplicação" em cada card da UI
- Loading indicator, preview, download PDF

---

### ÉPICO 10: Feedback Loop

**Objetivo:** Feedback do usuário alimenta o scoring das próximas rodadas.

**Dependência:** Épicos 6 e 8 rodando com dados de pelo menos 2 semanas.

**Critério de aceite:** Scoring melhora visivelmente após 2 semanas de feedback (menos falsos positivos/negativos).

#### 10.1 Agregação de feedback

- Script lê `data/feedback/*.json`, gera resumo de padrões: que tipo de vaga o candidato rejeita, que tipo aceita

#### 10.2 Feedback no prompt de scoring

- Resumo incluído como contexto no prompt do `score.py`
- Atualização manual (v1) — candidato revisa antes de incluir

#### 10.3 Persistência no repositório

- Feedback sobe via commit; Actions consegue ler para calibrar scoring automaticamente

---

## 💡 Ideias Futuras

- **Tracking de aplicações:** Status por vaga (aplicado → entrevista → oferta → rejeitado)
- **Analytics:** Vagas/dia, score médio, tendências, taxa de aplicação, fontes mais produtivas
- **Cover letter por plataforma:** Adaptar para formulários específicos ("Why this company?", "Why this role?")
- **Múltiplos perfis:** PM puro vs TPM vs hybrid — scoring e geração adaptados por perfil
- **DOCX e texto puro:** Formatos alternativos de saída além de PDF
- **VPS/Cloud:** Migrar Streamlit para acesso remoto (Hetzner, Streamlit Cloud, Railway)
- **discover.py manual:** Prospectar novas empresas-alvo via queries em boards ATS; dedupe contra `companies.yaml`; sem integração com pipeline diário
- **discover.py semanal via Actions:** Automação da descoberta de novas empresas-alvo
- **Notificação mobile:** Push via Telegram Bot para PERFECT_MATCH
- **Alertas por email (PERFECT_MATCH):** `notify.py` envia email se score ≥ 95, máximo 1 email/dia via Gmail SMTP
- **Tracking de vaga aberta:** Detectar automaticamente se uma vaga ainda está disponível antes de notificar

---

**Última atualização:** Fev 2026

# ROADMAP - Job Radar

📡 **Status:** Pipeline completo. Épico 4 (Qualidade de Filtragem) concluído. Próximo: **Épico 5 — Qualidade de Scoring**.

> **Filosofia:** POC → Protótipo → MVP. Validar cada etapa antes de avançar.

---

## ✅ Concluído

### ÉPICO 1: Fetch + Score (Arquitetura Base)

**Objetivo:** Validar a arquitetura fetch → score → commit com dados reais.

**Resumo:** Pipeline fetch (OpenAI web search) + score (Claude Haiku) + GitHub Actions; config em `config/profile.md` e `config/search.yaml`; dedupe e filtros eliminatórios. Detalhes em [ARCHITECTURE.md](ARCHITECTURE.md).

**Decisão:** OpenAI web search desativado como fonte primária (volume baixo, JDs rasos). Mantido como camada futura de descoberta, não de coleta diária.

---

### ÉPICO 2: Fetch Multi-Fonte — 2.1 a 2.7 concluídos

**Resumo:** Pipeline com coletores independentes (Remotive, We Work Remotely, Jobicy, opcional OpenAI Search); schema único e dedupe em `job_schema` + `fetch_pipeline`; Quality Guard (JD/título/empresa) e métricas `coverage` no JSON de saída. **2.7:** Dedup persistente em `data/seen_jobs.json` (`src/seen_jobs.py`), throttle de 20 novos JDs/run, `daily.yml` commita `seen_jobs.json` e timeout 10 min. Estrutura e componentes em [ARCHITECTURE.md](ARCHITECTURE.md). Lições de ambiente, Windows e testes: *ibid.* (Notas de desenvolvimento).

---

### ÉPICO 3: Fetch Estratégico — Greenhouse + Empresas-Alvo ✅ CONCLUÍDO

**Resumo:** Conectores Greenhouse, Lever e Ashby para empresas-alvo em `config/companies.yaml`; vagas ATS no pipeline com mesmo schema do Épico 2. Lista curada e expansível sem alterar código.

*(Detalhes dos itens 3.1–3.4 preservados em histórico do repo.)*

---

### Pipeline fetch → filter → score (hard filters + redução de tokens) ✅ CONCLUÍDO

**Objetivo:** Separar hard filters (gratuitos) do LLM e reduzir tokens nos prompts.

**Resumo:**

- **filter.py:** Lê raw de `data/raw/`, aplica location filter (expandido) + quality guard (JD/título/empresa), grava em `data/filtered/<mesmo nome>.json` com `jd_full` intacto. CLI: `--input <path>` ou `--date YYYY-MM-DD`. `data/filtered/` no `.gitignore`.
- **score.py:** Passa a ler de `data/filtered/` por padrão. Removido `apply_location_filter` (feito em filter.py). `check_eliminatorios` recebe objeto reduzido (title, company, location, jd_snippet 300 chars). `score_single_job` trunca JD a 3000 chars só no prompt, não no arquivo.
- **daily.yml:** Step "Filter jobs" entre Fetch e Score (`python src/filter.py --date $(date +%Y-%m-%d)`). Commit não inclui `data/filtered/`.

**Critérios de aceite:** filter.py gera filtered com jd_full intacto; score.py lê de filtered; eliminatórios com 4 campos; score trunca JD no prompt; data/filtered/ no .gitignore.

---

#### 3.5 Seed inicial (manual)

- Script `src/seed.py --source greenhouse|lever|ashby|all` que:
  - Roda o(s) coletor(es) indicados e normaliza para o schema único
  - Grava o bruto em `data/raw/seed_YYYY-MM-DD_HHMMSS.json` (timestamp para múltiplas runs no mesmo dia)
  - Popula `data/seen_jobs.json` com **todas** as vagas coletadas (sem throttle, sem filtro de 7 dias)
- Uso: **uma fonte por vez** (recomendado) — `--source greenhouse` → revisar `data/raw/seed_*.json` e `seen_jobs` → `--source lever` → revisar → `--source ashby`. Ou `--source all` de uma vez. A partir daí o pipeline diário só considera vagas novas.
- Objetivo: evitar que a primeira execução do pipeline encha o dia com dezenas de vagas antigas; seed = “histórico já visto”, daily = só o novo

**Plano de implementação (3.5)**

| Etapa | Descrição |
| :--- | :--- |
| **3.5.1** | CLI: `argparse` com `--source` (greenhouse \| lever \| ashby \| all) e `--dry-run`. Carregar `load_companies()`; montar lista de coletores ATS conforme a fonte (reutilizar lógica do `fetch.py`: empresas por ATS, lambdas que chamam `collect_*`). |
| **3.5.2** | Executar apenas os coletores selecionados e normalizar: chamar `run_pipeline(collectors_config)` só com esses coletores (sem Remotive, Jobicy, etc.). Sem `apply_seen_jobs_filter`, sem `filter_old_jobs`, sem throttle. |
| **3.5.3** | Gravar saída em `data/raw/seed_YYYY-MM-DD_HHMMSS.json`: mesmo formato do fetch (ex.: `fetched_at`, `date`, `coverage` mínimo, `jobs`). Garantir que `data/raw/` existe. |
| **3.5.4** | Para cada job na lista normalizada: `mark_seen(id_hash, source, title, company, seen)`; ao final `save_seen(seen)`. Assim o seed apenas "marca como já visto" sem passar pelo pipeline de filtros. |
| **3.5.5** | `--dry-run`: apenas listar fontes e quantidade de vagas que seriam coletadas (e opcionalmente o path do arquivo); não gravar JSON nem atualizar `seen_jobs`. |

---

## 📋 Fluxo de população (experiência esperada)

1. **Configurar conectores** — `config/companies.yaml`, `config/search.yaml`, etc.
2. **Popular banco bruto** — rodar coletores (manual: `fetch.py` ou `seed.py`); saída em `data/raw/`.
3. **Popular banco filtrado** — aplicar eliminatórios/quality guard aos brutos (manual ou via pipeline).
4. **Popular banco de matches com score** — rodar scoring sobre os filtrados; saída em `data/scored/`.

A população pode ser feita de forma **manual** (passo a passo, revisando entre etapas). O **pipeline diário** (`daily.yml`) armazena apenas as **novas** vagas (dedup via `seen_jobs` + throttle); o seed inicial (3.5) é a forma recomendada de “zerar” o histórico antes de deixar o daily rodar limpo.

---

## 🎯 Próximos passos (pós-seed)

- **Filtrar e score nas vagas atuais:** aplicar `filter.py` aos brutos já coletados (ex.: `python src/filter.py --input data/raw/seed_*.json`), depois `score.py --date YYYY-MM-DD` sobre `data/filtered/`. Pipeline: fetch → filter → score já em uso no daily.
- **Suporte a raw de seed no score:** score.py já lê de filtered; para seed, rodar filter.py com `--input` no raw desejado e em seguida score com `--date` (ou extensão futura de score para `--input` em filtered).

---

## 🔍 Investigação: o que cada coletor expõe (para decisão)

Resumo do que cada fonte já retorna ou pode retornar, para decidir enriquecimento (JD, localização, salário, títulos).

| Coletor | Título | Empresa | Localização | Salário | URL | JD (descrição) | Data | Observações |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Greenhouse** | ✅ API | ✅ config | ✅ `location.name` (detail) | ❌ | ✅ `absolute_url` | ✅ `content` (GET job/{id}) | ✅ `updated_at` | JD completo em 2ª chamada por vaga. Filtro: TITLE_KEYWORDS (PM, program manager, TPM, technical program). |
| **Lever** | ✅ `text` | ✅ config | ✅ `categories.location` | ✅ `salaryRange` | ✅ `hostedUrl` | ✅ `descriptionPlain` + lists + additional | ✅ `createdAt` (epoch ms) | JD rico na própria API. Filtro: mesmo TITLE_KEYWORDS. |
| **Ashby** | ✅ | ✅ config | ✅ string | ❌ | ✅ `jobUrl` | ✅ `descriptionPlain` ou strip HTML | ✅ `publishedAt` | JD na resposta única. Filtro: TITLE_KEYWORDS. |
| **Remotive** | ✅ | ✅ `company_name` | ✅ `candidate_required_location` | ✅ | ✅ | ✅ `description` | ✅ `publication_date` | Categorias fixas (product, project-management); recência 48h. Sem filtro por título no código. |
| **We Work Remotely** | ✅ (RSS "Company: Title") | ✅ parse do título | ❌ no RSS | ❌ | ✅ link | ⚠️ via link (não no RSS) | ✅ item pubDate | RSS; filtro por keywords no título. JD exige fetch da página. |
| **Jobicy** | ✅ | ✅ | ✅ | ✅ min/max/currency/period | ✅ | ✅ | ✅ pubDate | industry=product, 48h. |

**Decisões sugeridas:** (1) ATS (Greenhouse, Lever, Ashby) já trazem ou podem trazer JD completo na coleta — garantir que `jd_full` seja preenchido no schema. (2) We Work Remotely: decidir se vale fetch da página para JD ou manter só título/link. (3) Usar a análise exploratória de títulos (abaixo) para alinhar filtros e não perder vagas por título limitado.

---

## 📊 Análise exploratória de títulos de vagas

- **Objetivo:** Evitar perder vagas porque o filtro de título está limitado a poucos termos (ex.: "product manager", "program manager", "tpm", "technical program"). Descobrir quais outros títulos aparecem nos boards/APIs e ainda são relevantes para o perfil.
- **Atividade:** (1) Extrair **títulos únicos** de um ou mais runs (raw do fetch ou seed), por fonte. (2) Agrupar por similaridade ou frequência; revisar manualmente amostra. (3) Decidir: expandir `TITLE_KEYWORDS` nos coletores, ou mover lista para config (ex. `config/search.yaml`) e usar em todos. (4) Opcional: coletar **sem** filtro de título em um run de análise, salvar só títulos; depois escolher quais entram no filtro.
- **Entregável:** Lista de títulos (ou regex/keywords) documentada e, se fizer sentido, configurável em um único lugar; menos falsos negativos por título “diferente” (ex. "Product Lead", "Associate PM").

---

## 📍 Próximos Épicos

---

### ÉPICO 4: Preparação / qualidade

**Objetivo:** Corrigir riscos e reduzir duplicação antes do Épico 5 (Calibração de Scoring). Base estável para score, fetch e seed.

**Dependência:** Épico 3 concluído.

#### 4.1 score.py: excluir seed_*.json ao escolher raw do dia

- Hoje `glob(f"{date}*.json")` pode pegar arquivo de seed no mesmo dia e pontuar histórico em vez do fetch diário.
- Ao listar raw para score, ignorar arquivos cujo nome começa com `seed_`.

#### 4.2 Extrair carregamento/agrupamento de companies por ATS

- Mesma lógica em `fetch.py` e `seed.py` (YAML → listas greenhouse/lever/ashby). Extrair para um único lugar (ex. `fetch_pipeline` ou módulo) e consumir em ambos.

#### 4.3 Centralizar paths

- `config/search.yaml` já define `output.raw_dir`, `scored_dir`, etc., mas não é usado. Criar módulo que lê e expõe paths; fetch, score, generate, notify e seen_jobs passam a usar esse ponto único.

#### 4.4 Análise exploratória de títulos

- Realizar a análise exploratória de títulos de vagas (ver seção dedicada acima) para ampliar o filtro de títulos sem perder relevância e evitar perder vagas por lista limitada de keywords.

---

### ÉPICO 5: Calibração de Scoring

**Objetivo:** Garantir que o scoring reflete fit real, usando dados reais do Épico 2 como base.

**Dependência:** Épico 4 concluído. Épico 2 rodando com volume ≥ 20 vagas/dia por pelo menos 5 dias.

**Critério de aceite:**
- Concordância ≥ 80% entre score do LLM e avaliação manual em amostra de 30 vagas
- Distribuição de scores saudável (não concentrada em 85-92)
- Falsos positivos (score alto, vaga ruim) < 20%

#### 5.1 Avaliação manual de amostra

- Candidato avalia 30 vagas manualmente (fit 0-100 + motivo)
- Comparação com scores do LLM
- Identificação de padrões de erro

#### 5.2 Ajuste de pesos e prompt

- Revisar pesos em `config/search.yaml`
- Ajustar prompt de scoring com base nos padrões identificados
- Re-rodar scoring na mesma amostra para validar melhora

#### 5.3 Critérios eliminatórios revisados

- Validar se filtros atuais (localização, nível, idioma, tipo de cargo) estão corretos
- Adicionar red flags identificados na avaliação manual

---

### ÉPICO 6: Interface Streamlit

**Objetivo:** Interface local para visualizar vagas, gerar materiais de aplicação e dar feedback.

**Dependência:** Épico 5 concluído (scoring calibrado).

**Critério de aceite:** Jornada completa funcional — ver vagas → gerar currículo → download PDF → feedback.

#### 6.1 Tela principal — vagas do dia

- Lista de vagas pontuadas, ordenadas por score
- Card por vaga: título, empresa, score (badge colorido), salário, justificativa, link direto
- Cores: verde (≥ 90), amarelo (80-89)
- Seletor de data para ver dias anteriores

#### 6.2 Botão "Preparar aplicação"

- Chama `generate.py` com dados da vaga + perfil
- Loading indicator enquanto gera
- Preview do currículo e cover letter gerados
- Botão de download PDF

#### 6.3 Feedback por vaga

- Botões "👍 Bom match" / "👎 Não relevante" em cada card
- Salva em `data/feedback/YYYY-MM-DD.json`

#### 6.4 Histórico

- Lista de dias anteriores na sidebar
- Contadores: vagas vistas, aplicações geradas, feedbacks dados

---

### ÉPICO 7: Geração de Materiais

**Objetivo:** Gerar currículo e cover letter personalizados por vaga, com qualidade de aplicação real.

**Dependência:** Pode rodar em paralelo com Épico 6.

**Critério de aceite:** Materiais gerados para 5 vagas reais. Candidato considera ≥ 4 prontos para enviar com mínima edição.

#### 7.1 Currículo base modular

- `config/resume_base.md` com seções organizadas por relevância
- Seções: Summary (adaptável), Experience (bullets selecionáveis), Skills, Education

#### 7.2 Template de cover letter

- `config/cover_letter_template.md`
- Voz do candidato: direto, sem clichês, conecta experiência com a vaga
- Estrutura: abertura (por que essa empresa), fit (o que trago), fechamento

#### 7.3 Script generate.py

- Input: vaga (scored JSON) + resume_base + cover_letter_template + profile
- LLM: Claude Sonnet (qualidade de escrita)
- Output: currículo adaptado + cover letter adaptada em Markdown + PDF
- Regra: reorganizar e enfatizar, nunca inventar experiência

#### 7.4 Geração de PDF

- Markdown → PDF com layout limpo e profissional
- 1 página (currículo), 0.5-1 página (cover letter)
- Biblioteca: weasyprint

---

### ÉPICO 8: Pipeline Automatizado

**Objetivo:** Fetch + Score rodando automaticamente via GitHub Actions com o novo fetch multi-fonte.

**Dependência:** Épicos 2, 3 e 5 concluídos.

**Critério de aceite:** 5 dias consecutivos rodando sem intervenção. Cobertura ≥ 20 vagas/dia consistente.

#### 8.1 Atualização do daily.yml

- Remover dependência de `OPENAI_API_KEY` do step de fetch
- Timeout: aumentar para 10 min (múltiplas fontes)
- Step de fetch agora roda coletores em paralelo

#### 8.2 Tratamento de falhas

- Se uma fonte falhar, pipeline continua com as demais
- Retry 1x por fonte se timeout
- Commit de log de erro se todas as fontes falharem

#### 8.3 Alertas por email (PERFECT_MATCH)

- `notify.py` envia email se score ≥ 95
- Máximo 1 email/dia (agrupa todos os PERFECT_MATCH)
- Via Gmail SMTP (App Password)

---

### ÉPICO 9: Feedback Loop

**Objetivo:** Feedback do usuário alimenta o scoring das próximas rodadas.

**Dependência:** Épicos 6 e 8 rodando.

**Critério de aceite:** Scoring melhora visivelmente após 2 semanas de feedback (menos falsos positivos/negativos).

#### 9.1 Agregação de feedback

- Script lê todos `data/feedback/*.json`
- Gera resumo de padrões: que tipo de vaga o candidato rejeita? que tipo aceita?

#### 9.2 Feedback no prompt de scoring

- Resumo de feedback incluído como contexto no prompt do `score.py`
- Atualização manual (v1) — candidato revisa resumo antes de incluir

#### 9.3 Persistência no repositório

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
- **discover.py:** Script manual para prospectar novas empresas-alvo via queries em boards ATS (Greenhouse, Lever, Ashby); dedupe contra companies.yaml; sem integração com o pipeline diário.
- **discover.py semanal via Actions:** Automação da descoberta de novas empresas-alvo

---

**Última atualização:** Fev 2026