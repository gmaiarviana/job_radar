# ROADMAP - Job Radar

📡 **Status:** Épico 1 concluído. Épico 2 concluído (2.1–2.7). Épico 3 concluído (Greenhouse, Lever, Ashby). Próximo: **Épico 4** (Preparação / qualidade).

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