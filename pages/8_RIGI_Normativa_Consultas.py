import streamlit as st

NOTEBOOK_URL = "https://notebooklm.google.com/notebook/39713be2-d428-4a3a-bb3c-744323fb690e"

st.title("🏛️ RIGI — Normativa y Consultas")
st.markdown("---")

st.markdown(
    """
    Consultá normativa, decretos y análisis sobre el **Régimen de Incentivo 
    para Grandes Inversiones (RIGI)** en base a fuentes oficiales verificadas.
    """
)

st.markdown("### ¿Qué podés consultar?")

col1, col2 = st.columns(2)

with col1:
    st.markdown(
        """
        - 📄 Ley 27.742 y sus alcances  
        - 📋 Decretos reglamentarios  
        - 🏗️ Requisitos para adherir al RIGI  
        - 💰 Beneficios impositivos y aduaneros  
        """
    )

with col2:
    st.markdown(
        """
        - 🌍 Sectores alcanzados  
        - ⚖️ Estabilidad jurídica y fiscal  
        - 📦 Importaciones en el marco del RIGI  
        - 🔍 Análisis y comparativas normativas  
        """
    )

st.markdown("---")

st.info(
    "💡 **Tip:** Podés hacer preguntas concretas como: "
    "*¿Qué sectores están incluidos en el RIGI?*, "
    "*¿Cuáles son los beneficios aduaneros?*, "
    "*¿Qué dice el Decreto 749/2024?*"
)

st.markdown("### Acceder al asistente")

st.markdown(
    """
    El asistente se abre en una nueva pestaña. 
    Necesitás una cuenta de **Google (Gmail)** para acceder.
    """
)

st.link_button(
    label="🚀 Abrir asistente RIGI",
    url=NOTEBOOK_URL,
    use_container_width=True,
    type="primary",
)

st.markdown("---")
st.caption("Fuentes: Ley 27.742 · Decretos 749/2024, 940/2024, 1028/2024, 105/2026 · Análisis Marval · Análisis Beccar Varela · Fuentes CDA")
