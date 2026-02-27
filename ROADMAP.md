# ROADMAP - Job Radar

📡 **Status:** Pipeline completo (fetch → filter → score). Épico 6 concluído. Próximo: Épico 7 (Expansão de Coleta).

> **Filosofia:** POC → Protótipo → MVP. Validar cada etapa antes de avançar. Qualidade antes de volume.

---

## ✅ Concluído

**Épicos 1–4:** Pipeline fetch multi-fonte, schema único, dedup, filtros (título + localização), scoring em dois estágios, GitHub Actions diário, seed ATS, eval (`src/eval/`), paths (`src/paths.py`). Ver [ARCHITECTURE.md](ARCHITECTURE.md).

**Épico 5 — Qualidade de scoring:** Prompt em 2 chamadas (analyze_job → compute_ceiling → score_with_analysis), validado no seed; ceiling em Python; arquivos scored por data/hora; filter/score com exclusão de `*_discarded.json` e `seed_*`. Pipeline end-to-end validado (fetch → filter → score).

**Épico 6 — UI Funcional Mínima:** Streamlit com duas abas. Aba "Vagas": tabela unificada (pipeline + manuais) com score, veredito (APLICAR/AVALIAR/PULAR), badge de fonte, filtro por data, expand com análise completa. Aba "LinkedIn": links de busca + paste-and-score (analyze_job → compute_ceiling → score_with_analysis) com persistência em `data/scored/manual_*.json` e `seen_jobs.json`. Config: `config/linkedin_searches.yaml`.

**Épico 7.1 — OpenAI search no GitHub Actions:** Habilitado. OPENAI_API_KEY configurada nos secrets do Actions. Coletor já roda no pipeline diário.

---

## 📍 Próximos Épicos

### ÉPICO 7: Expansão de Coleta

**Objetivo:** Aumentar volume, diversidade e qualidade das vagas coletadas — mais fontes, mais empresas remote-friendly, mais cobertura LATAM/worldwide.

**Dependência:** Épico 6 rodando. OpenAI search ativo no Actions.

**Critério de aceite global:** Pipeline diário gerando ≥ 5 vagas que passam nos filtros (location + quality) por pelo menos 3 dias consecutivos.

#### ✅ 7.1 OpenAI search no GitHub Actions
Habilitado. OPENAI_API_KEY configurada nos secrets do Actions. Coletor já roda no pipeline diário.

#### 7.2 Novos coletores (APIs validadas)

**Remote OK:**
- Endpoint: `GET https://remoteok.com/api` → JSON array, sem auth
- Campos: id, date, company, position, tags, description, location, salary_min, salary_max, apply_url
- Filtro client-side por tags (ex: "product", "management", "exec")
- Requisito legal: mencionar Remote OK como fonte e linkar URL original
- Critério de aceite: coletor em `src/collectors/remoteok.py`, integrado em fetch.py, retorna vagas PM/TPM das últimas 48h

**Get on Board:**
- API pública: `https://api-doc.getonbrd.com` — search por texto livre + browse por categoria, paginação (per_page, page), sem auth
- Foco LATAM nativo (Chile, México, Colômbia, Brasil, Argentina)
- Critério de aceite: coletor em `src/collectors/getonboard.py`, integrado em fetch.py, busca por "product manager" remote

#### 7.3 Expandir companies.yaml

Adicionar empresas validadas como remote-first com ATS suportado:
- Zapier (Greenhouse) — SaaS workflow automation, remote worldwide
- Doist (Greenhouse) — Produtividade (Todoist/Twist), remote global
- dLocal (Lever) — Fintech LATAM (AR, BR, UY), PM roles confirmados
- Stripe (Greenhouse) — Fintech, LATAM confirmado em boards
- Loadsmart (Greenhouse) — Logistics SaaS, TPM LATAM explícito
- Deel (Ashby) — Remote-first por definição; slug anterior deu 404 como Greenhouse, pesquisa indica Ashby

Critério de aceite: empresas adicionadas no companies.yaml com ats e ats_id corretos; seed valida que pelo menos 4 de 6 retornam vagas (slug OK).

#### 7.4 Renomear LinkedIn → Busca Manual

- Renomear `config/linkedin_searches.yaml` → `config/manual_searches.yaml`
- Atualizar app.py: aba "LinkedIn" → "Busca Manual"; referência ao novo yaml
- Adicionar links de fontes sem API:
  - Wellfound (AngelList): remote PM filter
  - YC Work at a Startup: remote PM filter
  - Product Jobs Anywhere: LATAM PM filter
  - Remote Rocketship: LATAM PM filter
- Manter links LinkedIn existentes (são links manuais também)
- Critério de aceite: aba funcional com novo nome e links adicionais; yaml antigo removido ou renomeado

#### 7.5 Remover penalty `outsourcing_context` do scoring

- Remover `outsourcing_context` de CEILING_BY_PENALTY em score.py
- Remover do prompt de analyze_job (Chamada 1): penalties passa a ter apenas `seniority_gap` e `domain_gap_core`
- Atualizar compute_ceiling: lógica de 2+ penalties continua (agora com 2 penalties possíveis, o máximo de activas é 2)
- Atualizar testes em src/eval/test_scoring.py para refletir 2 penalties
- Critério de aceite: testes passam; scoring não penaliza vagas em consultorias

#### 7.6 Seed das novas fontes

- Rodar seed para Remote OK e Get on Board (popular seen_jobs, evitar engarrafamento no primeiro run)
- Rodar seed para novas empresas do companies.yaml (7.3)
- Critério de aceite: seen_jobs atualizado; data/raw/ com seed das novas fontes

**Ordem de execução sugerida (para implementação futura):** 7.5 → 7.3 + 7.4 (paralelo) → 7.2 → 7.6

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

### ÉPICO 9: Polimento de UI — Cards, Detalhes e Cópia

**Objetivo:** Melhorar a experiência visual dos cards de vagas e facilitar extração de conteúdo para uso externo (Claude, docs).

**Dependência:** Épico 6 concluído.

**Critério de aceite:** Cards com hierarquia visual limpa; ceiling removido da UI; botões de cópia funcionais (JD + relatório); botão "Avaliar outra" funcional na aba LinkedIn.

#### 9.1 Redesign da seção de detalhes

- Substituir a barra "Ver detalhes (ceiling, requisitos, seniority, gap)" por algo mais limpo (ex: apenas "Detalhes" ou ícone de expand)
- Remover exibição de ceiling e motivo do teto da UI (manter nos JSONs para debug/eval)
- Reordenar conteúdo expandido: justificativa e principal gap primeiro, requisitos e seniority depois

#### 9.2 Botões de cópia (JD + Relatório)

- Botão "Copiar JD" no detalhe expandido: copia `jd_full` como markdown para clipboard
- Botão "Copiar Relatório" no detalhe expandido: copia score + justificativa + main_gap + requisitos + seniority formatados em markdown
- Funcional tanto na aba Vagas quanto na aba LinkedIn (resultado do paste-and-score)

#### 9.3 Botão "Avaliar outra vaga" na aba LinkedIn

- Após scoring manual exibir resultado + botão "Avaliar outra vaga"
- Ao clicar: limpar formulário e resultado, pronto para nova entrada
- Sem necessidade de refresh da página

---

### ÉPICO 10: UX Completa

**Objetivo:** Polimento da UI — feedback e histórico consolidado.

**Dependência:** Épico 6 rodando.

**Critério de aceite:** Feedback por vaga funcional; histórico com contadores.

#### 10.1 Feedback por vaga (👍/👎)

- Botões em cada card (manual e automático)
- Salva em `data/feedback/YYYY-MM-DD.json`

#### 10.2 Histórico com contadores

- Lista de dias anteriores na sidebar
- Contadores: vagas vistas, feedbacks dados, avaliações manuais

---

### ÉPICO 11: Pipeline Automatizado Estável

**Objetivo:** Fetch + Score rodando de forma confiável via GitHub Actions.

**Dependência:** Épicos 5 e 6 concluídos.

**Critério de aceite:** 5 dias consecutivos sem intervenção. Cobertura ≥ 10 vagas novas/dia.

#### 11.1 Tratamento de falhas por coletor

- Se uma fonte falhar, pipeline continua com as demais
- Retry 1x por fonte se timeout
- Commit de log de erro se todas falharem

---

### ÉPICO 12: Geração de Materiais

**Objetivo:** Gerar currículo e cover letter personalizados por vaga, com botão na UI.

**Dependência:** Scoring estável por ≥ 2 semanas.

**Critério de aceite:** Materiais gerados para 5 vagas reais. ≥ 4 prontos para enviar com mínima edição.

#### 12.1 Currículo base modular (`config/resume_base.md`)
#### 12.2 Template de cover letter (`config/cover_letter_template.md`)
#### 12.3 Script generate.py (Claude Sonnet)
#### 12.4 Geração de PDF (weasyprint)
#### 12.5 Botão "Preparar aplicação" na UI

- Em cada card com score ≥ 70
- Loading → preview → download PDF

---

### ÉPICO 13: Feedback Loop

**Objetivo:** Feedback do usuário alimenta o scoring.

**Dependência:** Épicos 9 e 10 rodando com dados de ≥ 2 semanas.

**Critério de aceite:** Scoring melhora visivelmente após 2 semanas de feedback.

#### 13.1 Agregação de feedback (padrões de aceite/rejeição)
#### 13.2 Feedback no prompt de scoring (contexto extra)
#### 13.3 Persistência no repositório (Actions lê feedback)

---

---

Backlog, itens postergados e ideias futuras → [docs/governance/backlog.md](docs/governance/backlog.md)

---

**Última atualização:** Fev 2026
