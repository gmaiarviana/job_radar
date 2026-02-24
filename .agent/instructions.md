# Project Instructions — Job Radar

Este é o ponto de entrada para agentes de IA que trabalham neste projeto. Siga rigorosamente a estrutura modular de protocolos.

## 1. PROTOCOLOS FUNDAMENTAIS
Consulte estes arquivos antes de iniciar qualquer trabalho:
- **[CONSTITUTION.md](file:///c:/Users/guilh/Desktop/projetos_epso/job_radar/.agent/CONSTITUTION.md)**: Papéis (Claude Web vs Antigravity), Princípio de Não-Duplicação e **Processo de Refinamento** (refinar épicos para trabalho em paralelo).
- **[decision_map.md](file:///c:/Users/guilh/Desktop/projetos_epso/job_radar/.agent/decision_map.md)**: Onde encontrar cada informação (Single Source of Truth).
- **[closure_protocol.md](file:///c:/Users/guilh/Desktop/projetos_epso/job_radar/.agent/closure_protocol.md)**: Checklist obrigatório para finalização de tarefas.

## 2. REGRAS GERAIS DE EXECUÇÃO
- **Ambiente**: Windows PowerShell. Use `;` para encadear comandos. **NUNCA use `&&`** — é inválido no PowerShell e causa falha.
- **Comandos git**: Antes de rodar `git add`/`commit`/`push`, consulte [.agent/workflows/commit.md](.agent/workflows/commit.md) e use a sintaxe correta.
- **Python**: Use sempre `python` com o ambiente virtual ativo (`.\venv\Scripts\Activate.ps1`).
- **Commits**: Sempre realize um commit ao finalizar uma funcionalidade, seguindo o protocolo de fechamento.

## 3. WORKFLOWS (Slash Commands)
- `/commit`: Atalho para adicionar, commitar e dar push.
- `/verify`: Verifica integridade dos stubs e diretórios.
- `/finish`: Executa o protocolo de fechamento completo (Limpeza + Docs + Sync).

---
*Para uma visão geral do projeto, veja o [README.md](file:///c:/Users/guilh/Desktop/projetos_epso/job_radar/README.md). Para detalhes técnicos, veja o [ARCHITECTURE.md](file:///c:/Users/guilh/Desktop/projetos_epso/job_radar/ARCHITECTURE.md).*
