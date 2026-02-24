# ROADMAP - Job Radar

📡 **Status:** Épico 1 concluído. Épico 2 concluído (2.1–2.7). Épico 3 concluído (Greenhouse, Lever, Ashby). Próximo: **Épico 4** (Calibração de Scoring).

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

## 📍 Próximos Épicos

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
- **discover.py:** Script manual para prospectar novas empresas-alvo via queries em boards ATS (Greenhouse, Lever, Ashby); dedupe contra companies.yaml; sem integração com o pipeline diário.
- **discover.py semanal via Actions:** Automação da descoberta de novas empresas-alvo

---

**Última atualização:** Fev 2026