# ROADMAP - Job Radar

📡 **Status:** Pipeline completo (fetch → filter → score). Épico 6 concluído. Próximo: Épico 7 (Expansão de Coleta).

> **Filosofia:** POC → Protótipo → MVP. Validar cada etapa antes de avançar. Qualidade antes de volume.

---

## ✅ Concluído

**Épicos 1–4:** Pipeline fetch multi-fonte, schema único, dedup, filtros (título + localização), scoring em dois estágios, GitHub Actions diário, seed ATS, eval (`src/eval/`), paths (`src/paths.py`). Ver [ARCHITECTURE.md](ARCHITECTURE.md).

**Épico 5 — Qualidade de scoring:** Prompt em 2 chamadas (analyze_job → compute_ceiling → score_with_analysis), validado no seed; ceiling em Python; arquivos scored por data/hora; filter/score com exclusão de `*_discarded.json` e `seed_*`. Pipeline end-to-end validado (fetch → filter → score).

**Épico 6 — UI Funcional Mínima:** Streamlit com duas abas. Aba "Vagas": tabela unificada (pipeline + manuais) com score, veredito (APLICAR/AVALIAR/PULAR), badge de fonte, filtro por data, expand com análise completa. Aba "LinkedIn": links de busca + paste-and-score (analyze_job → compute_ceiling → score_with_analysis) com persistência em `data/scored/manual_*.json` e `seen_jobs.json`. Config: `config/linkedin_searches.yaml`.

---

## 📍 Próximos Épicos

### ÉPICO 7: Expansão de Coleta

**Objetivo:** Aumentar volume, diversidade e qualidade das vagas coletadas.

**Dependência:** Épico 6 rodando.

#### 7.1 Seed exploratório (títulos)

- Rodar seed ATS SEM filtro de título (flag --no-title-filter ou equivalente) para capturar todos os cargos disponíveis nas empresas-alvo
- Extrair lista de títulos únicos + contagem por fonte
- Analisar via NotebookLM: identificar títulos relevantes fora do filtro atual (ex: "Product Lead", "Associate PM", "Group PM", "Chief of Staff")
- Decisão: expandir TITLE_KEYWORDS nos coletores ou centralizar em config/search.yaml

#### 7.2 Novos boards e plataformas de recrutamento

- Pesquisar fontes via Perplexity/ChatGPT/Grok: job boards com vagas remotas LATAM/worldwide para PM/TPM
- Pesquisar plataformas de recrutamento usadas por empresas de qualidade (ex: Dover, Wellfound, Work at a Startup/YC, etc.)
- Para cada fonte/plataforma: verificar se tem API pública ou RSS
  - Com API/RSS: prototipar coletor, testar com 10-20 vagas, avaliar relevância antes de integrar
  - Sem API/RSS: adicionar como link manual no linkedin_searches.yaml (acesso manual + paste-and-score)
- Identificar empresas que usam essas plataformas para expandir a lista de empresas-alvo (7.3)
- Priorizar fontes com vagas LATAM/Worldwide confirmadas por teste real

#### 7.3 Revalidar e expandir companies.yaml

- Revalidar empresas com "404 no seed": checar se slug mudou ou se migraram de ATS
- Expandir lista com novas empresas-alvo: sinais das plataformas (7.2), vagas avaliadas via paste-and-score, pesquisa direta
- Atualizar config/companies.yaml

---

### ÉPICO 8: Deploy Online (Streamlit Community Cloud)

**Objetivo:** App acessível de qualquer computador, com persistência de scores manuais via GitHub API.

**Dependência:** Épico 6 concluído.

**Critério de aceite:** App funcional no Streamlit Cloud; paste-and-score persiste `manual_*.json` no repo via GitHub Contents API; vagas do pipeline visíveis normalmente.

#### 8.1 Camada de escrita GitHub API

- Função utilitária em `src/github_api.py`: commit de arquivo via GitHub Contents API (PUT)
- Token via env/secrets (`GITHUB_TOKEN`)

#### 8.2 Integrar persistência no app.py

- Após salvar `manual_*.json`, commitar via `github_api.py`
- Fallback gracioso se token ausente (funciona local-only)

#### 8.3 Configuração Streamlit Community Cloud (manual)

- Conectar repo, configurar secrets, validar

#### 8.4 Documentação

- ARCHITECTURE: deploy + github_api.py na tabela
- README: acesso online + variáveis de ambiente

---

### ÉPICO 9: UX Completa

**Objetivo:** Polimento da UI — feedback e histórico consolidado.

**Dependência:** Épico 6 rodando.

**Critério de aceite:** Feedback por vaga funcional; histórico com contadores.

#### 9.1 Feedback por vaga (👍/👎)

- Botões em cada card (manual e automático)
- Salva em `data/feedback/YYYY-MM-DD.json`

#### 9.2 Histórico com contadores

- Lista de dias anteriores na sidebar
- Contadores: vagas vistas, feedbacks dados, avaliações manuais

---

### ÉPICO 10: Pipeline Automatizado Estável

**Objetivo:** Fetch + Score rodando de forma confiável via GitHub Actions.

**Dependência:** Épicos 5 e 6 concluídos.

**Critério de aceite:** 5 dias consecutivos sem intervenção. Cobertura ≥ 10 vagas novas/dia.

#### 10.1 Tratamento de falhas por coletor

- Se uma fonte falhar, pipeline continua com as demais
- Retry 1x por fonte se timeout
- Commit de log de erro se todas falharem

---

### ÉPICO 11: Geração de Materiais

**Objetivo:** Gerar currículo e cover letter personalizados por vaga, com botão na UI.

**Dependência:** Scoring estável por ≥ 2 semanas.

**Critério de aceite:** Materiais gerados para 5 vagas reais. ≥ 4 prontos para enviar com mínima edição.

#### 11.1 Currículo base modular (`config/resume_base.md`)
#### 11.2 Template de cover letter (`config/cover_letter_template.md`)
#### 11.3 Script generate.py (Claude Sonnet)
#### 11.4 Geração de PDF (weasyprint)
#### 11.5 Botão "Preparar aplicação" na UI

- Em cada card com score ≥ 70
- Loading → preview → download PDF

---

### ÉPICO 12: Feedback Loop

**Objetivo:** Feedback do usuário alimenta o scoring.

**Dependência:** Épicos 9 e 10 rodando com dados de ≥ 2 semanas.

**Critério de aceite:** Scoring melhora visivelmente após 2 semanas de feedback.

#### 12.1 Agregação de feedback (padrões de aceite/rejeição)
#### 12.2 Feedback no prompt de scoring (contexto extra)
#### 12.3 Persistência no repositório (Actions lê feedback)

---

Backlog, itens postergados e ideias futuras → [docs/governance/backlog.md](docs/governance/backlog.md)

---

**Última atualização:** Fev 2026
