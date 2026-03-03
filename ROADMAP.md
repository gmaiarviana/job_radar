# ROADMAP - Job Radar

📡 **Status:** Pipeline completo (fetch → filter → score → dashboard). Épico 8 concluído. Próximo: Épico 7.3/7.6 (Expansão de Coleta) e Épico 9 (Polimento de UI).

> **Filosofia:** POC → Protótipo → MVP. Validar cada etapa antes de avançar. Qualidade antes de volume.

---

## ✅ Concluído

**Épicos 1–4:** Pipeline fetch multi-fonte, schema único, dedup, filtros (título + localização), scoring em dois estágios, GitHub Actions diário, seed ATS, eval (`src/eval/`), paths (`src/paths.py`). Ver [ARCHITECTURE.md](ARCHITECTURE.md).

**Épico 5 — Qualidade de scoring:** Prompt em 2 chamadas (analyze_job → compute_ceiling → score_with_analysis), validado no seed; ceiling em Python; arquivos scored por data/hora; filter/score com exclusão de `*_discarded.json` e `seed_*`. Pipeline end-to-end validado (fetch → filter → score).

**Épico 6 — UI Funcional Mínima:** Streamlit com duas abas. Aba "Vagas": tabela unificada (pipeline + manuais) com score, veredito (APLICAR/AVALIAR/PULAR), badge de fonte, filtro por data, expand com análise completa. Aba "Busca Manual": links de busca + paste-and-score (analyze_job → compute_ceiling → score_with_analysis) com persistência em `data/scored/manual_*.json` e `seen_jobs.json`. Config: `config/manual_searches.yaml`.

**Épico 7.1 — OpenAI search no GitHub Actions:** Habilitado. OPENAI_API_KEY configurada nos secrets do Actions. Coletor já roda no pipeline diário.

**Épico 7.4 — Renomear LinkedIn → Busca Manual:** config renomeado para `manual_searches.yaml`; aba "Busca Manual", subtítulo "Links de busca" e docs atualizados.

**Épico 8 — Deploy Online (GitHub Pages):** Dashboard read-only em GitHub Pages; `build_frontend_data.py` consolida scored em `data/jobs.json`; o workflow copia para `docs/data/jobs.json` para o Pages servir; step no Actions gera e commita automaticamente.

**Infra — GitHub Pages (Hello World):** landing page mínima movida para `docs/index.html` para servir na URL raiz via GitHub Pages (source: branch `main`, pasta `/docs/`).

---

## 📍 Próximos Épicos

### ÉPICO 7: Expansão de Coleta

**Objetivo:** Aumentar volume, diversidade e qualidade das vagas coletadas — mais fontes, mais empresas remote-friendly, mais cobertura LATAM/worldwide.

**Dependência:** Épico 6 rodando. OpenAI search ativo no Actions.

**Critério de aceite global:** Pipeline diário gerando ≥ 5 vagas que passam nos filtros (location + quality) por pelo menos 3 dias consecutivos.

#### ✅ 7.1 OpenAI search no GitHub Actions
Habilitado. OPENAI_API_KEY configurada nos secrets do Actions. Coletor já roda no pipeline diário.

#### ✅ 7.2 Novos coletores (APIs validadas)

**Concluído:** Remote OK (`src/collectors/remoteok.py`) e Get on Board (`src/collectors/getonboard.py`) integrados em fetch.py. Remote OK: API pública, filtro por título/cargo (TITLE_KEYWORDS globais para PM/TPM e afins), janela de 7 dias, atribuição "Source: Remote OK" nos logs. Get on Board: API search jobs (query=product manager, remote=true), filtro por título PM/TPM (keywords centralizadas incluindo LATAM), janela de 7 dias, paginação até 5 páginas, foco LATAM.

#### 7.3 Expandir companies.yaml — **Pendente**

Adicionar empresas validadas como remote-first com ATS suportado:
- Zapier (Greenhouse) — SaaS workflow automation, remote worldwide
- Doist (Greenhouse) — Produtividade (Todoist/Twist), remote global
- dLocal (Lever) — Fintech LATAM (AR, BR, UY), PM roles confirmados
- Stripe (Greenhouse) — Fintech, LATAM confirmado em boards
- Loadsmart (Greenhouse) — Logistics SaaS, TPM LATAM explícito
- Deel (Ashby) — Remote-first por definição; slug anterior deu 404 como Greenhouse, pesquisa indica Ashby

Critério de aceite: empresas adicionadas no companies.yaml com ats e ats_id corretos; seed valida que pelo menos 4 de 6 retornam vagas (slug OK).  
*Estado:* Nenhuma das seis empresas acima está ativa em `config/companies.yaml` (Deel está comentada por 404).

#### ✅ 7.4 Revisar buscas manuais e renomear LinkedIn → Busca Manual

**Concluído:** Revisão de botões (8 entries). `config/linkedin_searches.yaml` renomeado para `config/manual_searches.yaml`. Aba "LinkedIn" → "Busca Manual"; subtítulo "Links de busca"; caption e docs atualizados.

#### ✅ 7.5 Remover penalty `outsourcing_context` do scoring
Concluído: penalty removida de CEILING_BY_PENALTY e do prompt de analyze_job; penalties apenas `seniority_gap` e `domain_gap_core`. Testes atualizados (4 cenários + 2 auto-eliminate); todos passam.

#### ✅ 7.6 Seed das novas fontes

- Remote OK e Get on Board populam `seen_jobs` via runs normais de `fetch.py` (sem necessidade de seed dedicado).
- Após expandir `companies.yaml` (7.3), as novas empresas ATS serão naturalmente “seedadas” nos primeiros runs de `fetch.py`.
- Critério de aceite: `seen_jobs` traz entradas de `remoteok` e (quando houver vagas) `getonboard`; novas empresas de 7.3 passam a aparecer sem gargalo após alguns runs do `fetch.py`.

**Ordem de execução sugerida (para implementação futura):** 7.5 → 7.3 + 7.4 (paralelo) → 7.2 → 7.6

---

### ✅ ÉPICO 8: Deploy Online (GitHub Pages)

**Concluído:** Dashboard read-only via GitHub Pages. `src/build_frontend_data.py` consolida `data/scored/` em `data/jobs.json` (últimos 14 dias); o workflow copia para `docs/data/jobs.json` para o Pages. `docs/index.html` renderiza cards com score, veredito, filtro por data e detalhes expandíveis. Pipeline diário (Actions) gera o JSON automaticamente e commita.

---

### ÉPICO 9: Polimento de UI — Cards, Detalhes e Cópia

**Objetivo:** Melhorar a experiência visual dos cards de vagas e facilitar extração de conteúdo para uso externo (Claude, docs).

**Dependência:** Épico 6 concluído.

**Critério de aceite:** Cards com hierarquia visual limpa; ceiling removido da UI; botões de cópia funcionais (JD + relatório); botão "Avaliar outra" funcional na aba Busca Manual.

#### 9.1 Redesign da seção de detalhes

- Substituir a barra "Ver detalhes (ceiling, requisitos, seniority, gap)" por algo mais limpo (ex: apenas "Detalhes" ou ícone de expand)
- Remover exibição de ceiling e motivo do teto da UI (manter nos JSONs para debug/eval)
- Reordenar conteúdo expandido: justificativa e principal gap primeiro, requisitos e seniority depois

#### 9.2 Botões de cópia (JD + Relatório)

- Botão "Copiar JD" no detalhe expandido: copia `jd_full` como markdown para clipboard
- Botão "Copiar Relatório" no detalhe expandido: copia score + justificativa + main_gap + requisitos + seniority formatados em markdown
- Funcional tanto na aba Vagas quanto na aba Busca Manual (resultado do paste-and-score)

#### 9.3 Botão "Avaliar outra vaga" na aba Busca Manual

- Após scoring manual exibir resultado + botão "Avaliar outra vaga"
- Ao clicar: limpar formulário e resultado, pronto para nova entrada
- Sem necessidade de refresh da página

---

### ÉPICO 10: Persistência Online (GitHub API)

**Objetivo:** Habilitar escrita a partir do dashboard online — paste-and-score e feedback persistem no repo via GitHub Contents API, sem necessidade de acesso local.

**Dependência:** Épico 8 (dashboard read-only) concluído. Épico 9 (UI polish) recomendado mas não bloqueante.

**Critério de aceite:** Paste-and-score no dashboard online grava `manual_*.json` no repo via GitHub API. Vagas manuais aparecem na listagem após refresh.

#### 10.1 Camada de escrita GitHub API

- Função utilitária em `src/github_api.py`: commit de arquivo via GitHub Contents API (PUT)
- Token via env/secrets (`GITHUB_TOKEN`)

#### 10.2 Integrar persistência no dashboard

- Após scoring manual, commitar `manual_*.json` via `github_api.py`
- Fallback gracioso se token ausente (funciona read-only)

#### 10.3 Atualizar `build_frontend_data.py`

- Incluir `manual_*.json` commitados via API no consolidado

#### 10.4 Documentação

- ARCHITECTURE: `github_api.py` na tabela de componentes
- README: variáveis de ambiente (`GITHUB_TOKEN`)

---

### ÉPICO 11: UX Completa

**Objetivo:** Polimento da UI — feedback e histórico consolidado.

**Dependência:** Épico 6 rodando.

**Critério de aceite:** Feedback por vaga funcional; histórico com contadores.

#### 11.1 Feedback por vaga (👍/👎)

- Botões em cada card (manual e automático)
- Salva em `data/feedback/YYYY-MM-DD.json`

#### 11.2 Histórico com contadores

- Lista de dias anteriores na sidebar
- Contadores: vagas vistas, feedbacks dados, avaliações manuais

#### 11.3 Visibilidade de custo de modelos (por dia)

- **Objetivo:** Ver quanto aquele dia está custando em uso de modelos, em **reais (BRL)**.
- **Escopo inicial:** Apenas **buscas manuais** (paste-and-score na UI — Claude Haiku, 2 chamadas por vaga). Monitoramento de custo do pipeline fica para depois.
- **Exibição:** Custo por dia na UI (sidebar do histórico ou seção dedicada), em reais.
- **Implementação:** Dicionário de custo por modelo (ex.: em `config/` ou módulo dedicado) com preço por token ou por 1k tokens, para calcular BRL a partir do usage retornado pelas APIs. Se necessário, taxa de câmbio configurável ou fixa.
- **Nota:** Hoje o código não persiste usage (tokens); será necessário registrar usage nas chamadas do paste-and-score e persistir (ex.: `data/usage/`) para agregar por dia.

---

### ÉPICO 12: Pipeline Automatizado Estável

**Objetivo:** Fetch + Score rodando de forma confiável via GitHub Actions.

**Dependência:** Épicos 5 e 6 concluídos.

**Critério de aceite:** 5 dias consecutivos sem intervenção. Cobertura ≥ 10 vagas novas/dia.

#### 12.1 Tratamento de falhas por coletor

- Se uma fonte falhar, pipeline continua com as demais
- Retry 1x por fonte se timeout
- Commit de log de erro se todas falharem

---

### ÉPICO 13: Geração de Materiais

**Objetivo:** Gerar currículo e cover letter personalizados por vaga, com botão na UI.

**Dependência:** Scoring estável por ≥ 2 semanas.

**Critério de aceite:** Materiais gerados para 5 vagas reais. ≥ 4 prontos para enviar com mínima edição.

#### 13.1 Currículo base modular (`config/resume_base.md`)
#### 13.2 Template de cover letter (`config/cover_letter_template.md`)
#### 13.3 Script generate.py (Claude Sonnet)
#### 13.4 Geração de PDF (weasyprint)
#### 13.5 Botão "Preparar aplicação" na UI

- Em cada card com score ≥ 70
- Loading → preview → download PDF

---

### ÉPICO 14: Feedback Loop

**Objetivo:** Feedback do usuário alimenta o scoring.

**Dependência:** Épicos 9 e 11 rodando com dados de ≥ 2 semanas.

**Critério de aceite:** Scoring melhora visivelmente após 2 semanas de feedback.

#### 14.1 Agregação de feedback (padrões de aceite/rejeição)
#### 14.2 Feedback no prompt de scoring (contexto extra)
#### 14.3 Persistência no repositório (Actions lê feedback)

---

---

Backlog, itens postergados e ideias futuras → [docs/governance/backlog.md](docs/governance/backlog.md)

---

**Última atualização:** Mar 2026  
**Revisão (estado do código):** Conferido em Mar 2026. Concluídos conforme seção ✅; Épicos 9 (UI polish), 10 (GitHub API), 11 (feedback/histórico), 12 (retry/tratamento de falhas), 13 (generate.py completo) e 14 ainda não implementados. `generate.py` segue stub; `github_api.py` não existe.
