import streamlit as st

NOTEBOOK_URL = "https://notebooklm.google.com/notebook/8ded9948-1029-4468-a7b8-976e338ce13d"

st.title("🍽️ INAL — Normativa y Consultas")
st.markdown("---")
st.markdown(
    """
    Consultá normativa, procedimientos y requisitos del **Instituto Nacional de Alimentos (INAL)**
    para la importación de productos alimenticios, en base a fuentes oficiales verificadas.
    """
)

st.markdown("### ¿Qué podés consultar?")
col1, col2 = st.columns(2)
with col1:
    st.markdown(
        """
        - 📄 Disposición ANMAT 537/2025  
        - 📋 Autorización vs Aviso de Importación  
        - 🏗️ RNE y RNPA — cuándo se requieren  
        - 🌍 Productos de países con convenio  
        """
    )
with col2:
    st.markdown(
        """
        - ⚖️ Ley 18.284 y Código Alimentario  
        - 📦 Certificado de Libre Circulación  
        - 🏷️ Rotulado y etiquetado (CAA Cap. V)  
        - 🔍 Notas externas DGA sobre INAL  
        """
    )

st.markdown("---")
st.info(
    "💡 **Tip:** Podés hacer preguntas concretas como: "
    "*¿Cuándo se necesita autorización previa del INAL?*, "
    "*¿Qué productos no requieren intervención del INAL?*, "
    "*¿Cuáles son los plazos y aranceles del trámite?*"
)

st.markdown("### Acceder al asistente")
st.markdown(
    """
    El asistente se abre en una nueva pestaña. 
    Necesitás una cuenta de **Google (Gmail)** para acceder.
    """
)
st.link_button(
    label="🚀 Abrir asistente INAL",
    url=NOTEBOOK_URL,
    use_container_width=True,
    type="primary",
)

st.markdown("---")
st.caption("Fuentes: Disp. ANMAT 537/2025 · Disp. ANMAT 3280/2025 · Ley 18.284 · Ley 27.642 · CAA Cap. V · Notas Externas DGA · FAQ ANMAT/INAL")
