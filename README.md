# Job Radar

Sistema automatizado de busca e scoring de vagas remotas para Product Manager / Technical Program Manager.

## Objetivo

Encontrar vagas relevantes com mínimo esforço diário (5-10 min). O sistema busca vagas via web search, pontua contra o perfil do candidato, e publica um portal HTML com as melhores oportunidades do dia.

## Como Funciona

```
GitHub Actions (seg-sex, 6h BRT)
│
├─ FETCH: OpenAI API (gpt-4o-mini + web_search)
│  Busca vagas PM/TPM remote LATAM/Worldwide nas últimas 24h
│  Output: lista estruturada de vagas (JSON)
│
├─ SCORE: Anthropic API (Claude Haiku)
│  Pontua cada vaga contra perfil do candidato (0-100)
│  Filtra top 5 (score ≥ 80)
│  Marca PERFECT_MATCH (score ≥ 95)
│
├─ RENDER: Gera HTML estático
│  Página do dia + índice com histórico
│  Push para branch gh-pages
│
└─ NOTIFY: Email (apenas PERFECT_MATCH)
   Envia alerta quando score ≥ 95
```

## Decisões Técnicas

| Decisão | Escolha | Motivo |
|---------|---------|--------|
| Busca de vagas | OpenAI web_search | Melhor cobertura que APIs gratuitas (Remotive, Arbeitnow). Navega LinkedIn, Indeed, remote.com, Wellfound |
| Scoring | Claude Haiku | Barato para análise de texto longo (perfil ~800 tokens + vagas). Consistente no scoring |
| Infra | GitHub Actions + Pages | Gratuito. Sem servidor. Histórico versionado |
| Entrega | HTML portal + email alertas | Portal para consulta ativa. Email só para urgências (PERFECT_MATCH) |
| Frequência | Seg-sex, 6h BRT | Vagas postadas no dia anterior. Sem fins de semana |

**Por que dois modelos?**
- OpenAI com web_search é superior para *buscar* — navega sites, extrai dados estruturados
- Claude Haiku é mais barato e consistente para *analisar* — scoring contra perfil longo
- Separar busca de scoring dá flexibilidade para trocar qualquer um independentemente

## Custo Estimado

| Componente | Estimativa |
|------------|-----------|
| OpenAI web_search (~80 buscas/mês) | ~$1.00 |
| OpenAI tokens (gpt-4o-mini) | ~$0.10 |
| Claude Haiku scoring (~1k vagas/mês) | ~$1.50 |
| GitHub Actions + Pages | Gratuito |
| **Total** | **~$2-3/mês** |

## Estrutura do Projeto

```
job-radar/
├── README.md                # Este arquivo
├── ROADMAP.md               # Épicos e progresso
├── .env.example             # Template de API keys
│
├── src/
│   ├── fetch.py             # Busca vagas (OpenAI web search)
│   ├── score.py             # Scoring contra perfil (Claude Haiku)
│   ├── render.py            # Gera HTML estático
│   └── notify.py            # Email para PERFECT_MATCH
│
├── config/
│   ├── profile.md           # Perfil condensado do candidato
│   └── search.yaml          # Parâmetros de busca (queries, thresholds, fontes)
│
├── templates/
│   └── index.html           # Template do portal
│
├── .github/
│   └── workflows/
│       └── daily.yml        # GitHub Actions (seg-sex 6h BRT)
│
└── docs/                    # HTML gerado (GitHub Pages serve daqui)
    ├── index.html           # Índice com histórico
    └── YYYY-MM-DD.html      # Página de cada dia
```

## Setup

### Pré-requisitos
- Python 3.11+
- Conta OpenAI com créditos API
- Conta Anthropic com créditos API
- Repositório GitHub (para Actions + Pages)

### Instalação Local

```bash
git clone <repo-url>
cd job-radar
python -m venv venv
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
cp .env.example .env
# Editar .env com API keys
```

### Variáveis de Ambiente

```bash
OPENAI_API_KEY=sk-...        # Para web search
ANTHROPIC_API_KEY=sk-ant-... # Para scoring
SMTP_USER=seu@gmail.com      # Para alertas por email
SMTP_PASS=app-password       # App password do Gmail
NOTIFY_EMAIL=seu@gmail.com   # Destinatário dos alertas
```

### Execução Manual

```bash
python src/fetch.py          # Busca vagas do dia
python src/score.py          # Pontua contra perfil
python src/render.py         # Gera HTML
python src/notify.py         # Envia alertas (se houver PERFECT_MATCH)
```

### Deploy (GitHub Actions)

1. Configurar secrets no repositório (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, etc.)
2. Ativar GitHub Pages (branch `gh-pages`, pasta `/docs`)
3. Workflow roda automaticamente seg-sex às 6h BRT

## Perfil do Candidato

O arquivo `config/profile.md` contém o perfil condensado usado pelo LLM para scoring. Derivado do Career Narrative completo, otimizado para contexto de LLM (~800 tokens).

**Critérios de scoring:**
- Localização: Brasil/LATAM/Worldwide (elimina US-only)
- Salário: ≥ $5,000 USD/mês
- Título: PM, TPM, PO, ou híbridos
- Experiência: 5+ anos tech, product/program management
- Skills: Agile, data analysis, AI/GenAI, stakeholder management
- Idioma: Inglês profissional obrigatório
- Red flags: Mandarin/outro idioma obrigatório, presencial, visa sponsorship required

## Referências

- [Career Narrative](link-to-gdocs) — Documento completo de posicionamento
- [Portal de Vagas](link-to-gh-pages) — HTML gerado diariamente