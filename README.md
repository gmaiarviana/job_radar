# Job Radar

Sistema automatizado de busca, scoring e aplicação a vagas remotas para Product Manager / Technical Program Manager.

## Objetivo

Encontrar vagas relevantes e aplicar com material personalizado, investindo 5-10 minutos por dia.

## Jornada do Usuário

```
Automático (GitHub Actions, seg-sex 6h BRT):
  1. Busca vagas PM/TPM remote LATAM/Worldwide (últimas 24h)
  2. Pontua cada vaga contra perfil do candidato (0-100)
  3. Salva resultados no repositório

Manual (Streamlit local, quando quiser):
  4. Abre o app: streamlit run app.py
  5. Vê as vagas do dia com scores e justificativas
  6. Clica "Preparar aplicação" nas vagas que interessam
  7. Sistema gera currículo + cover letter personalizados (PDF)
  8. Faz download, revisa, submete na plataforma
  9. Marca "👍 Bom match" ou "👎 Não relevante" para calibrar scoring
```

## Arquitetura

```
GitHub Actions (nuvem, automático)         Streamlit (local, sob demanda)
│                                          │
├─ fetch.py: OpenAI web_search             │
│  → busca vagas, salva JSON               │
├─ score.py: Claude Haiku                  │
│  → pontua contra perfil, salva JSON      │
├─ commit no repo ──────── git pull ───────┤
│                                          ├─ app.py: interface Streamlit
│                                          ├─ vê vagas pontuadas
│                                          ├─ clica "Preparar aplicação"
│                                          ├─ generate.py: Claude Sonnet
│                                          │  → currículo + cover letter (PDF)
│                                          ├─ download PDF
│                                          └─ feedback (salva local)
```

## Decisões Técnicas

| Decisão | Escolha | Motivo |
|---------|---------|--------|
| Busca de vagas | OpenAI gpt-4o-mini + web_search | Melhor cobertura que APIs gratuitas. Navega LinkedIn, Indeed, remote.com, Wellfound |
| Scoring | Claude Haiku | Barato para análise de texto longo. Consistente no scoring |
| Geração de materiais | Claude Sonnet | Qualidade de escrita superior para currículo e cover letter |
| Interface | Streamlit local | Botões funcionais, download integrado, feedback loop. Sem custo de hospedagem |
| Pipeline | GitHub Actions | Gratuito, roda na nuvem, máquina pode estar desligada |
| Output | PDF | Aceito pela maioria das plataformas. DOCX e texto puro como melhorias futuras |
| Feedback | JSON local | Simples. Insumo para recalibrar scoring. Migração para repo planejada |

## Custo Estimado

| Componente | Estimativa/mês |
|------------|---------------|
| OpenAI web_search (~80 buscas) | ~$1.00 |
| Claude Haiku scoring (~1k vagas) | ~$1.50 |
| Claude Sonnet geração (~30 aplicações) | ~$1.50 |
| GitHub Actions + infra | Gratuito |
| **Total** | **~$4/mês** |

## Estrutura do Projeto

```
job-radar/
├── README.md                    # Este arquivo
├── ROADMAP.md                   # Épicos e progresso
├── .env.example                 # Template de API keys
├── requirements.txt             # Dependências Python
│
├── app.py                       # Streamlit — interface principal (Épico 2)
│
├── src/
│   ├── fetch.py                 # Busca vagas (OpenAI web search) — Épico 1.3
│   ├── score.py                 # Scoring contra perfil (Claude Haiku) — Épico 1.5
│   ├── generate.py              # Gera currículo + cover letter (Claude Sonnet) — Épico 3.3
│   └── notify.py                # Email para PERFECT_MATCH — Épico 4.3
│
├── config/
│   ├── career_narrative.md      # Narrativa completa — fonte da verdade (não vai pro LLM)
│   ├── profile.md               # Perfil condensado (~800 tokens) — usado no scoring
│   ├── resume_base.md           # Currículo base modular (seções reorganizáveis)
│   ├── cover_letter_template.md # Template com voz do candidato
│   └── search.yaml              # Parâmetros de busca (queries, thresholds, pesos)
│
├── data/
│   ├── raw/                     # Vagas brutas (JSON por dia)
│   │   └── YYYY-MM-DD.json
│   ├── scored/                  # Vagas pontuadas — score ≥ 80 (JSON por dia)
│   │   └── YYYY-MM-DD.json
│   ├── feedback/                # Feedback do usuário — 👍/👎 (JSON, local)
│   │   └── YYYY-MM-DD.json
│   └── output/                  # PDFs gerados por vaga
│       └── YYYY-MM-DD_empresa_titulo/
│           ├── resume.pdf
│           └── cover_letter.pdf
│
└── .github/
    └── workflows/
        └── daily.yml            # GitHub Actions: fetch → score → notify → commit (seg-sex 9h UTC)
```

## Setup

### Pré-requisitos
- Python 3.11+
- Conta OpenAI com créditos API
- Conta Anthropic com créditos API
- Repositório GitHub (para Actions)

### Instalação

```bash
git clone <repo-url>
cd job-radar
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Editar .env com API keys
```

### Uso Diário

```bash
cd job-radar
source venv/bin/activate
git pull                    # Baixa vagas do dia (geradas pelo Actions)
streamlit run app.py        # Abre interface no navegador
```

### Variáveis de Ambiente

```
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
SMTP_USER=seu@gmail.com        # Opcional: alertas por email
SMTP_PASS=xxxx-xxxx-xxxx-xxxx
NOTIFY_EMAIL=seu@gmail.com
```

## Perfil e Materiais Base

### config/profile.md
Perfil condensado usado pelo LLM para scoring. Derivado do Career Narrative. ~800 tokens com critérios eliminatórios (localização, salário, idioma) e preferências (skills, indústria, cultura).

### config/resume_base.md
Currículo base em Markdown com seções modulares. O LLM reorganiza ênfases e bullets por vaga, sem inventar experiência. Seções: Summary (adaptável), Experience (bullets selecionáveis), Skills (modulares por tipo de vaga), Education & Certifications.

### config/cover_letter_template.md
Template com a voz do candidato. Estrutura fixa, conteúdo adaptado por vaga. Tom direto, sem clichês. O LLM preenche conexão com a empresa, fit específico, e motivação genuína baseada no Career Narrative.