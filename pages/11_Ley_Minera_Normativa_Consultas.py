import streamlit as st

st.markdown("""
<style>
[data-testid="stToolbar"] { visibility: hidden !important; }
[data-testid="stDecoration"] { display: none !important; }
a[href*="github.com"] { display: none !important; }
</style>
""", unsafe_allow_html=True)

NOTEBOOK_URL = "https://notebooklm.google.com/notebook/c43e859b-fc3f-47c1-bc2f-d1cfe6541fcd/preview"

st.markdown("## ⛏️ Ley Minera — Normativa y Consultas")
st.markdown("---")
st.markdown(
    """
    Consultá normativa, decretos y análisis sobre el **Régimen de Inversiones Mineras (Ley 24.196)**,
    comercio exterior minero, prestadores de servicios y el **RIGI (Ley 27.742)** en base a fuentes
    oficiales verificadas.
    """
)

st.markdown("### ¿Qué podés consultar?")
col1, col2 = st.columns(2)
with col1:
    st.markdown(
        """
        - 📄 Ley 24.196 — Régimen de Inversiones Mineras  
        - 📋 Decretos 2686/93 y 1089/2003  
        - 🏗️ Resolución 89/2019 y Res. 6/2024  
        - 💰 Beneficios impositivos y aduaneros mineros  
        """
    )
with col2:
    st.markdown(
        """
        - 📋 Resolución 21/2023 (Registro prestadores)  
        - ⚖️ Res. Gral. AFIP 5333/2023  
        - 🏛️ Ley 27.742 (RIGI) y Decreto 749/2024  
        - 🔍 Análisis de estudios jurídicos especializados  
        """
    )

st.markdown("---")
st.info(
    "💡 **Tip:** Podés hacer preguntas concretas como: "
    "*¿Qué beneficios aduaneros tiene la actividad minera?*, "
    "*¿Cómo se registran los prestadores de servicios mineros?*, "
    "*¿Cómo se combina la Ley Minera con el RIGI?*"
)

st.markdown("### Acceder al asistente")
st.markdown(
    """
    El asistente se abre en una nueva pestaña. 
    Necesitás una cuenta de **Google (Gmail)** para acceder.
    Solo podés hacer consultas — las fuentes no se pueden modificar.
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
