import streamlit as st

st.set_page_config(page_title="Construcción de Lote", page_icon="📦", layout="wide")

st.markdown("""
<style>
.stApp { background: linear-gradient(160deg, #0f3d4a 0%, #123d4a 40%, #0d3240 100%) !important; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<meta http-equiv="refresh" content="0; url=https://construccion-lote.streamlit.app">
<script>window.location.href = "https://construccion-lote.streamlit.app";</script>
""", unsafe_allow_html=True)

st.markdown("🔄 Redirigiendo a **Construcción de Lote**...")
st.link_button("Abrir Construcción de Lote →", "https://construccion-lote.streamlit.app", use_container_width=True)
