# ROADMAP - Job Radar

📡 **Status:** Pipeline completo (fetch → filter → score → dashboard). Épicos 7 e 8 concluídos. Próximo foco: Épicos 9 (Polimento de UI) e 10 (Persistência Online).

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

**Infra — Streamlit Cloud:** Compatibilidade do app.py com deploy em Streamlit Cloud (bridge st.secrets → os.environ, persistência graceful em filesystem efêmero, `.streamlit/config.toml`).

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

#### ✅ 7.3 Expandir companies.yaml

**Concluído:** 6 empresas adicionadas ao `config/companies.yaml` — Zapier (Greenhouse), Doist (Greenhouse), dLocal (Lever), Stripe (Greenhouse), Loadsmart (Greenhouse), Deel (Ashby, slug confirmado via jobs.ashbyhq.com/deel). Todas ativas (0 comentadas por 404).

#### ✅ 7.4 Revisar buscas manuais e renomear LinkedIn → Busca Manual

**Concluído:** Revisão de botões (8 entries). `config/linkedin_searches.yaml` renomeado para `config/manual_searches.yaml`. Aba "LinkedIn" → "Busca Manual"; subtítulo "Links de busca"; caption e docs atualizados.

#### ✅ 7.5 Remover penalty `outsourcing_context` do scoring
Concluído: penalty removida de CEILING_BY_PENALTY e do prompt de analyze_job; penalties apenas `seniority_gap` e `domain_gap_core`. Testes atualizados (4 cenários + 2 auto-eliminate); todos passam.

#### ✅ 7.6 Seed das novas fontes

- Remote OK e Get on Board populam `seen_jobs` via runs normais de `fetch.py` (sem necessidade de seed dedicado).
- Após expandir `companies.yaml` (7.3), as novas empresas ATS serão naturalmente “seedadas” nos primeiros runs de `fetch.py`.
- Critério de aceite: `seen_jobs` traz entradas de `remoteok` e (quando houver vagas) `getonboard`; novas empresas de 7.3 passam a aparecer sem gargalo após alguns runs do `fetch.py`.

#### ✅ 7.7 Novos coletores (Himalayas, Working Nomads, JobsCollider)

**Concluído:** 3 coletores adicionados (`himalayas.py`, `workingnomads.py`, `jobscollider.py`), registrados em `__init__.py` e `fetch.py`. Throttle corrigido de 20 → 50 em `apply_seen_jobs_filter`.

**Ordem de execução sugerida (para implementação futura):** 7.5 → 7.3 + 7.4 (paralelo) → 7.2 → 7.6 → 7.7

---

### ✅ ÉPICO 8: Deploy Online (GitHub Pages)

**Concluído:** Dashboard read-only via GitHub Pages. `src/build_frontend_data.py` consolida `data/scored/` em `data/jobs.json` (últimos 14 dias); o workflow copia para `docs/data/jobs.json` para o Pages. `docs/index.html` renderiza cards com score, veredito, filtro por data e detalhes expandíveis. Pipeline diário (Actions) gera o JSON automaticamente e commita.

---

### ÉPICO 9: Polimento de UI — Cards, Detalhes e Cópia

**Objetivo:** Melhorar a experiência visual dos cards de vagas e facilitar extração de conteúdo para uso externo (Claude, docs).

**Dependência:** Épico 6 concluído.

**Critério de aceite:** Cards com hierarquia visual limpa; ceiling removido da UI; botões de cópia funcionais (JD + relatório); botão "Avaliar outra" funcional na aba Busca Manual; formulário da Busca Manual com campos na ordem empresa → título → JD; badge de fonte exibindo o coletor de origem (mantendo "manual" para vagas manuais); nova aba "Resumo" no Streamlit e filtro/seção equivalente no GitHub Pages mostrando apenas vagas APLICAR (score ≥ 85).

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

#### 9.4 Reordenar formulário da Busca Manual

- Trocar a ordem dos campos para: empresa → título → JD (hoje está título → empresa → JD)
- Critério de aceite: ordem dos campos igual à sequência natural do LinkedIn

#### 9.5 Exibir coletor no badge de fonte

- Na aba Vagas, substituir o label "pipeline" pelo nome real do coletor (ex.: "remotive", "greenhouse", "openai_web_search")
- O campo `source` já existe no JSON com o nome correto; é só mudar a exibição no `app.py`
- Manter "manual" para vagas da busca manual (sem alteração)
- Critério de aceite: badge exibe o coletor de origem; vagas manuais continuam com badge "manual"

#### 9.6 Aba "Resumo"

- Nova aba no Streamlit com foco nas vagas que merecem ação: lista filtrada por veredito APLICAR (score ≥ 85), ordenada por score desc, com filtro de data
- Versão equivalente no GitHub Pages: seção ou filtro dedicado mostrando apenas APLICAR
- Read-only neste épico; status de aplicação vem depois do Épico 10
- Critério de aceite: aba funcional no Streamlit; GitHub Pages exibe filtro/seção equivalente

---

### ÉPICO 10: Persistência Online (GitHub API via Streamlit Cloud)

**Objetivo:** Habilitar escrita a partir do Streamlit Cloud — scoring manual e marcação de aplicações persistem no repo via GitHub Contents API, eliminando a necessidade de acesso local.

**Dependência:** Streamlit Cloud funcional (infra concluída). Épico 10.0 (auth) é pré-requisito para 10.1–10.4. Épico 9 recomendado mas não bloqueante.

**Critério de aceite global:** Paste-and-score no Streamlit Cloud grava `manual_*.json` no repo. Marcação "já apliquei" persiste entre sessões. Vagas manuais aparecem na aba Vagas e no GitHub Pages após o próximo build do Actions.

#### 10.0 Autenticação Google OAuth

- Habilitar "Viewer authentication" no painel do Streamlit Community Cloud (configuração sem código no painel)
- Usar `st.experimental_user` no `app.py` para ler o email do usuário logado
- Proteger todas as ações de escrita com verificação de email autorizado via `st.secrets` (ex: `AUTHORIZED_EMAIL`)
- Funcionalidade local (sem auth) continua funcionando normalmente — sem quebra de fluxo de desenvolvimento
- Critério de aceite: app no Streamlit Cloud exige login Google; email não autorizado vê mensagem de erro; ações de leitura permanecem acessíveis

#### 10.1 Camada de escrita GitHub API (`src/github_api.py`)

- Módulo com duas operações: `get_file(path)` → retorna conteúdo + SHA atual; `put_file(path, content, sha=None)` → cria (`sha=None`) ou atualiza (sha obrigatório)
- Detalhe obrigatório: update de arquivo existente exige o SHA retornado pelo GET anterior; sem o SHA correto a API retorna 409 Conflict. O módulo deve encapsular esse fluxo: GET para obter SHA → PUT com SHA
- Conteúdo trafegado em base64 (requisito da API) — encodar antes do PUT, decodificar no GET
- Token via `st.secrets` / `os.environ` (`GITHUB_TOKEN`) com escopo `contents: write` no repo
- Rate limit da API: 5.000 requests/hora autenticado — suficiente para uso pessoal
- Em caso de falha no PUT (ex: conflito, rede): lançar exceção com mensagem clara para o chamador tratar como fallback

#### 10.2 Integrar persistência no Streamlit Cloud (`app.py`)

- Após scoring manual: commitar `manual_*.json` e atualizar `seen_jobs.json` via `github_api.py`
- Após marcação "já apliquei": commitar `data/applications.json` via `github_api.py`
- Fallback gracioso se token ausente ou escrita falhar: exibir resultado normalmente + aviso de que a persistência falhou (não quebrar o fluxo do usuário)

#### 10.3 Validar `build_frontend_data.py`

- Confirmar que `manual_*.json` commitados via API aparecem no consolidado `data/jobs.json`
- Confirmar que `data/applications.json` é lido corretamente pela aba Resumo
- Sem alteração de código esperada — apenas validação

#### 10.4 Documentação

- `ARCHITECTURE.md`: adicionar `github_api.py` na tabela de componentes e descrever o fluxo GET→PUT
- `README.md`: adicionar `GITHUB_TOKEN` e `AUTHORIZED_EMAIL` nas variáveis de ambiente

---

### ÉPICO 11: UX Completa

**Objetivo:** Polimento da UI — feedback e histórico consolidado.

**Dependência:** Épico 6 rodando + Épico 10 concluído.

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

#### 11.4 Marcação "Já apliquei"

- Botão por vaga nas abas Vagas e Resumo: marca a vaga como aplicada (boolean) e registra a data automaticamente
- Persiste via GitHub API (depende do Épico 10)
- Aba Resumo exibe filtro adicional: "todas APLICAR" vs "ainda não apliquei"
- Dados em `data/applications.json` no repo (mesmo padrão de `seen_jobs.json`)
- Critério de aceite: marcação persiste entre sessões no Streamlit Cloud; aparece como filtro na aba Resumo

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
**Revisão (estado do código):** Conferido em Mar 2026. Concluídos conforme seção ✅; Épicos 9 (UI polish, incluindo formulário da Busca Manual, badge de coletor e aba Resumo), 10 (auth Google + GitHub API), 11 (feedback/histórico + marcação "Já apliquei"), 12 (retry/tratamento de falhas), 13 (generate.py completo) e 14 ainda não implementados. `generate.py` segue stub; `github_api.py` não existe.
