import streamlit as st

NOTEBOOK_URL = "https://notebooklm.google.com/notebook/c43e859b-fc3f-47c1-bc2f-d1cfe6541fcd"

st.markdown("## ⛏️ Ley Minera — Normativa y Consultas")
st.markdown("---")

st.markdown(
    """
    Consultá normativa, decretos y análisis sobre el **Régimen de Inversiones Mineras (Ley 24.196)**,
    comercio exterior minero, prestadores de servicios y el **RIGI (Ley 27.742)** en base a fuentes
    oficiales verificadas.

    **Fuentes incluidas:**
    - Ley 24.196 — Régimen de Inversiones Mineras
    - Decretos 2686/93 y 1089/2003
    - Resolución 89/2019 y Res. 6/2024 (Secretaría de Minería)
    - Resolución 21/2023 (Registro prestadores)
    - Res. Gral. AFIP 5333/2023
    - Ley 27.742 (RIGI) y Decreto 749/2024
    - Análisis de estudios jurídicos especializados

    > Necesitás acceso a internet para abrir el asistente.
    """
)

st.link_button(
    label="⛏️ Abrir asistente Ley Minera",
    url=NOTEBOOK_URL,
    use_container_width=True,
    type="primary",
)

st.markdown("---")
st.caption("Fuentes: Ley 24.196 · Decretos 2686/93, 1089/2003 · Res. 89/2019, 6/2024, 21/2023 · Res. Gral. AFIP 5333/2023 · Ley 27.742 (RIGI) · Decreto 749/2024")
