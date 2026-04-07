import streamlit as st

st.set_page_config(page_title="Construcción de Lote", page_icon="📦", layout="wide")

st.markdown("""
<style>
.stApp { background-color: #0f1117; }
</style>
""", unsafe_allow_html=True)

st.switch_page("https://construccion-lote.streamlit.app")
