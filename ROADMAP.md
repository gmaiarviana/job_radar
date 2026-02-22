# ROADMAP - Job Radar

Épicos incrementais do sistema de busca automatizada de vagas.

> **Filosofia:** POC → Protótipo → MVP. Validar cada etapa antes de avançar.

---

## ✅ Concluído

### Validação de Fontes (Exploratório)
Testamos 3 categorias de fontes para busca de vagas:
- **APIs gratuitas (Remotive, Arbeitnow):** Volume baixo, pouca relevância para PM/TPM remote LATAM
- **ChatGPT/Grok com web search (manual):** Melhor cobertura e qualidade. ChatGPT retornou 3 vagas com score ≥ 82
- **Decisão:** OpenAI API com web_search como fonte principal. APIs gratuitas descartadas.

---

## 📍 Próximos Passos

### ÉPICO 1: Fetch — Busca de Vagas via OpenAI Web Search (POC)

**Objetivo:** Script que busca vagas usando OpenAI Responses API com web_search e retorna JSON estruturado.

**Critério de sucesso:** Rodar localmente uma vez e retornar ≥ 3 vagas relevantes (PM/TPM remote LATAM).

#### 1.1 Prompt de busca otimizado
- Prompt que instrui gpt-4o-mini a buscar vagas PM/TPM remote LATAM/Worldwide das últimas 24h
- Output estruturado: título, empresa, salário, localização, URL, requisitos-chave, data
- Prompt armazenado em `config/search.yaml` (editável sem mexer em código)

#### 1.2 Script fetch.py
- Chama OpenAI Responses API com tool `web_search_preview`
- Parseia resposta em lista de vagas (JSON)
- Salva em `data/raw/YYYY-MM-DD.json`
- Tratamento de erro: API indisponível, resposta malformada, zero resultados
- Log mínimo no stdout

#### 1.3 Validação manual
- Rodar script 3 dias consecutivos
- Comparar resultados com busca manual no LinkedIn/remote.com
- Avaliar: cobertura (encontrou as mesmas?), falsos positivos, vagas duplicadas entre dias
- Documentar aprendizados para calibrar prompt

---

### ÉPICO 2: Score — Scoring contra Perfil via Claude Haiku

**Objetivo:** Script que recebe vagas brutas e retorna vagas pontuadas contra o perfil do candidato.

**Dependência:** Épico 1 validado.

**Critério de sucesso:** Scoring de 10 vagas com concordância ≥ 80% vs avaliação manual do candidato.

#### 2.1 Perfil condensado
- Criar `config/profile.md` derivado do Career Narrative
- ~800 tokens: experiência, skills, critérios eliminatórios, preferências
- Testar: LLM consegue diferenciar vaga boa de vaga ruim com esse perfil?

#### 2.2 Prompt de scoring
- System prompt com perfil + instruções de scoring
- Input: lista de vagas (título + descrição)
- Output por vaga: score (0-100), justificativa (1 linha), flag PERFECT_MATCH (boolean)
- Critérios explícitos no prompt: localização (peso alto), salário, fit de responsabilidades, red flags

#### 2.3 Script score.py
- Lê `data/raw/YYYY-MM-DD.json`
- Chama Claude Haiku com batch de vagas
- Salva em `data/scored/YYYY-MM-DD.json`
- Filtra: top 5 com score ≥ 80

#### 2.4 Calibração
- Candidato avalia manualmente 20-30 vagas (sim/não/talvez)
- Comparar com scores do LLM
- Ajustar prompt até concordância ≥ 80%
- Documentar thresholds finais

---

### ÉPICO 3: Render — Portal HTML Estático

**Objetivo:** Gerar página HTML navegável com as vagas do dia e histórico.

**Dependência:** Épico 2 validado.

**Critério de sucesso:** Página acessível via GitHub Pages, mobile-friendly, com vagas pontuadas do dia.

#### 3.1 Template HTML
- Design simples, mobile-first
- Card por vaga: título, empresa, score (badge colorido), salário, link direto, justificativa
- Ordenado por score (maior primeiro)
- Cores: verde (≥ 90), amarelo (80-89), cinza (< 80)

#### 3.2 Script render.py
- Lê `data/scored/YYYY-MM-DD.json`
- Gera `docs/YYYY-MM-DD.html` (página do dia)
- Atualiza `docs/index.html` (índice com links para cada dia)
- Mantém últimos 30 dias no índice

#### 3.3 Deploy GitHub Pages
- Configurar branch `gh-pages` ou pasta `/docs` no main
- Validar que página é acessível publicamente (ou privado se preferir)

---

### ÉPICO 4: Notify — Alertas por Email

**Objetivo:** Enviar email quando houver vaga com score ≥ 95 (PERFECT_MATCH).

**Dependência:** Épico 2 validado. Pode rodar em paralelo com Épico 3.

**Critério de sucesso:** Receber email com link direto para a vaga quando PERFECT_MATCH aparecer.

#### 4.1 Script notify.py
- Lê `data/scored/YYYY-MM-DD.json`
- Se alguma vaga tem `perfect_match: true`: envia email
- Template do email: título da vaga, empresa, score, link, justificativa
- Via Gmail SMTP (App Password) ou SendGrid free tier

#### 4.2 Proteção contra spam
- Máximo 1 email por dia (agrupa todos os PERFECT_MATCH)
- Não envia se não houver PERFECT_MATCH (silêncio = sem urgência)

---

### ÉPICO 5: Pipeline — Automação via GitHub Actions

**Objetivo:** Rodar pipeline completo automaticamente seg-sex às 6h BRT.

**Dependência:** Épicos 1-4 validados localmente.

**Critério de sucesso:** 5 dias consecutivos rodando sem intervenção manual, portal atualizado, emails enviados quando aplicável.

#### 5.1 Workflow daily.yml
- Cron: `0 9 * * 1-5` (9h UTC = 6h BRT)
- Steps: fetch → score → render → notify → commit + push
- Secrets: `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `SMTP_USER`, `SMTP_PASS`, `NOTIFY_EMAIL`
- Timeout: 5 min (pipeline leve)

#### 5.2 Tratamento de falhas
- Retry 1x se API falhar
- Se falhar de novo: commit log de erro, não quebra pipeline
- Notificação de falha via email (GitHub Actions nativo)

#### 5.3 Monitoramento
- Badge no README (status do último run)
- Log de cada execução no stdout do Actions
- Histórico de vagas acumulado no `/docs`

---

## 💡 Ideias Futuras

Não são épicos. Aguardando validação do MVP (Épicos 1-5).

- **Deduplicação cross-dia:** Detectar mesma vaga aparecendo em dias diferentes
- **Fonte adicional (JSearch API):** Adicionar como fallback se OpenAI web search perder cobertura
- **Tracking de aplicações:** Marcar vagas como "aplicado", "entrevista", "rejeitado"
- **Analytics:** Dashboard com métricas (vagas/dia, score médio, tendências de mercado)
- **Múltiplos perfis:** Suportar busca para diferentes posicionamentos (PM vs TPM vs hybrid)
- **RSS feed:** Alternativa ao email para quem usa leitores RSS
- **Telegram bot:** Push notification mais leve que email

---

## 📝 Observações

- Cada épico entrega valor isoladamente (posso usar fetch+score manual mesmo sem portal)
- Épicos 1 e 2 são os mais críticos — validam se a abordagem funciona
- Épicos 3-5 são infraestrutura de entrega — só fazem sentido se 1+2 funcionarem
- Custo total estimado: ~$2-3/mês após MVP completo

**Última atualização:** Fev 2026