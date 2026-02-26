# CONSTITUTION - Job Radar

Princípios fundamentais e responsabilidades para o desenvolvimento deste projeto.

---

## 1. PRINCÍPIOS DE TRABALHO

### Não-Duplicação (Single Source of Truth)
- **Regra de Ouro**: Cada informação vive em apenas um lugar.
- **Referências**: Se uma informação é necessária em múltiplos contextos, use links: `Ver [detalhes](caminho/para/arquivo.md)`.
- **Higiene**: Não duplique prompts em instruções. Instruções devem apontar para o cérebro (`src/`) ou configuração (`config/`).

### Organização e Limpeza
- **Raiz Limpa**: Arquivos na raiz devem ser apenas os essenciais de documentação e configuração global.
- **Destino Estruturado**: 
  - Lógica/Scripts -> `src/`
  - Dados (JSONs) -> `data/`
  - Configuração/Material Base -> `config/`
  - Governança e planejamento -> `docs/governance/`
  - Protocolos de execução (closure, workflows, decision_map) -> `.agent/`

### Documentação Viva
- **ARCHITECTURE.md**: Representa o **PRESENTE** (o que o sistema é hoje).
- **ROADMAP.md**: Representa o **FUTURO** (o que o sistema será).

---

## 2. RESPONSABILIDADES

### Claude Web (Estrategista)
**Papel:** Refinar o roadmap, discutir decisões arquiteturais e gerar caminhos de solução.
- ✅ Analisa o contexto completo.
- ✅ Define critérios de aceite para novos épicos.
- ✅ Gere "Prompts de Execução" claros para o Antigravity.
- ❌ Não implementa código diretamente.

**Formato padrão de Prompt de Execução:**
1. Contexto — estado atual e por que a mudança é necessária
2. Tarefas numeradas — cada uma com comportamento esperado e critério de aceite próprio
3. Critério de aceite global — como verificar que o épico está completo
4. Fechamento — lembrete do closure_protocol.md

### Antigravity (Executor)
**Papel:** Implementar funcionalidades, manter a integridade técnica e garantir o fechamento correto de cada tarefa.
- ✅ Escreve código funcional e limpo.
- ✅ Atualiza `ARCHITECTURE.md` a cada mudança estrutural.
- ✅ Segue o `closure_protocol.md` ao finalizar cada funcionalidade.
- ✅ Mantém o `ROADMAP.md` sincronizado (limpando o passado e detalhando o próximo passo).
- ✅ Pode trabalhar em paralelo com outros agentes quando o épico for refinado em tarefas independentes (sub-itens com critérios de aceite próprios).

**Não deve:**
- ❌ Refinar épicos (é papel do Claude Web).
- ❌ Tomar decisões arquiteturais sem base em ROADMAP/ARCHITECTURE.

---

## 3. PROCESSO DE REFINAMENTO

Objetivo: Detalhar épicos e funcionalidades para que múltiplos agentes possam trabalhar em paralelo com prompts claros e critérios de aceite explícitos.

### Input esperado (você fornece)
- Comportamento desejado OU problema existente.
- Contexto: épico novo, ajuste em épico atual, ou discussão de prioridade.

### Claude Web deve

**1. Análise contextual**
- Consultar `ROADMAP.md` (épicos anteriores, padrão de sub-itens, dependências).
- Consultar `ARCHITECTURE.md` (fluxo atual, componentes).
- Consultar `decision_map.md` (onde cada informação mora).
- Identificar onde o comportamento está documentado (ou pedir para ver).

**2. Clarificação**
- Fazer perguntas específicas (volume, fontes, critérios de sucesso).
- Validar entendimento.
- Apontar trade-offs técnicos (ex.: mais fontes vs tempo de pipeline).

**3. Recomendação**
- Oferecer opções (A, B, C) quando houver trade-off.
- Recomendar com base em ROADMAP e ARCHITECTURE.
- Justificar recomendação.

**4. Refino para trabalho paralelo**
- Quebrar épicos em sub-itens com critérios de aceite próprios (ex.: 2.1, 2.2, 2.3).
- Marcar dependências entre sub-itens (ex.: 2.5 depende de 2.1–2.4).
- Gerar **um Prompt de Execução por sub-item** (ou por grupo que possa rodar em paralelo), para que diferentes agentes possam pegar cada prompt sem conflito.

**5. Gerar prompts**
- Múltiplos prompts (1 por arquivo ou 1 por tarefa independente).
- Ordem de execução clara quando houver dependência.
- Instruções enxutas (o executor pensa também).
- Incluir lembrete do `closure_protocol.md` no fechamento.

**6. Validação**
- Confirmar que os prompts cobrem o épico sem lacunas.
- Verificar se nada foi esquecido (docs, config, testes).

### Output esperado (Claude Web gera)

```
PROMPT 1: [ROADMAP.md ou spec]
[instruções enxutas]
PROMPT 2: [ARCHITECTURE.md ou src/ X]
[instruções enxutas]
PROMPT 3: [outro arquivo]
[instruções enxutas]
---
Ordem: 1 → 2 e 3 em paralelo (quando aplicável).
Fechamento: seguir closure_protocol.md.
```

---

## 4. AVALIAÇÃO DE DADOS (NotebookLM)

Quando o corpus de dados (`data/raw/*.json` ou `data/scored/*.json`) for grande demais para o contexto do Claude:

- **Source of truth** permanece em `data/raw/` e `data/scored/` (JSON). Cópias em TXT para o NotebookLM: `data/raw/copy txt/` e `data/scored/copy txt/` (NotebookLM não consome JSON).
- **Fluxo**: (1) Você carrega os TXTs no NotebookLM; (2) Claude formula perguntas de refinamento/qualidade; (3) Você faz as perguntas no NotebookLM e traz as respostas; (4) Claude usa as respostas para iterar (scoring, critérios, etc.).
- **Papel do Claude**: formular perguntas e interpretar o que você trouxer; **não** tentar ingerir o dataset inteiro. Script único JSON→TXT (raw + scored): `src/convert_json_to_txt_for_notebooklm.py`.

---

## 5. O QUE PROPOR (Guidelines de refinamento)

### Ao refinar épico novo
- ✅ Consultar `ROADMAP.md` (padrão dos épicos anteriores: objetivo, dependência, critério de aceite global, sub-itens numerados).
- ✅ Propor sub-itens com critérios de aceite claros por sub-item (permite paralelização).
- ✅ Perguntar sobre trade-offs (ex.: cobertura vs latência, simplicidade vs flexibilidade).
- ✅ Sugerir divisão POC → Protótipo → MVP quando fizer sentido.
- ✅ Indicar quais sub-itens podem ser executados em paralelo e quais dependem de outros.

### Ao discutir comportamento existente
- ✅ Identificar onde está documentado (`decision_map.md`, ROADMAP, ARCHITECTURE, `src/`).
- ✅ Analisar impacto (quais arquivos precisam ser atualizados).
- ✅ Propor mudança de spec + prompts para todos os arquivos afetados.
- ✅ Gerar prompts que permitam execução paralela quando possível.

### Ao propor melhorias
- ✅ Ser proativo quando ROADMAP/ARCHITECTURE forem claros.
- ✅ Oferecer opções quando houver trade-offs.
- ✅ Justificar com base em ROADMAP ou ARCHITECTURE.

---

## 6. MAPA DE REFINAMENTO

| Se você quer... | Consultar... | Gerar prompts para... |
|----------------|--------------|------------------------|
| **Refinar épico novo** | ROADMAP.md (épicos anteriores) + ARCHITECTURE.md + decision_map.md | ROADMAP.md + [specs novas se necessário] + ARCHITECTURE.md se mudar fluxo |
| **Discutir fetch / fontes** | ROADMAP.md (Épicos 2–3) + ARCHITECTURE.md + `src/fetch.py` | ROADMAP.md + ARCHITECTURE.md + `src/` e/ou `config/` |
| **Discutir scoring** | ROADMAP.md (Épico 4) + `config/search.yaml` + `src/score.py` | ROADMAP.md + config/search.yaml + src/score.py |
| **Discutir pipeline / CI** | `.github/workflows/daily.yml` + ROADMAP.md (Épico 7) | daily.yml + ROADMAP.md + ARCHITECTURE.md |
| **Discutir interface (Streamlit)** | ROADMAP.md (Épico 5) + ARCHITECTURE.md | ROADMAP.md + ARCHITECTURE.md + código da UI |
| **Discutir geração (CV/CL)** | ROADMAP.md (Épico 6) + config (resume_base, cover_letter_template) | ROADMAP.md + config/ + src/generate.py |
| **Revisar processo de refinamento** | Este arquivo (CONSTITUTION.md) | docs/governance/CONSTITUTION.md |
| **Revisar fechamento de tarefas** | closure_protocol.md | .agent/closure_protocol.md |

---

## 7. ANTI-PADRÕES (O que não fazer)

### ❌ Duplicar informação
- Cada informação vive em um lugar só (ver `decision_map.md`).
- Outros documentos referenciam: "Ver detalhes em...".
- Não copiar specs entre ROADMAP e ARCHITECTURE; ROADMAP = futuro, ARCHITECTURE = presente.

### ❌ Atualizar documentação diretamente (Claude Web)
- Claude Web **não** atualiza docs nem código; gera prompts.
- Quem aplica nas docs/código: Cursor ou Antigravity (conforme o prompt).

### ❌ Assumir sem base
- Sempre consultar ROADMAP.md e ARCHITECTURE.md.
- Perguntar se incerto.
- Não inventar padrões.

### ❌ Prompts verbosos
- Enxuto > detalhado (o executor pensa também).
- Instruções claras e suficientes.
- Evitar microgerenciamento.

### ❌ Ignorar paralelização
- Ao refinar, indicar sub-itens independentes e gerar um prompt por sub-item quando possível, para permitir trabalho em paralelo.

---

## 8. DOCUMENTOS ESSENCIAIS

### Para refinamento (enviar / ter à mão)
1. **CONSTITUTION.md** (este arquivo) — Princípios, responsabilidades, processo de refinamento, mapa.
2. **ROADMAP.md** — Épicos, status, sub-itens e critérios de aceite.
3. **ARCHITECTURE.md** — Estado atual do sistema (fluxo, componentes).
4. **planning_guidelines.md** — Templates de épico/funcionalidade, quando refinar, critérios de qualidade. Ver [planning_guidelines.md](planning_guidelines.md).
5. **decision_map.md** — Onde cada informação mora (Single Source of Truth). Ver [.agent/decision_map.md](../../.agent/decision_map.md).
6. **closure_protocol.md** — Checklist de fechamento (lembrete nos prompts). Ver [.agent/closure_protocol.md](../../.agent/closure_protocol.md).

### Consultados sob demanda
- **Config:** `config/profile.md`, `config/search.yaml`, `config/companies.yaml` (quando existir), templates.
- **Código:** `src/fetch.py`, `src/score.py`, `src/generate.py`, pipeline em `.github/workflows/`.

---

## 9. LOCALIZAÇÃO DESTE DOCUMENTO

Este arquivo fica em **`docs/governance/`** junto com `planning_guidelines.md`, para que governança e planejamento sejam fáceis de encontrar. Os protocolos de execução (closure_protocol, decision_map, workflows) permanecem em `.agent/`.

---

## 10. AMBIENTE TÉCNICO

- **OS**: Windows
- **Shell**: PowerShell (usar `;` para encadear comandos).
- **Python**: Obrigatório uso de `venv` ativo.
