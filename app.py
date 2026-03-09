import streamlit as st

st.set_page_config(
    page_title="Grupo 8 · Interlog",
    page_icon="🔷",
    layout="wide"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=DM+Sans:wght@300;400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}

.stApp {
    background: linear-gradient(160deg, #0f3d4a 0%, #123d4a 40%, #0d3240 100%) !important;
}

.block-container {
    padding: 3rem 4rem 4rem 4rem;
    max-width: 1200px;
}

.portal-header {
    text-align: center;
    padding: 20px 0 50px 0;
}

.portal-eyebrow {
    font-family: 'Outfit', sans-serif;
    font-size: 0.65rem;
    font-weight: 500;
    letter-spacing: 0.3em;
    text-transform: uppercase;
    color: #5bbfcf;
    margin-bottom: 16px;
}

.portal-title {
    font-family: 'Outfit', sans-serif;
    font-size: 3rem;
    font-weight: 800;
    color: #ffffff;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    line-height: 1;
}

.portal-title span { color: #5bbfcf; }

.portal-subtitle {
    font-size: 0.75rem;
    font-weight: 300;
    letter-spacing: 0.22em;
    text-transform: uppercase;
    color: rgba(255,255,255,0.55);
    margin-top: 12px;
}

.divider {
    width: 40px;
    height: 2px;
    background: linear-gradient(90deg, #5bbfcf, transparent);
    margin: 20px auto 0 auto;
}

.section-label {
    font-family: 'Outfit', sans-serif;
    font-size: 0.62rem;
    font-weight: 600;
    letter-spacing: 0.25em;
    text-transform: uppercase;
    color: rgba(255,255,255,0.4);
    margin-bottom: 20px;
    border-left: 2px solid #5bbfcf;
    padding-left: 10px;
}

.card-wrapper {
    background: rgba(255,255,255,0.07);
    border: 1px solid rgba(91,191,207,0.25);
    border-radius: 20px;
    padding: 28px 26px;
    margin-bottom: 4px;
    position: relative;
    transition: all 0.3s ease;
    box-shadow: 0 4px 24px rgba(0,0,0,0.2);
}

.card-wrapper:hover {
    background: rgba(91,191,207,0.12);
    border-color: rgba(91,191,207,0.55);
    transform: translateY(-2px);
    box-shadow: 0 12px 36px rgba(0,0,0,0.3);
}

.card-tag {
    display: inline-block;
    font-family: 'Outfit', sans-serif;
    font-size: 0.58rem;
    font-weight: 600;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: #5bbfcf;
    border: 1px solid rgba(91,191,207,0.4);
    padding: 3px 10px;
    border-radius: 20px;
    margin-bottom: 14px;
}

.card-icon {
    font-size: 1.8rem;
    margin-bottom: 10px;
    display: block;
}

.card-name {
    font-family: 'Outfit', sans-serif;
    font-size: 1.05rem;
    font-weight: 600;
    color: #ffffff;
    margin-bottom: 10px;
    line-height: 1.3;
}

.card-desc {
    font-size: 0.80rem;
    color: rgba(255,255,255,0.65);
    font-weight: 300;
    line-height: 1.65;
    margin-bottom: 18px;
}

.card-cta {
    font-family: 'Outfit', sans-serif;
    font-size: 0.72rem;
    font-weight: 500;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #5bbfcf;
}

.coming-soon {
    background: rgba(255,255,255,0.03);
    border: 1.5px dashed rgba(91,191,207,0.18);
    border-radius: 20px;
    padding: 28px;
    text-align: center;
    color: rgba(255,255,255,0.2);
    font-size: 0.78rem;
    letter-spacing: 0.12em;
    font-style: italic;
    margin-top: 4px;
}

.portal-footer {
    text-align: center;
    margin-top: 48px;
    font-size: 0.62rem;
    color: rgba(255,255,255,0.2);
    letter-spacing: 0.2em;
    text-transform: uppercase;
}

.footer-line {
    width: 100%;
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(91,191,207,0.25), transparent);
    margin-bottom: 20px;
}

.stLinkButton a {
    background: transparent !important;
    border: 1px solid rgba(91,191,207,0.45) !important;
    color: #5bbfcf !important;
    border-radius: 10px !important;
    font-family: 'Outfit', sans-serif !important;
    font-size: 0.72rem !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
}

.stLinkButton a:hover {
    background: rgba(91,191,207,0.15) !important;
    border-color: #5bbfcf !important;
}
</style>
""", unsafe_allow_html=True)

# HEADER
st.markdown("""
<div class="portal-header">
    <div class="portal-eyebrow">Interlog Comercio Exterior</div>
    <div class="portal-title">GRUPO <span>8</span></div>
    <div class="portal-subtitle">Ecosistema de Herramientas Operativas</div>
    <div class="divider"></div>
</div>
""", unsafe_allow_html=True)

st.markdown('<div class="section-label">Herramientas disponibles</div>', unsafe_allow_html=True)

projects = [
    {
        "icon": "✅",
        "name": "Corrector Co Natura",
        "tag": "Auditoría",
        "desc": "Validación automática del Certificado de Origen para la cuenta Natura. Detecta inconsistencias y genera reporte de correctos.",
        "url": "https://corrector-co-natura.streamlit.app/"
    },
    {
        "icon": "📋",
        "name": "Corrector Descripciones Finning",
        "tag": "Auditoría",
        "desc": "Control y corrección de descripciones de mercadería para la cuenta Finning. Verifica y normaliza la uniformidad de datos.",
        "url": "https://corrector-descripciones.streamlit.app/"
    },
    {
        "icon": "📊",
        "name": "KPI Finning",
        "tag": "Reportes",
        "desc": "Dashboard de indicadores clave de desempeño operativo para la cuenta Finning. Visualización de métricas y seguimiento de gestión.",
        "url": "https://interlog-kpi-finning.streamlit.app/"
    },
]

cols = st.columns(3)

for i, p in enumerate(projects):
    with cols[i]:
        st.markdown(f"""
        <div class="card-wrapper">
            <div class="card-tag">{p['tag']}</div>
            <span class="card-icon">{p['icon']}</span>
            <div class="card-name">{p['name']}</div>
            <div class="card-desc">{p['desc']}</div>
            <div class="card-cta">Ingresar →</div>
        </div>
        """, unsafe_allow_html=True)
        st.link_button("Abrir herramienta", p['url'], use_container_width=True)

st.markdown("""
<div class="coming-soon">
    Nuevas herramientas próximamente...
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="portal-footer">
    <div class="footer-line"></div>
    Grupo 8 · Interlog Comercio Exterior · 2025
</div>
""", unsafe_allow_html=True)
