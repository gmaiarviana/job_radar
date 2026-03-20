# Backlog — Job Radar

Decisões fora de escopo e ideias/features futuras. O plano ativo (épicos em andamento) está em [ROADMAP.md](../../ROADMAP.md).

---

## Backlog

- **Validação manual e enriquecimento do profile:** Fazer com dados reais do pipeline rodando. Reintroduzir como épico no ROADMAP se padrões de erro surgirem.

### Decisões documentadas (fora de escopo)

- Flexibility signals ("do apply even if...") — boilerplate; risco de inflar scores
- Pesos altos em mission alignment — decisão manual na UI
- Decomposição granular de skills — evidence mapping por requirement já captura

---

## 💡 Ideias e features futuras

- **Tracking de aplicações:** Status por vaga (aplicado → entrevista → oferta → rejeitado)
- **Analytics:** Vagas/dia, score médio, tendências, taxa de aplicação, fontes mais produtivas
- **Cover letter por plataforma:** Adaptar para formulários específicos ("Why this company?", "Why this role?")
- **Múltiplos perfis:** PM puro vs TPM vs hybrid — scoring e geração adaptados
- **DOCX e texto puro:** Formatos alternativos de saída
- **discover.py:** Prospectar novas empresas-alvo via queries em boards ATS
- **Notificação mobile:** Push via Telegram Bot para `PERFECT_MATCH` (ideia futura; notify.py removido do pipeline atual)
- **Alertas por email:** enviar email se score >= 95 (ideia futura; notify.py removido do pipeline atual)
- **Links de fontes manuais sem API:** Wellfound (AngelList), YC Work at a Startup, Product Jobs Anywhere, Remote Rocketship. Avaliar inclusão em config/manual_searches.yaml após 1 semana com os 8 botões LinkedIn revisados. Só adicionar se fonte gerar ≥ 2 vagas compatíveis por semana. Contexto: Épico 7.4.

---

**Última atualização:** Fev 2026
