import streamlit as st
import sqlite3
import pandas as pd
import os
import gzip
import shutil
import requests
import re

st.set_page_config(
    page_title="Consulta Descripciones CAT",
    page_icon="🔍",
    layout="wide"
)

st.markdown("""
<style>
    [data-testid="stToolbar"] { visibility: hidden !important; }
    [data-testid="stDecoration"] { display: none !important; }
    a[href*="github.com"] { display: none !important; }
</style>
""", unsafe_allow_html=True)

st.title("🔍 Consulta de Descripciones CAT")
st.caption("Base de datos de partes Caterpillar en español — INTERLOG Comercio Exterior")

DB_PATH = "cat_partes.db"
DB_GZ_PATH = "cat_partes.db.gz"
HF_URL = "https://huggingface.co/datasets/AlvaIA/cat-partes-db/resolve/main/cat_partes.db.gz"

def normalizar_parte(raw):
    s = str(raw).strip().upper()
    s = re.sub(r'\s+', '', s)
    if not s or s in ('NAN', 'NONE', ''):
        return raw
    # Sacar guión y verificar si es numérico puro
    s_sin_guion = s.replace('-', '')
    if re.match(r'^\d+$', s_sin_guion):
        # 6 dígitos → agregar cero adelante → 7 dígitos
        if len(s_sin_guion) == 6:
            s_sin_guion = '0' + s_sin_guion
        # 7+ dígitos → dividir XXX-XXXX
        if len(s_sin_guion) >= 7:
            return s_sin_guion[:-4] + '-' + s_sin_guion[-4:]
    # Alfanumérico tipo 1P0459 → 1P-0459
    m = re.match(r'^([A-Z0-9]{2,4})(\d{4,})$', s)
    if m:
        return m.group(1) + '-' + m.group(2)
    # Ya tiene guión y no es numérico puro → devolver tal cual
    if '-' in s:
        return s
    return s

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

def consultar_db(conn, parts_unicos):
    placeholders = ','.join(['?' for _ in parts_unicos])
    query = f"""
        SELECT part_number, nombre, descripcion_corta, descripcion_larga
        FROM partes
        WHERE UPPER(part_number) IN ({placeholders})
    """
    return pd.read_sql_query(query, conn, params=parts_unicos)

conn = get_db()

st.markdown("### Ingresá los números de parte")
tab1, tab2 = st.tabs(["✏️ Ingresar manualmente", "📂 Subir Excel"])

modo = None
parts_raw = []
df_original = None

with tab1:
    input_text = st.text_area(
        "Un número por línea, o separados por coma (con o sin guión):",
        height=150,
        placeholder="Ejemplo:\n1095724\n1R-0750\n2T5626\n321267"
    )
    if input_text.strip():
        modo = "manual"
        raw = input_text.replace(',', '\n').replace(';', '\n')
        parts_raw = [p.strip() for p in raw.splitlines() if p.strip()]

with tab2:
    st.markdown("Subí un Excel con los números de parte en la **primera columna** (sin importar el nombre del encabezado).")
    uploaded_file = st.file_uploader("Seleccioná el archivo Excel", type=["xlsx", "xls"])
    if uploaded_file:
        try:
            df_original = pd.read_excel(uploaded_file, header=0, dtype=str)
            col = df_original.columns[0]
            parts_raw = [str(p).strip() for p in df_original[col].dropna() if str(p).strip()]
            modo = "excel"
            st.success(f"✅ {len(parts_raw)} filas cargadas ({len(set(parts_raw))} únicas)")
        except Exception as e:
            st.error(f"Error al leer el archivo: {e}")

col1, col2 = st.columns([3, 1])
with col2:
    buscar = st.button("🔍 Buscar", use_container_width=True, type="primary")

if buscar:
    if not parts_raw:
        st.warning("Ingresá al menos un número de parte.")
    else:
        parts_norm = [normalizar_parte(p) for p in parts_raw]
        parts_unicos = list(dict.fromkeys(parts_norm))

        df_result = consultar_db(conn, parts_unicos)
        df_result.columns = ["N° de Parte", "Nombre", "Descripción Corta", "Descripción Larga"]
        lookup = df_result.set_index("N° de Parte").to_dict(orient="index")

        if modo == "excel" and df_original is not None:
            col_parte = df_original.columns[0]
            df_original["_norm"] = df_original[col_parte].apply(lambda x: normalizar_parte(str(x)))
            df_original["Nombre"] = df_original["_norm"].map(lambda x: lookup.get(x, {}).get("Nombre", ""))
            df_original["Descripción Corta"] = df_original["_norm"].map(lambda x: lookup.get(x, {}).get("Descripción Corta", ""))
            df_original["Descripción Larga"] = df_original["_norm"].map(lambda x: lookup.get(x, {}).get("Descripción Larga", ""))
            df_original = df_original.drop(columns=["_norm"])
            df_salida = df_original
        else:
            df_salida = df_result

        encontrados = len([p for p in parts_unicos if p in lookup])
        no_encontrados = [p for p in parts_unicos if p not in lookup]

        st.markdown(f"### Resultados — {encontrados} de {len(parts_unicos)} únicos encontrados")

        if no_encontrados:
            st.warning(f"**No encontrados ({len(no_encontrados)}):** {', '.join(no_encontrados)}")

        if not df_salida.empty:
            st.dataframe(df_salida, use_container_width=True, hide_index=True)
            df_salida.to_excel("/tmp/resultado_cat.xlsx", index=False)
            with open("/tmp/resultado_cat.xlsx", "rb") as f:
                st.download_button(
                    label="📥 Descargar Excel con resultados",
                    data=f,
                    file_name="resultado_cat.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

st.divider()
st.caption("Base de datos: 1.708.979 partes CAT en español | INTERLOG © 2025")
