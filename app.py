import streamlit as st

st.set_page_config(
    page_title="Grupo 8 · Interlog",
    page_icon="🔷",
    layout="wide"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=DM+Sans:wght@300;400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}

.main {
    background-color: #f0f4f6;
}

.block-container {
    padding-top: 2rem;
    padding-bottom: 2rem;
    max-width: 1100px;
}

/* Header */
.portal-header {
    text-align: center;
    padding: 40px 0 10px 0;
}

.portal-title {
    font-family: 'Outfit', sans-serif;
    font-size: 2.2rem;
    font-weight: 700;
    color: #1e5f6b;
    letter-spacing: 0.06em;
    text-transform: uppercase;
}

.portal-subtitle {
    font-size: 0.78rem;
    font-weight: 400;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: #7a9aaa;
    margin-top: 6px;
}

.divider {
    width: 60px;
    height: 3px;
    background: #1e5f6b;
    margin: 16px auto 40px auto;
    border-radius: 2px;
}

/* Section title */
.section-label {
    font-family: 'Outfit', sans-serif;
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: #7a9aaa;
    margin-bottom: 14px;
    margin-top: 8px;
}

/* Cards */
.project-card {
    background: #1e5f6b;
    border-radius: 14px;
    padding: 22px 24px;
    margin-bottom: 14px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    transition: all 0.2s ease;
    box-shadow: 0 4px 18px rgba(30,95,107,0.13);
    cursor: pointer;
    text-decoration: none;
}

.project-card:hover {
    background: #236070;
    box-shadow: 0 8px 28px rgba(30,95,107,0.22);
    transform: translateY(-2px);
}

.card-left {
    display: flex;
    align-items: center;
    gap: 16px;
}

.card-icon {
    font-size: 1.6rem;
    min-width: 36px;
    text-align: center;
}

.card-name {
    font-family: 'Outfit', sans-serif;
    font-size: 1rem;
    font-weight: 600;
    color: white;
    letter-spacing: 0.01em;
}

.card-desc {
    font-size: 0.78rem;
    color: rgba(255,255,255,0.65);
    margin-top: 2px;
    font-weight: 300;
}

.card-tag {
    font-size: 0.65rem;
    font-weight: 600;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: rgba(255,255,255,0.5);
    border: 1px solid rgba(255,255,255,0.2);
    padding: 3px 10px;
    border-radius: 20px;
    white-space: nowrap;
}

/* Footer */
.portal-footer {
    text-align: center;
    margin-top: 50px;
    font-size: 0.72rem;
    color: #aac4cc;
    letter-spacing: 0.08em;
}
</style>
""", unsafe_allow_html=True)

# HEADER
st.markdown("""
<div class="portal-header">
    <div class="portal-title">GRUPO 8</div>
    <div class="portal-subtitle">Ecosistema de Herramientas · Interlog Comercio Exterior</div>
    <div class="divider"></div>
</div>
""", unsafe_allow_html=True)

# PROJECTS DATA
projects = [
    {
        "icon": "✅",
        "name": "Correctos Co Natura",
        "desc": "Validación y control de documentos Co Natura",
        "tag": "Auditoría",
        "url": "https://corrector-co-natura.streamlit.app/"
    },
    {
        "icon": "📋",
        "name": "Correctos Descripciones Finning",
        "desc": "Corrección y validación de descripciones Finning",
        "tag": "Auditoría",
        "url": "https://corrector-descripciones.streamlit.app/"
    },
    {
        "icon": "📊",
        "name": "KPI Finning",
        "desc": "Dashboard de indicadores clave de desempeño Finning",
        "tag": "Reportes",
        "url": "https://interlog-kpi-finning.streamlit.app/"
    },
]

# SECTION
st.markdown('<div class="section-label">Herramientas disponibles</div>', unsafe_allow_html=True)

for p in projects:
    st.markdown(f"""
    <a class="project-card" href="{p['url']}" target="_blank">
        <div class="card-left">
            <div class="card-icon">{p['icon']}</div>
            <div>
                <div class="card-name">{p['name']}</div>
                <div class="card-desc">{p['desc']}</div>
            </div>
        </div>
        <div class="card-tag">{p['tag']}</div>
    </a>
    """, unsafe_allow_html=True)

# COMING SOON
st.markdown("""
<div style="
    border: 1.5px dashed #b0cdd4;
    border-radius: 14px;
    padding: 22px 24px;
    margin-top: 6px;
    text-align: center;
    color: #9ab8c0;
    font-size: 0.85rem;
    letter-spacing: 0.05em;
">
    Nuevas herramientas próximamente...
</div>
""", unsafe_allow_html=True)

# FOOTER
st.markdown("""
<div class="portal-footer">
    GRUPO 8 · INTERLOG COMERCIO EXTERIOR · 2025
</div>
""", unsafe_allow_html=True)
