---
description: Executa o protocolo de fechamento completo (Limpeza + Docs + Sync + Commit)
---

// turbo-all

> ⚠️ Este workflow executa o `closure_protocol.md`. Certifique-se de que a funcionalidade está pronta para entrega.

1. **Leitura do Protocolo**:
Leia o arquivo `.agent/closure_protocol.md` para garantir que todos os passos mentais foram seguidos.

2. **Verificação Técnica**:
Execute o workflow de verificação:
```powershell
python src/fetch.py; python src/score.py; python src/generate.py --job-id 123; python src/notify.py
```

3. **Arquivamento do Roadmap**:
Atualize o `ROADMAP.md`:
- Converta o checklist detalhado da tarefa concluída em um resumo de 1 linha.
- Mova para a seção `✅ CONCLUÍDO RECENTEMENTE`.

4. **Atualização da Arquitetura**:
Revise o `ARCHITECTURE.md` para garantir que novas dependências ou fluxos estão documentados.

5. **Commit e Push Final**:
```powershell
git add <arquivos_relevantes>; git commit -m "chore: functional closure - documentation and sync updated"; git push
```
