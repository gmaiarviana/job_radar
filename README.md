# Job Radar

Sistema automatizado de busca e scoring para vagas remotas para Product Manager / Technical Program Manager.

## 🎯 Objetivo

Encontrar vagas altamente relevantes e automatizar o scoring, reduzindo o esforço manual para 5-10 minutos por dia.

## 🧭 Jornada do Usuário

```text
Automático (GitHub Actions, seg-sex 6h BRT):
  1. Busca vagas PM/TPM (fetch.py)
  2. Pontua cada vaga contra perfil (score.py)
  3. Salva resultados no repositório

Online (GitHub Pages, sempre disponível):
  4. Acessa https://gmaiarviana.github.io/job_radar/
  5. Vê as vagas dos últimos 14 dias com scores e vereditos
  6. Sem instalação necessária — basta um browser

Online (Streamlit Cloud, sempre disponível):
  4b. Acessa o app no Streamlit Cloud
  5b. Avalia vagas manualmente (paste-and-score) com scoring online
  6b. Vê vagas do pipeline com scores e vereditos

Manual (Streamlit local, quando quiser):
  7. Abre o app: streamlit run app.py
  8. Vê as vagas do dia com scores e justificativas
  9. Marca "👍 Bom match" ou "👎 Não relevante" para calibrar scoring
```

## 📂 Estrutura de Documentação

Para facilitar o trabalho de agentes de IA:

-   **`README.md`**: (Este arquivo) O que é o projeto e visão geral da jornada.
-   **[ARCHITECTURE.md](ARCHITECTURE.md)**: Detalhes técnicos, decisões e fluxos internos.
-   **[ROADMAP.md](ROADMAP.md)**: Planos futuros e próximos épicos técnicos.
-   **`docs/governance/`**: [CONSTITUTION.md](docs/governance/CONSTITUTION.md) (princípios, processo de refinamento) e [planning_guidelines.md](docs/governance/planning_guidelines.md) (templates, quando refinar).
-   **`.agent/`**: Protocolos de execução (closure, decision_map, workflows).

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
| Streamlit Cloud | $0 (tier gratuito) |
| **Total** | **~$2.50** |

---

## 🛠️ Setup Rápido

### Visualizar vagas (sem instalação)

- **GitHub Pages**: https://gmaiarviana.github.io/job_radar/
- **Streamlit Cloud**: https://jobradar-hvmzhnimrql79kndcbwz9t.streamlit.app/ — scoring online de vagas

### Deploy no Streamlit Cloud (scoring online)

**Pré-requisitos**: conta GitHub + conta Streamlit Cloud (gratuita).

1. Acesse `share.streamlit.io` e faça login com GitHub.
2. Clique em **"New app"**.
3. Selecione o repositório `job_radar`, branch `main`, arquivo `app.py`.
4. Em **"Advanced settings" → "Secrets"**, adicione:

   ```text
   ANTHROPIC_API_KEY = "sk-ant-..."
   GITHUB_TOKEN = "ghp_..."
   GITHUB_REPO = "owner/repo"
   AUTHORIZED_EMAIL = "seu@gmail.com"
   ```

   - `GITHUB_TOKEN`: Personal Access Token com permissão `contents: write` no repositório. Crie em GitHub → Settings → Developer settings → Personal access tokens → Fine-grained tokens, selecionando o repositório e permissão "Contents: Read and write".
   - `GITHUB_REPO`: formato `"owner/repo"` (ex: `"gmaiarviana/job_radar"`).
   - `AUTHORIZED_EMAIL`: email Google autorizado a usar o app.

5. (Opcional) Habilite **"Viewer authentication"** no painel do Streamlit Cloud (Settings → Sharing → "Require viewers to log in with Google") para restringir acesso ao app.

6. Clique **"Deploy"**.

**Persistência**: com `GITHUB_TOKEN` configurado, scoring manual persiste diretamente no repositório via GitHub API. Sem token, fallback para filesystem local (efêmero no Cloud).

### Desenvolvimento local (scoring)

#### Pré-requisitos (desenvolvimento / scoring manual)

- Python 3.11+
- API Keys (OpenAI & Anthropic)
- Repositório Git configurado

#### Instalação (Windows/PowerShell)

```powershell
git clone <repo-url>
cd job-radar
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp .env.example .env
# Adicione suas API keys no .env
```

Para validar o pipeline de fetch: `python src/fetch.py --dry-run`

#### Uso Diário

```powershell
git pull                    # Sincroniza vagas do Actions
streamlit run app.py        # Revisa e avalia vagas
```

#### Variáveis de Ambiente

```text
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GITHUB_TOKEN=ghp_...              # Opcional: persistência via GitHub API (Streamlit Cloud)
GITHUB_REPO=owner/repo            # Opcional: formato "owner/repo"
AUTHORIZED_EMAIL=seu@gmail.com    # Opcional: restrição de acesso no Streamlit Cloud
```

---
*Para detalhes técnicos de infraestrutura e decisões de design, veja [ARCHITECTURE.md](ARCHITECTURE.md).*