# ROADMAP - Job Radar

📡 **Status:** Épico 1 concluído. Épico 2 concluído (2.1–2.7): multi-fonte, Quality Guard, dedup persistente e throttle. Próximo: **Épico 3** (Greenhouse/empresas-alvo).

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

## 📍 Próximos Épicos

---

### ÉPICO 3: Fetch Estratégico — Greenhouse + Empresas-Alvo *(3.1–3.4 ✅)*

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

#### 3.2 Conector Greenhouse — ✅ CONCLUÍDO

- Coletor `src/collectors/greenhouse.py`: `collect_greenhouse(companies)`; lista flat de empresas com `ats == "greenhouse"`; GET boards/{ats_id}/jobs → filtro por título (product manager, program manager, tpm, technical program) → GET job/{id} para content; 0,5s delay; 404/erro logado como WARN; saída no mesmo schema (title, company, location, salary=null, url, description, date).

#### 3.3 Conector Lever — ✅ CONCLUÍDO

- Coletor `src/collectors/lever.py`: `collect_lever(companies)`; GET postings/{ats_id}?mode=json; filtro por título (product manager, program manager, tpm, technical program); JD = descriptionPlain + blocos lists (header + content sem HTML); 0,5s delay; 404/erro WARN; saída: title, company, location (categories.location), salary (salaryRange), url (hostedUrl), description, date (createdAt epoch ms → ISO).

#### 3.4 Conector Ashby — ✅ CONCLUÍDO

- Coletor `src/collectors/ashby.py`: `collect_ashby(companies)`; POST `jobs.ashbyhq.com/.../job-posting/list` com body `{"organizationHostedJobsPageName": "{ats_id}"}`; mapeamento flexível (jobs/results/jobPostings; title/text; jobUrl/url; descriptionPlain/descriptionHtml; publishedAt/updatedAt); filtro por título; descrição sem HTML; 0,5s delay; 404/erro WARN; saída no mesmo schema.

#### 3.5 Descoberta manual (src/discover.py)

- **Objetivo:** Script separado para prospectar novas empresas-alvo; sem integração com o pipeline diário; revisão manual obrigatória antes de adicionar ao `companies.yaml`.
- **Uso:** Rodar manualmente quando quiser expandir a lista de empresas (ex.: `python src/discover.py` ou `python src/discover.py --ats greenhouse`).
- **Estratégia:** Queries de busca (ex.: Google) com `site:boards.greenhouse.io`, `site:jobs.lever.co`, `site:jobs.ashbyhq.com`; filtros por localização (remote, LATAM) e título (Product Manager, TPM). Opcional: limitar por ATS (`--ats greenhouse|lever|ashby`).
- **Output:** Lista de sugestões com empresa + ATS + ats_id (slug) para revisão; formato legível (JSON ou texto) em `data/discover/` ou stdout; nenhuma alteração automática em `companies.yaml`.
- **Implementação sugerida:** Módulo `src/discover.py` com função principal que aceita args (ATS opcional, limite de resultados); usa requests/selenium ou API de busca para obter URLs de job boards; extrai domínio/slug do ATS a partir da URL; dedupe contra empresas já presentes no `companies.yaml`; imprime ou grava sugestões. Não chamado por `fetch.py` nem por `daily.yml`.

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