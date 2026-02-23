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
  - Instruções de Agente -> `.agent/`

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

### Antigravity (Executor)
**Papel:** Implementar funcionalidades, manter a integridade técnica e garantir o fechamento correto de cada tarefa.
- ✅ Escreve código funcional e limpo.
- ✅ Atualiza `ARCHITECTURE.md` a cada mudança estrutural.
- ✅ Segue o `closure_protocol.md` ao finalizar cada funcionalidade.
- ✅ Mantém o `ROADMAP.md` sincronizado (limpando o passado e detalhando o próximo passo).

---

## 3. AMBIENTE TÉCNICO

- **OS**: Windows
- **Shell**: PowerShell (usar `;` para encadear comandos).
- **Python**: Obrigatório uso de `venv` ativo.
