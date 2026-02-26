# Protocolo de Fechamento (Closure) - Job Radar

Este protocolo deve ser executado obrigatoriamente ao finalizar qualquer funcionalidade ou conjunto de tarefas. 

Objetivo: Garantir que o projeto esteja sempre em estado de "pronto para entrega", com documentação sincronizada e sem lixo técnico.

---

## 1. VERIFICAÇÃO TÉCNICA
- [ ] O código está funcional e sem erros de sintaxe?
- [ ] Execute o workflow de verificação: `/verify`
- [ ] Verifique se há erros no console ou logs.

## 2. HIGIENE DO REPOSITÓRIO
- [ ] Removeu arquivos temporários?
- [ ] Garantiu que nenhum arquivo `.json` ou de dados foi criado na raiz? (Mover para `data/` se necessário).
- [ ] Verificou se o `.gitignore` está sendo respeitado?

## 3. SINCRONIZAÇÃO DE DOCUMENTAÇÃO
- [ ] **ROADMAP.md**: 
    - Converta o checklist detalhado da funcionalidade recém-concluída em um resumo de 1 ou 2 linhas.
    - Marque como `✅ CONCLUÍDO`.
    - Certifique-se de que o próximo passo imediato no roadmap está detalhado o suficiente para a próxima sessão.
- [ ] **ARCHITECTURE.md**: 
    - Atualizou o mapa do sistema (mermaid) se houve mudança no fluxo?
    - Atualizou a tabela de componentes se criou um novo script?
- [ ] **README.md**: 
    - Atualizou o setup ou jornada do usuário se algo mudou?

## 4. ENTREGA (GIT)
- [ ] Stage APENAS arquivos relevantes (ex: `git add src/meu_script.py ARCHITECTURE.md`).
- [ ] Evite `git add .` para não subir lixo ou alterações paralelas indesejadas.
- [ ] Commit com mensagem descritiva (ex: `feat: implementa protocolo de fechamento e limpeza`).
- [ ] **Push**: fica a cargo do usuário (não incluir no fluxo automatizado).

## 5. RETROSPECTIVA (processo, não código)
- [ ] Houve algo de **processo ou implementação** que causou ineficiência? (ex: falta de contexto, decisão de fluxo equivocada, ferramenta inadequada).
- [ ] **Onde documentar**: aprendizado de processo → `.agent/`, `.cursor/` ou `docs/governance/` (ex.: CONSTITUTION.md). Detalhes técnicos ou de código → resolver com fix e documentar no ROADMAP/ARCHITECTURE (fluxo normal de fechamento).
- [ ] Registre em 1–2 linhas no lugar adequado (ex.: nota em `.agent/` ou doc de governança).

---

> [!IMPORTANT]
> **Cursor**: Você pode automatizar este processo chamando o comando `/finish`.
