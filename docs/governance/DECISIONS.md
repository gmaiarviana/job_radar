# Decisões de produto e pipeline

Registro de decisões que afetam fontes, coletores ou comportamento do pipeline.

---

## 2026-03-14 — Remoção do coletor WeWorkRemotely

- **Decisão:** Coletor `weworkremotely` removido do pipeline.
- **Motivo:** WeWorkRemotely é um site pago para publicação de vagas; não faz sentido mantê-lo como fonte de coleta no Job Radar.
- **Ações:** Removidos `src/collectors/weworkremotely.py` e referências em `src/fetch.py`. Dados históricos em `data/` permanecem (não foram alterados).
