import streamlit as st

# Ocultar toolbar de GitHub
st.markdown("""
    <style>
        .stAppToolbar { display: none; }
    </style>
""", unsafe_allow_html=True)

NOTEBOOKLM_URL = "https://notebooklm.google.com/notebook/f410bdf4-992a-40e7-8f20-4ac2d7c8beec"

st.markdown("## 🧴 ANMAT — Cosméticos y Perfumes")
st.markdown("Consultá normativa y procedimientos de ANMAT para importación de cosméticos y perfumes. Fuentes oficiales verificadas.")

st.divider()

col1, col2 = st.columns(2)

with col1:
    st.markdown("##### 📋 ¿Qué podés consultar?")
    st.markdown("""
    - Habilitación de establecimientos importadores
    - Aviso de importación en TAD (Disp. 4033/2025)
    - Rotulado y nomenclatura INCI
    - Sustancias permitidas, restringidas y prohibidas
    - Diferencia cosmético vs. medicamento
    - Exportación y Certificado de Libre Venta
    - Marco normativo MERCOSUR
    """)

with col2:
    st.markdown("##### 📚 Fuentes cargadas")
    st.markdown("""
    - Resolución 155/98 (norma base)
    - Disp. 4033/2025 y 7939/2025
    - Instructivos ANMAT oficiales
    - Resoluciones GMC MERCOSUR
    - Normativa de sustancias e ingredientes
    - Documentación práctica de comercio exterior
    """)

st.divider()

st.info("💡 El asistente abre en una nueva pestaña. Podés hacer preguntas en lenguaje natural sobre normativa ANMAT para cosméticos y perfumes.", icon="ℹ️")

st.link_button(
    "🚀 ABRIR ASISTENTE ANMAT",
    NOTEBOOKLM_URL,
    use_container_width=True,
    type="primary"
)

st.divider()

st.caption("Herramienta desarrollada por Grupo 8 — Interlog Comercio Exterior · Fuentes: ANMAT, Boletín Oficial, MERCOSUR")
