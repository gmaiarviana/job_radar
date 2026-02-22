"""
app.py — Interface Streamlit do Job Radar.

Épico 2 | Interface local para visualizar vagas, gerar materiais e dar feedback.

Uso:
    streamlit run app.py
"""

import streamlit as st

# TODO: Épico 2.1 — tela principal com vagas do dia
# TODO: Épico 2.2 — botão "Preparar aplicação" → generate.py
# TODO: Épico 2.3 — feedback por vaga (👍/👎)
# TODO: Épico 2.4 — histórico de dias anteriores

st.set_page_config(
    page_title="Job Radar",
    page_icon="📡",
    layout="wide",
)

st.title("📡 Job Radar")
st.caption("Sistema automatizado de busca e scoring de vagas remotas")

st.info(
    "🚧 Interface em construção — Épico 2. "
    "Execute `python src/fetch.py` e `python src/score.py` para gerar vagas primeiro.",
    icon="🚧",
)

st.markdown("---")
st.markdown("**Próximas etapas:** Épico 1 (fetch + score) → Épico 2 (Streamlit) → Épico 3 (geração de materiais)")
