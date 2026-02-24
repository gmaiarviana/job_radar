# ROADMAP - Job Radar

📡 **Status:** Épico 1 concluído. Épico 2 concluído (2.1–2.6): multi-fonte, Quality Guard e métricas de cobertura. Próximo: **Épico 2.7** (dedup persistente + throttle JD), depois Épico 3 (Greenhouse/empresas-alvo).

> **Filosofia:** POC → Protótipo → MVP. Validar cada etapa antes de avançar.

---

## ✅ Concluído

### ÉPICO 1: Fetch + Score (Arquitetura Base)

**Objetivo:** Validar a arquitetura fetch → score → commit com dados reais.

**Resumo:** Pipeline fetch (OpenAI web search) + score (Claude Haiku) + GitHub Actions; config em `config/profile.md` e `config/search.yaml`; dedupe e filtros eliminatórios. Detalhes em [ARCHITECTURE.md](ARCHITECTURE.md).

**Decisão:** OpenAI web search desativado como fonte primária (volume baixo, JDs rasos). Mantido como camada futura de descoberta, não de coleta diária.

---

### ÉPICO 2: Fetch Multi-Fonte — 2.1 a 2.6 concluídos

**Resumo:** Pipeline com coletores independentes (Remotive, We Work Remotely, Jobicy, opcional OpenAI Search); schema único e dedupe em `job_schema` + `fetch_pipeline`; Quality Guard (JD/título/empresa) e métricas `coverage` no JSON de saída. Estrutura e componentes em [ARCHITECTURE.md](ARCHITECTURE.md). Lições de ambiente, Windows e testes: *ibid.* (Notas de desenvolvimento).

---

## 📍 Próximos Épicos

---

### ÉPICO 2.7: Dedup Persistente + Throttle JD (evolução do pipeline 2.x)

**Objetivo:** Camada de dedup persistente e universal para todas as fontes, com throttle de JD para fontes ATS.

**Dependência:** Épico 2 concluído (está).

**Critério de aceite global:**
- `data/seen_jobs.json` é criado e atualizado a cada run
- Vagas já vistas não são reprocessadas em runs subsequentes
- Pipeline não passa de 20 novos JDs por run
- GitHub Actions commita o arquivo junto com os raw JSONs
- Os coletores existentes (Remotive, Jobicy, WWR) continuam funcionando sem mudança de interface

#### 2.7.1 — `src/seen_jobs.py` (módulo isolado)

Responsabilidade única: ler, checar e persistir o `seen_jobs.json`. Nenhum outro módulo acessa o arquivo diretamente.

Interface mínima:
- `load_seen() -> dict` — lê `data/seen_jobs.json`
- `is_seen(id_hash: str, seen: dict) -> bool` — checa se já foi visto
- `mark_seen(id_hash, source, title, company, seen: dict)` — adiciona entrada
- `save_seen(seen: dict)` — persiste no arquivo

Critério de aceite: módulo importável, sem efeitos colaterais no import, arquivo criado com `{}` se não existir.

#### 2.7.2 — Integração no `fetch_pipeline.py` / `fetch.py`

Substitui o `remove_duplicates` (janela 7 dias) pela checagem via `seen_jobs`. Fluxo:

1. `run_pipeline()` → jobs normalizados com JD já no schema
2. `check_seen_jobs()` → separa novos vs já vistos
3. `throttle(max_new=20)` → limita novos para este run
4. `mark_all_new_as_seen()` → persiste seen_jobs
5. `filter_old_jobs()` → ainda faz sentido para fontes com data
6. `apply_quality_guard()` → sem mudança

Critério de aceite:
- Run 1: até 20 vagas novas processadas; restantes ignoradas com log
- Run 2 com mesmo arquivo raw: 0 vagas novas (todas já no seen_jobs)
- O `remove_duplicates` antigo pode ser mantido como fallback ou removido na implementação

#### 2.7.3 — Atualização do `daily.yml`

Adicionar `data/seen_jobs.json` ao stage do commit final e aumentar timeout do job de 5 para 10 minutos.

```yaml
git add data/raw/ data/scored/ data/seen_jobs.json
```

Critério de aceite: após um run no Actions, o `seen_jobs.json` aparece no commit.

**Plano de execução (ordem sequencial):**

| # | Escopo | Dependência | Critério de fechamento |
|---|--------|-------------|------------------------|
| **Prompt 1** | Criar `src/seen_jobs.py` com `load_seen`, `is_seen`, `mark_seen`, `save_seen` | — | Import sem erro; arquivo `{}` criado se não existir |
| **Prompt 2** | Integrar em `fetch_pipeline.py` + `fetch.py`: `apply_seen_jobs_filter`, throttle 20, output_data com `total_already_seen` e `total_throttled` | Prompt 1 | `python src/fetch.py` ok; 2ª execução com `total_already_seen` > 0; `seen_jobs.json` em `data/` |
| **Prompt 3** | `.github/workflows/daily.yml`: add `data/seen_jobs.json` ao `git add`; timeout 5→10 min | Prompt 2 | YAML válido; após run no Actions, `seen_jobs.json` no commit |

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