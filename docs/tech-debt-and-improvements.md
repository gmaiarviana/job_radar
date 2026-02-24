# Débitos técnicos e melhorias (checkpoint Fev 2026)

Itens de **preparação / qualidade** (score excluir seed_*, extrair companies, centralizar paths) estão no [ROADMAP](../ROADMAP.md) como **Épico 4**. Tratamento de falhas por coletor está no **Épico 8.2**.

Este doc guarda apenas o que **não** virou épico — referência para mais tarde.

---

## Não priorizado (quando for mexer)

- **Testes:** Nenhuma suíte (pytest). ARCHITECTURE cita smoke test + unitários para `job_schema` e pipeline. Fase de experimento; priorizar quando estabilizar.
- **Type hints em score.py**, **pyproject.toml / ruff / mypy:** melhorias contínuas.

---

## Estrutura e organização

- **Estrutura atual:** Boa — `src/`, config, data separados. Manter.
- **README:** Índice curto (ARCHITECTURE, ROADMAP, como rodar fetch/score/seed) ajuda onboarding e IA.

---

**Referências:** [ROADMAP](../ROADMAP.md) · [ARCHITECTURE](../ARCHITECTURE.md)
