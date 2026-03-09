import streamlit as st

st.set_page_config(
    page_title="Grupo 8 · Interlog",
    page_icon="🔷",
    layout="wide"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=DM+Sans:ital,wght@0,300;0,400;0,500;1,300&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}

.stApp {
    background: #0d2b33;
    background-image: 
        radial-gradient(ellipse at 20% 20%, rgba(42,122,138,0.15) 0%, transparent 60%),
        radial-gradient(ellipse at 80% 80%, rgba(30,95,107,0.12) 0%, transparent 60%);
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
    color: #3a9aaa;
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

.portal-title span {
    color: #3a9aaa;
}

.portal-subtitle {
    font-size: 0.75rem;
    font-weight: 300;
    letter-spacing: 0.22em;
    text-transform: uppercase;
    color: rgba(255,255,255,0.35);
    margin-top: 12px;
}

.divider {
    width: 40px;
    height: 2px;
    background: linear-gradient(90deg, #3a9aaa, transparent);
    margin: 20px auto 0 auto;
}

.section-label {
    font-family: 'Outfit', sans-serif;
    font-size: 0.62rem;
    font-weight: 600;
    letter-spacing: 0.25em;
    text-transform: uppercase;
    color: rgba(255,255,255,0.25);
    margin-bottom: 20px;
    border-left: 2px solid #3a9aaa;
    padding-left: 10px;
}

.bento-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 16px;
    margin-bottom: 16px;
}

.bento-card {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(58,154,170,0.2);
    border-radius: 20px;
    padding: 28px 26px;
    position: relative;
    overflow: hidden;
    transition: all 0.3s ease;
    text-decoration: none;
    display: block;
    cursor: pointer;
}

.bento-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(58,154,170,0.5), transparent);
}

.bento-card:hover {
    background: rgba(58,154,170,0.1);
    border-color: rgba(58,154,170,0.5);
    transform: translateY(-4px);
    box-shadow: 0 20px 40px rgba(0,0,0,0.3), 0 0 0 1px rgba(58,154,170,0.2);
}

.card-tag {
    display: inline-block;
    font-family: 'Outfit', sans-serif;
    font-size: 0.58rem;
    font-weight: 600;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: #3a9aaa;
    border: 1px solid rgba(58,154,170,0.35);
    padding: 3px 10px;
    border-radius: 20px;
    margin-bottom: 18px;
}

.card-icon {
    font-size: 1.8rem;
    margin-bottom: 14px;
    display: block;
}

.card-name {
    font-family: 'Outfit', sans-serif;
    font-size: 1.05rem;
    font-weight: 600;
    color: #ffffff;
    letter-spacing: 0.01em;
    margin-bottom: 8px;
    line-height: 1.3;
}

.card-desc {
    font-size: 0.78rem;
    color: rgba(255,255,255,0.45);
    font-weight: 300;
    line-height: 1.6;
    margin-bottom: 22px;
}

.card-cta {
    display: flex;
    align-items: center;
    gap: 6px;
    font-family: 'Outfit', sans-serif;
    font-size: 0.72rem;
    font-weight: 500;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #3a9aaa;
}

.bento-card:hover .card-cta {
    gap: 10px;
}

.coming-soon {
    background: rgba(255,255,255,0.02);
    border: 1.5px dashed rgba(58,154,170,0.15);
    border-radius: 20px;
    padding: 28px 26px;
    text-align: center;
    color: rgba(255,255,255,0.15);
    font-size: 0.78rem;
    letter-spacing: 0.12em;
    font-style: italic;
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: 80px;
}

.portal-footer {
    text-align: center;
    margin-top: 48px;
    font-size: 0.62rem;
    color: rgba(255,255,255,0.15);
    letter-spacing: 0.2em;
    text-transform: uppercase;
}

.footer-line {
    width: 100%;
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(58,154,170,0.2), transparent);
    margin-bottom: 20px;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="portal-header">
    <div class="portal-eyebrow">Interlog Comercio Exterior</div>
    <div class="portal-title">GRUPO <span>8</span></div>
    <div class="portal-subtitle">Ecosistema de Herramientas Operativas</div>
    <div class="divider"></div>
</div>
""", unsafe_allow_html=True)

st.markdown('<div class="section-label">Herramientas disponibles</div>', unsafe_allow_html=True)

st.markdown("""
<div class="bento-grid">

    <a class="bento-card" href="https://corrector-co-natura.streamlit.app/" target="_blank">
        <div class="card-tag">Auditoría</div>
        <span class="card-icon">✅</span>
        <div class="card-name">Correctos Co Natura</div>
        <div class="card-desc">Validación automática de documentos de importación para la cuenta Co Natura. Detecta inconsistencias y genera reporte de correctos.</div>
        <div class="card-cta">Ingresar →</div>
    </a>

    <a class="bento-card" href="https://corrector-descripciones.streamlit.app/" target="_blank">
        <div class="card-tag">Auditoría</div>
        <span class="card-icon">📋</span>
        <div class="card-name">Correctos Descripciones Finning</div>
        <div class="card-desc">Control y corrección de descripciones de mercadería para despachos Finning. Verifica cumplimiento normativo y uniformidad de datos.</div>
        <div class="card-cta">Ingresar →</div>
    </a>

    <a class="bento-card" href="https://interlog-kpi-finning.streamlit.app/" target="_blank">
        <div class="card-tag">Reportes</div>
        <span class="card-icon">📊</span>
        <div class="card-name">KPI Finning</div>
        <div class="card-desc">Dashboard de indicadores clave de desempeño operativo para la cuenta Finning. Visualización de métricas y seguimiento de gestión.</div>
        <div class="card-cta">Ingresar →</div>
    </a>

</div>

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
