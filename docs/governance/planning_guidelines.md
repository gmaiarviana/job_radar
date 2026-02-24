# Planning Guidelines - Job Radar

> Complemento à [CONSTITUTION.md](CONSTITUTION.md). O **processo de refinamento** (input, o que Claude Web faz, output), papéis e documentos essenciais estão na CONSTITUTION. Aqui: filosofia, quando refinar, templates e critérios de qualidade.

---

## Filosofia

**POC → Protótipo → MVP.** Validar cada etapa antes de avançar. Entregar valor incremental; expandir só quando o mínimo está sólido.

---

## Quando Refinar um Épico

Refine quando **todos** estes critérios forem atendidos:

- Épico é prioritário (próximo na fila)
- Dependências técnicas implementadas e validadas
- Estado atual do sistema compreendido
- Clareza sobre valor de negócio e viabilidade técnica

**Não refine:** épicos distantes, dependências não validadas, incerteza técnica. Detalhes do *como* refinar: [CONSTITUTION §3](CONSTITUTION.md#3-processo-de-refinamento).

---

## Estados do Épico (ROADMAP)

- **Não refinado:** Só objetivo definido. Aguarda sessão de refinamento.
- **Refinado:** Objetivo + sub-itens com critérios de aceite. Pronto para implementação.

**Fluxo:** Ideia → Épico (não refinado) → Refinamento → Épico (refinado) → Implementação.

Estado atual (ver ROADMAP.md): Épico 2 refinado; Épicos 3–8 com sub-itens definidos, podem ser refinados quando prioritários.

---

## Template: Épico

**Não refinado:** Objetivo apenas.

**Refinado:** Objetivo + sub-itens numerados (X.1, X.2, …) com critérios de aceite por sub-item. Exemplos em [ROADMAP.md](../../ROADMAP.md).

---

## Template: Funcionalidade (sub-item)

- **Descrição:** 1–2 frases.
- **Critérios de aceite:** Comportamentos esperados testáveis; "Não deve" só se relevante.

Exemplos no ROADMAP (ex.: 2.1, 2.2).

---

## Critérios de Qualidade

**Épico:** Objetivo claro (valor de negócio); coeso; 2–5 funcionalidades; entrega valor mesmo se parar no meio.

**Funcionalidade:** Testável; incremental; escopo claro; não se sobrepõe a outras.

---

## Manutenção do ROADMAP

Quando épico for concluído: marque ✅ no título, resuma em 1–2 linhas, remova detalhes, mova para "✅ Concluído".

---

## Documentos para Refinamento

Lista completa e links: [CONSTITUTION §7](CONSTITUTION.md#7-documentos-essenciais).
