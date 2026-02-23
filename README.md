# Job Radar

Sistema automatizado de busca, scoring e aplicação a vagas remotas para Product Manager / Technical Program Manager.

## 🎯 Objetivo

Encontrar vagas altamente relevantes e automatizar a preparação de materiais de aplicação de alta qualidade, reduzindo o esforço manual para 5-10 minutos por dia.

## 🧭 Jornada do Usuário

```text
Automático (GitHub Actions, seg-sex 6h BRT):
  1. Busca vagas PM/TPM (fetch.py)
  2. Pontua cada vaga contra perfil (score.py)
  3. Salva resultados no repositório

Manual (Streamlit local, quando quiser):
  4. Abre o app: streamlit run app.py
  5. Vê as vagas do dia com scores e justificativas
  6. Clica "Preparar aplicação" nas vagas que interessam
  7. Sistema gera currículo + cover letter personalizados (PDF)
  8. Faz download, revisa, submete na plataforma
  9. Marca "👍 Bom match" ou "👎 Não relevante" para calibrar scoring
```

## 📂 Estrutura de Documentação

Para facilitar o trabalho de agentes de IA:

-   **`README.md`**: (Este arquivo) O que é o projeto e visão geral da jornada.
-   **[ARCHITECTURE.md](file:///c:/Users/guilh/Desktop/projetos_epso/job_radar/ARCHITECTURE.md)**: Detalhes técnicos, decisões e fluxos internos.
-   **[ROADMAP.md](file:///c:/Users/guilh/Desktop/projetos_epso/job_radar/ROADMAP.md)**: Planos futuros e próximos épicos técnicos.
-   **`.agent/`**: Instruções de trabalho e workflows para agentes.

---

## 📝 Perfil e Materiais Base (Config)

-   **`config/profile.md`**: O cérebro do scoring. Perfil condensado (~800 tokens) extraído da narrativa de carreira.
-   **`config/resume_base.md`**: Currículo base modular. O sistema seleciona e enfatiza bullets sem inventar dados.
-   **`config/cover_letter_template.md`**: Template com a "voz" do usuário, preenchido pelo LLM com fit específico por vaga.

## 💰 Custo Estimado

| Componente | Estimativa/mês |
| :--- | :--- |
| OpenAI Search (~80 buscas) | ~$1.00 |
| Claude Haiku (Scoring) | ~$1.50 |
| Claude Sonnet (Escrita) | ~$1.50 |
| **Total** | **~$4.00** |

---

## 🛠️ Setup Rápido

### Pré-requisitos
- Python 3.11+
- API Keys (OpenAI & Anthropic)
- Repositório Git configurado

### Instalação (Windows/PowerShell)

```powershell
git clone <repo-url>
cd job-radar
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp .env.example .env
# Adicione suas API keys no .env
```

### Uso Diário

```powershell
git pull                    # Sincroniza vagas do Actions
streamlit run app.py        # Revisa e gera materiais
```

### Variáveis de Ambiente

```
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
SMTP_USER=seu@gmail.com        # Opcional: alertas por email
SMTP_PASS=xxxx-xxxx-xxxx-xxxx
NOTIFY_EMAIL=seu@gmail.com
```

---
*Para detalhes técnicos de infraestrutura e decisões de design, veja [ARCHITECTURE.md](file:///c:/Users/guilh/Desktop/projetos_epso/job_radar/ARCHITECTURE.md).*