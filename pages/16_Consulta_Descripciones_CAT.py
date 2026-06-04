import streamlit as st
import sqlite3
import pandas as pd
import os
import gzip
import shutil
import requests
import re
import io

st.set_page_config(page_title="Consulta Descripciones CAT", page_icon="🔍", layout="wide")

st.markdown("""
<style>
    .block-container { padding-top: 2rem; }
    .step-header {
        background: #1e2a35;
        border-left: 4px solid #4fc3f7;
        padding: 0.6rem 1rem;
        border-radius: 0 8px 8px 0;
        margin-bottom: 1rem;
        font-weight: 700;
        font-size: 1rem;
        color: #e0f7ff !important;
    }
    .instruccion {
        background: #1a2744;
        border: 1px solid #1e3a5f;
        border-radius: 8px;
        padding: 0.75rem 1rem;
        font-size: 0.9rem;
        margin-bottom: 1rem;
        color: #cfd8dc;
        line-height: 1.8;
    }
    .metric-box {
        background: #1e2a35;
        border-radius: 8px;
        padding: 0.5rem 0.75rem;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    [data-testid="stToolbar"] { visibility: hidden !important; }
    [data-testid="stDecoration"] { display: none !important; }
    a[href*="github.com"] { display: none !important; }
</style>
""", unsafe_allow_html=True)

st.markdown("## 🔍 Consulta de Descripciones CAT")
st.markdown("Buscá descripciones en español de repuestos Caterpillar — base de datos local de **1.708.979 partes**.")
st.divider()

DB_PATH = "cat_partes.db"
DB_GZ_PATH = "cat_partes.db.gz"
HF_URL = "https://huggingface.co/datasets/AlvaIA/cat-partes-db/resolve/main/cat_partes.db.gz"

def normalizar_parte(code):
    code = str(code).strip().upper()
    code = re.sub(r'\s+', '', code)
    if not code or code in ('NAN', 'NONE', ''):
        return None
    if '-' in code:
        return code
    match = re.match(r'^(.+?)(\d{4})$', code)
    if match:
        return f"{match.group(1)}-{match.group(2)}"
    return code

def is_valid_gz(path):
    try:
        with gzip.open(path, 'rb') as f:
            f.read(10)
        return True
    except:
        return False

def download_db():
    with st.spinner("Descargando base de datos (74MB)... puede tardar unos minutos."):
        response = requests.get(HF_URL, stream=True)
        response.raise_for_status()
        with open(DB_GZ_PATH, 'wb') as f:
            for chunk in response.iter_content(chunk_size=32768):
                if chunk:
                    f.write(chunk)

def get_db():
    if os.path.exists(DB_GZ_PATH) and not is_valid_gz(DB_GZ_PATH):
        os.remove(DB_GZ_PATH)
    if os.path.exists(DB_PATH) and os.path.getsize(DB_PATH) < 1000:
        os.remove(DB_PATH)
    if not os.path.exists(DB_PATH):
        if not os.path.exists(DB_GZ_PATH):
            download_db()
        with st.spinner("Descomprimiendo base de datos..."):
            with gzip.open(DB_GZ_PATH, 'rb') as f_in:
                with open(DB_PATH, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
    return sqlite3.connect(DB_PATH, check_same_thread=False)

conn = get_db()

# ─── PASO 1: CARGAR CÓDIGOS ───────────────────────────────────────────────
st.markdown('<div class="step-header">📂 Paso 1 — Cargar códigos de parte</div>', unsafe_allow_html=True)
st.markdown("""
<div class="instruccion">
Ingresá los códigos manualmente o subí un Excel con los códigos en la primera columna.<br>
Los códigos <strong>con o sin guión</strong> son aceptados — el sistema los normaliza automáticamente.<br>
Ejemplos: <code>1095724</code> → <code>109-5724</code> &nbsp;|&nbsp; <code>2T5626</code> → <code>2T-5626</code>
</div>
""", unsafe_allow_html=True)

metodo = st.radio("Método de carga", ["✏️ Ingresar manualmente", "📂 Subir Excel"], horizontal=True)

modo = None
parts_raw = []
df_original = None

if metodo == "✏️ Ingresar manualmente":
    input_text = st.text_area(
        "Un código por línea, o separados por coma:",
        height=150,
        placeholder="Ejemplo:\n1095724\n1R-0750\n2T5626\n023-6598"
    )
    if input_text.strip():
        modo = "manual"
        raw = input_text.replace(',', '\n').replace(';', '\n')
        parts_raw = [p.strip() for p in raw.splitlines() if p.strip()]

else:
    uploaded_file = st.file_uploader("Subí el archivo Excel (códigos en la primera columna):", type=["xlsx", "xls"])
    if uploaded_file:
        try:
            df_original = pd.read_excel(uploaded_file, header=0, dtype=str)
            col = df_original.columns[0]
            parts_raw = [str(p).strip() for p in df_original[col].dropna() if str(p).strip()]
            modo = "excel"
            st.success(f"✅ {len(parts_raw)} filas cargadas — columna detectada: **{col}** | Únicos: {len(set(parts_raw))}")
        except Exception as e:
            st.error(f"Error al leer el archivo: {e}")

buscar = st.button("🔍 Buscar descripciones", type="primary", disabled=(len(parts_raw) == 0))

# ─── PASO 2: RESULTADOS ───────────────────────────────────────────────────
if buscar and parts_raw:
    parts_norm = [normalizar_parte(p) for p in parts_raw]
    parts_unicos = list(dict.fromkeys([p for p in parts_norm if p]))

    placeholders = ','.join(['?' for _ in parts_unicos])
    query = f"""
        SELECT part_number, nombre, descripcion_corta, descripcion_larga
        FROM partes WHERE UPPER(part_number) IN ({placeholders})
    """
    df_result = pd.read_sql_query(query, conn, params=parts_unicos)
    df_result.columns = ["N° de Parte", "Nombre", "Descripción Corta", "Descripción Larga"]
    lookup = df_result.set_index("N° de Parte").to_dict(orient="index")

    if modo == "excel" and df_original is not None:
        col_parte = df_original.columns[0]
        df_original["_norm"] = df_original[col_parte].apply(lambda x: normalizar_parte(str(x)))
        df_original["Nombre"] = df_original["_norm"].map(lambda x: lookup.get(x, {}).get("Nombre", "") if x else "")
        df_original["Descripción Corta"] = df_original["_norm"].map(lambda x: lookup.get(x, {}).get("Descripción Corta", "") if x else "")
        df_original["Descripción Larga"] = df_original["_norm"].map(lambda x: lookup.get(x, {}).get("Descripción Larga", "") if x else "")
        df_original = df_original.drop(columns=["_norm"])
        df_salida = df_original
    else:
        df_salida = df_result

    encontrados = len([p for p in parts_unicos if p in lookup])
    no_encontrados = [p for p in parts_unicos if p not in lookup]

    st.divider()
    st.markdown('<div class="step-header">📊 Paso 2 — Resultados</div>', unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    c1.metric("🔎 Únicos consultados", len(parts_unicos))
    c2.metric("✅ Encontrados", encontrados)
    c3.metric("❌ No encontrados", len(no_encontrados))

    if no_encontrados:
        st.warning(f"**No encontrados ({len(no_encontrados)}):** {', '.join(no_encontrados)}")

    st.dataframe(df_salida, use_container_width=True, hide_index=True)

    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine='openpyxl') as writer:
        df_salida.to_excel(writer, index=False, sheet_name='Descripciones CAT')
    st.download_button(
        label="📥 Descargar Excel con resultados",
        data=buf.getvalue(),
        file_name="descripciones_cat.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

st.divider()
st.caption("Base de datos: 1.708.979 partes CAT en español | INTERLOG © 2025")
