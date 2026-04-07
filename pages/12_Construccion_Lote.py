import streamlit as st
import base64
import json
import pandas as pd
import openpyxl
import xlrd
from xlutils.copy import copy as xl_copy
import pdfplumber
import re
import io
import os
from datetime import datetime

# ─── ESTILOS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;600&display=swap');

html, body, [class*="css"] {
    font-family: 'IBM Plex Sans', sans-serif;
}
.stApp { background-color: #0f1117; }

h1, h2, h3 { font-family: 'IBM Plex Mono', monospace; color: #f0f0f0; }

.titulo-app {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 2rem;
    font-weight: 600;
    color: #FFD600;
    border-bottom: 2px solid #FFD600;
    padding-bottom: 0.5rem;
    margin-bottom: 1.5rem;
}
.paso-header {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.85rem;
    color: #FFD600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    margin-bottom: 0.3rem;
}
.info-box {
    background: #1a1f2e;
    border: 1px solid #2a2f3e;
    border-left: 3px solid #FFD600;
    padding: 0.8rem 1rem;
    border-radius: 4px;
    margin: 0.5rem 0;
    font-size: 0.9rem;
    color: #c0c0c0;
}
.alerta-box {
    background: #1f1510;
    border: 1px solid #5a3a1a;
    border-left: 3px solid #FF8C00;
    padding: 0.8rem 1rem;
    border-radius: 4px;
    margin: 0.5rem 0;
    font-size: 0.9rem;
    color: #ffb060;
}
.ok-box {
    background: #101f15;
    border: 1px solid #1a5a2a;
    border-left: 3px solid #00c853;
    padding: 0.8rem 1rem;
    border-radius: 4px;
    margin: 0.5rem 0;
    font-size: 0.9rem;
    color: #60d080;
}
.stButton > button {
    background-color: #FFD600;
    color: #0f1117;
    font-family: 'IBM Plex Mono', monospace;
    font-weight: 600;
    border: none;
    border-radius: 4px;
    padding: 0.6rem 1.5rem;
}
.stButton > button:hover {
    background-color: #ffe033;
    color: #0f1117;
}
div[data-baseweb="select"] > div {
    background-color: #1a1f2e;
    border-color: #2a2f3e;
    color: #f0f0f0;
}
.stRadio label { color: #c0c0c0 !important; }
.stRadio > div { color: #c0c0c0 !important; }

/* Expander fondo oscuro */
div[data-testid="stExpander"] {
    background-color: #1a1f2e !important;
    border: 1px solid #2a2f3e !important;
    border-radius: 6px !important;
}
div[data-testid="stExpander"] summary {
    color: #f0f0f0 !important;
}
div[data-testid="stExpander"] > div > div {
    background-color: #1a1f2e !important;
}

/* Labels e inputs */
label { color: #c0c0c0 !important; }
.stTextInput label { color: #c0c0c0 !important; }
.stSelectbox label { color: #c0c0c0 !important; }
.stFileUploader label { color: #c0c0c0 !important; }
.stTextInput input {
    background-color: #1a1f2e !important;
    color: #f0f0f0 !important;
    border-color: #2a2f3e !important;
}
p, span, div { color: #c0c0c0; }
</style>
""", unsafe_allow_html=True)

# ─── CONSTANTES ────────────────────────────────────────────────────────────
PAISES = {
    "BRASIL": 203, "BRAZIL": 203,
    "ESTADOS UNIDOS": 212, "USA": 212, "UNITED STATES": 212, "US": 212,
    "REINO UNIDO": 426, "UNITED KINGDOM": 426, "UK": 426, "GREAT BRITAIN": 426,
    "ALEMANIA": 438, "GERMANY": 438, "DEUTSCHLAND": 438,
    "ITALIA": 417, "ITALY": 417,
    "AUSTRIA": 405,
    "SUECIA": 429, "SWEDEN": 429,
    "NORUEGA": 422, "NORWAY": 422,
    "FINLANDIA": 411, "FINLAND": 411,
    "REPUBLICA CHECA": 451, "REP. CHECA": 451, "CZECH REPUBLIC": 451, "CZ": 451,
    "TAIWAN": 313,
    "CHINA": 310,
    "VIETNAM": 337,
    "COREA DEL SUR": 309, "SOUTH KOREA": 309, "KOREA": 309,
    "JAPON": 320, "JAPAN": 320,
    "INDIA": 315,
    "SUIZA": 430, "SWITZERLAND": 430,
    "PAISES BAJOS": 423, "NETHERLANDS": 423, "HOLLAND": 423,
    "FRANCE": 412, "FRANCIA": 412,
    "ESPAÑA": 410, "SPAIN": 410,
    "BELGICA": 406, "BELGIUM": 406,
    "CANADA": 204,
    "MEXICO": 218, "MÉXICO": 218,
    "ARGENTINA": 200,
    "CHILE": 208,
    "PERU": 222, "PERÚ": 222,
    "COLOMBIA": 205,
    "SINGAPORE": 333, "SINGAPUR": 333,
    "MALAYSIA": 326, "MALASIA": 326,
    "INDONESIA": 316,
    "THAILAND": 335, "TAILANDIA": 335,
    "TURQUIA": 436, "TURKEY": 436,
    "ISRAEL": 319,
    "SUDAFRICA": 159, "SOUTH AFRICA": 159,
    "AUSTRALIA": 501,
    "NUEVA ZELANDA": 504, "NEW ZEALAND": 504,
    "POLONIA": 424, "POLAND": 424,
    "HUNGRIA": 414, "HUNGARY": 414,
    "RUMANIA": 427, "ROMANIA": 427,
    "BULGARIA": 407,
    "CROACIA": 447, "CROATIA": 447,
    "ESLOVAQUIA": 448, "SLOVAKIA": 448,
    "ESLOVENIA": 449, "SLOVENIA": 449,
    "RUSIA": 444, "RUSSIA": 444,
    "UCRANIA": 445, "UKRAINE": 445,
    "PORTUGAL": 425,
    "GRECIA": 413, "GREECE": 413,
    "LUXEMBURGO": 419, "LUXEMBOURG": 419,
    "IRLANDA": 415, "IRELAND": 415,
    "DINAMARCA": 409, "DENMARK": 409,
    "HONG KONG": 341,
}

UNIDAD_CME = {
    "KG": 1, "KILOGRAM": 1, "KILOGRAMO": 1,
    "MT": 2, "M": 2, "METRO": 2, "METROS": 2,
    "M2": 3, "M²": 3,
    "M3": 4, "M³": 4,
    "L": 5, "LT": 5, "LITRO": 5, "LITROS": 5,
    "PC": 7, "UNI": 7, "UNIDAD": 7, "UNIT": 7, "PCS": 7, "UN": 7,
    "PAR": 8, "PAIR": 8,
    "DOC": 9, "DOCENA": 9,
    "G": 14, "GR": 14, "GRAMO": 14, "GRAMOS": 14, "GRAM": 14,
    "TON": 29, "TONELADA": 29,
    "ML": 47, "MILILITRO": 47,
}

UNIDAD_SIDOM = {
    1: "01 - KILOGRAMO",
    2: "02 - METROS",
    3: "03 - METRO CUADRADO",
    4: "04 - METRO CUBICO",
    5: "05 - LITROS",
    7: "07 - UNIDAD",
    8: "08 - PAR",
    9: "09 - DOCENA",
    14: "14 - GRAMO",
    29: "29 - TONELADA",
    47: "47 - MILILITRO",
}

# ─── FUNCIONES AUXILIARES ──────────────────────────────────────────────────
def get_codigo_pais(texto):
    if not texto:
        return None
    t = str(texto).strip().upper()
    # Buscar coincidencia directa
    for k, v in PAISES.items():
        if k in t or t in k:
            return v
    return None

def get_codigo_unidad(texto):
    if not texto:
        return 7
    t = str(texto).strip().upper()
    return UNIDAD_CME.get(t, 7)

def limpiar_numero(texto):
    if texto is None:
        return 0.0
    try:
        s = str(texto).strip()
        # Manejar formato europeo (1.234,56) vs americano (1,234.56)
        if ',' in s and '.' in s:
            if s.rfind(',') > s.rfind('.'):
                s = s.replace('.', '').replace(',', '.')
            else:
                s = s.replace(',', '')
        elif ',' in s:
            s = s.replace(',', '.')
        return float(s)
    except:
        return 0.0

def extraer_datos_factura_hci(texto_pdf):
    """Extrae ítems de facturas HCI/Natura tipo COMMERCIAL INVOICE."""
    items = []
    lineas = texto_pdf.split('\n')

    # Detectar moneda
    moneda = "USD"
    for l in lineas:
        if "Currency" in l or "CURRENCY" in l:
            if "USD" in l: moneda = "USD"
            elif "EUR" in l: moneda = "EUR"
            elif "ARS" in l: moneda = "ARS"
            elif "BRL" in l: moneda = "BRL"
            break

    # Detectar origen general de la factura
    origen_factura = None
    for l in lineas:
        if "PAIS DE ORIGEN" in l.upper() or "COUNTRY OF ORIGIN" in l.upper():
            idx = lineas.index(l)
            for j in range(idx, min(idx+3, len(lineas))):
                cod = get_codigo_pais(lineas[j])
                if cod:
                    origen_factura = cod
                    break
        if origen_factura:
            break

    # Detectar procedencia (país del exportador)
    procedencia_factura = origen_factura

    return moneda, origen_factura, procedencia_factura

def extraer_items_natura(texto_pdf):
    """
    Extrae ítems de factura Natura.
    Formato real de cada línea:
    50293720 1.050,000 KGIsoamyl Laurate... 1.050,000 13.272,66 13.936.293,00
    487685 210,000 KG Dimethicone... 210,000 64.107,54 13.462.583,40
    50443307 9000 PC Valvula Avon... 126,000 268,79 2.419.110,00
    """
    items = []
    lineas = texto_pdf.split('\n')
    origen = 203
    procedencia = 203
    moneda = "ARS"

    # Patrón: codigo cantidad UNIDAD(pegada o no)descripcion peso unitario total
    # La unidad puede estar pegada a la descripción (KGIsoamyl) o separada (KG Dimethicone)
    patron = re.compile(
        r'^(\d{5,8})\s+([\d.,]+)\s+(KG|G|PC|MT|L|LT|M)\s*(.+?)\s+([\d.,]+)\s+([\d.,]+)\s+([\d.,]+)\s*$',
        re.IGNORECASE
    )

    for l in lineas:
        l = l.strip()
        # Saltar líneas de subtotal (contienen NCM, NALADI, guiones)
        if "NCM" in l or "NALADI" in l or l.startswith("---") or l.startswith("===="):
            continue
        # Saltar líneas de volúmenes y pallets
        if any(skip in l for skip in ["VOLUMES", "Pallet", "PESO NETO", "PESO BRUTO",
                                        "CANTIDAD CAJAS", "TOTAL", "FLETE", "SEGURO",
                                        "MEDIDA", "CONDICIÓN", "OBSERVACIÓN", "MARCA",
                                        "IMPORTADOR", "RECEPTOR", "BENEFICIARIO"]):
            continue

        m = patron.match(l)
        if m:
            codigo = m.group(1).strip()
            cantidad_raw = m.group(2)
            unidad_raw = m.group(3).upper()
            descripcion = m.group(4).strip()
            peso_raw = m.group(5)
            ars_unit = m.group(6)
            ars_total = m.group(7)

            cantidad = limpiar_numero(cantidad_raw)
            peso = limpiar_numero(peso_raw)
            unitario = limpiar_numero(ars_unit)
            total = limpiar_numero(ars_total)
            unidad_cod = get_codigo_unidad(unidad_raw)

            # Calcular unitario si no viene (para ítems sin precio unitario explícito)
            if unitario == 0 and cantidad > 0:
                unitario = round(total / cantidad, 2)

            items.append({
                "codigo": codigo,
                "descripcion": descripcion,
                "cantidad": cantidad,
                "unidad_cod": unidad_cod,
                "unidad_raw": unidad_raw,
                "peso_neto": peso,
                "unitario": unitario,
                "total": total,
                "origen": origen,
                "procedencia": procedencia,
                "moneda": moneda,
            })

    return items

def extraer_items_hci(texto_pdf):
    """Extrae ítems de factura HCI (COMMERCIAL INVOICE con REFI CLI)."""
    items = []
    lineas = texto_pdf.split('\n')

    moneda = "USD"
    origen = 203
    procedencia = 203

    # Detectar origen
    for i, l in enumerate(lineas):
        if "ORIGEM" in l.upper() or "ORIGIN" in l.upper():
            for j in range(i, min(i+5, len(lineas))):
                cod = get_codigo_pais(lineas[j])
                if cod:
                    origen = cod
                    procedencia = cod
                    break

    # Patrón HCI: ITEM QUANT NET_KG DESCRIPTION REFI_CLI ORIGEM UNIT_PRICE TOTAL_PRICE
    patron = re.compile(
        r'^(\d+)\s+([\d.,]+)\s+([\d.,]+)\s+(.+?)\s+([\w_]+)\s+(\w+)\s+([\d.,]+)\s+([\d.,]+)$'
    )

    for l in lineas:
        m = patron.match(l.strip())
        if m:
            item_num = m.group(1)
            cantidad = limpiar_numero(m.group(2))
            peso = limpiar_numero(m.group(3))
            descripcion = m.group(4).strip()
            codigo = m.group(5).strip()
            origem_raw = m.group(6).strip()
            unitario = limpiar_numero(m.group(7))
            total = limpiar_numero(m.group(8))

            origen_item = get_codigo_pais(origem_raw) or origen

            items.append({
                "codigo": codigo,
                "descripcion": descripcion,
                "cantidad": cantidad,
                "unidad_cod": 7,  # PC por defecto en HCI
                "unidad_raw": "PC",
                "peso_neto": peso,
                "unitario": unitario,
                "total": total,
                "origen": origen_item,
                "procedencia": origen_item,
                "moneda": moneda,
            })

    return items

def extraer_items_wartsila(texto_pdf):
    """Extrae ítems de factura Wärtsilä."""
    items = []
    lineas = texto_pdf.split('\n')
    moneda = "EUR"

    # Patrón Wärtsilä: item_num part_no description origin hs_code qty net_weight unit_price vat total
    patron = re.compile(
        r'^(\d{6})\s+(\d+)\s+(.+?)\s+([A-Z]{2})\s+\d+\s+([\d.,]+)\s+PC\s+([\d.,]+)\s+[\d.,]+%\s+([\d.,]+)',
        re.IGNORECASE
    )

    for l in lineas:
        m = patron.match(l.strip())
        if m:
            codigo = m.group(2).strip()
            descripcion = m.group(3).strip()
            origen_iso = m.group(4).strip()
            cantidad = limpiar_numero(m.group(5))
            unitario = limpiar_numero(m.group(6))
            total = limpiar_numero(m.group(7))
            origen = get_codigo_pais(origen_iso) or 0

            items.append({
                "codigo": codigo,
                "descripcion": descripcion,
                "cantidad": cantidad,
                "unidad_cod": 7,
                "unidad_raw": "PC",
                "peso_neto": 0,  # se calcula después
                "unitario": unitario,
                "total": total,
                "origen": origen,
                "procedencia": origen,
                "moneda": moneda,
            })

    return items


def extraer_items_aesa_desde_excel(marcas_bytes):
    """
    Para AESA con PDF escaneado: extrae ítems directamente del Excel de marcas
    (solapa Pos) que tiene toda la info de la factura.
    Solo se usa cuando el PDF no tiene texto extraíble.
    """
    items = []
    try:
        df = pd.read_excel(io.BytesIO(marcas_bytes), sheet_name="Pos", dtype=str, skiprows=3)
        df = df[df["Pos"].str.match(r"^\d+$", na=False)].copy()

        for _, row in df.iterrows():
            cod = str(row.get("Código SAP del Material", "")).strip()
            desc = str(row.get("Descripción", "")).strip().replace("\n", " ")
            cant = limpiar_numero(row.get("Cantidad", 0))
            unid_raw = str(row.get("Unidad", "UNI")).strip().upper()
            unit = limpiar_numero(row.get("Precio Unitario de Posición", 0))
            total = limpiar_numero(row.get("Precio Total de Posición", 0))
            peso = limpiar_numero(row.get("Peso Neto Total de Posición (kg)", 0))
            origen_raw = str(row.get("Origen", "brasil")).strip()
            origen = get_codigo_pais(origen_raw) or 203

            if not cod or cant == 0:
                continue

            items.append({
                "codigo": cod,
                "descripcion": desc,
                "cantidad": cant,
                "unidad_cod": get_codigo_unidad(unid_raw),
                "unidad_raw": unid_raw,
                "peso_neto": peso,
                "unitario": unit,
                "total": total,
                "origen": origen,
                "procedencia": origen,
                "moneda": "USD",
            })
    except Exception as e:
        pass
    return items

def extraer_items_groq_vision(pdf_bytes):
    """Usa Groq Vision para extraer ítems de PDFs escaneados directamente como JSON."""
    try:
        from pdf2image import convert_from_bytes
        from groq import Groq
        groq_key = st.secrets.get("GROQ_API_KEY", "")
        if not groq_key:
            return []
        client = Groq(api_key=groq_key)
        images = convert_from_bytes(pdf_bytes, dpi=200)
        todos_items = []

        prompt = """Analizá esta factura comercial y extraé SOLO los ítems de la tabla de productos.
Para cada ítem retorná un objeto JSON con estos campos exactos:
- codigo: el código de material o REFI CLI (ej: O__CAP01331691, F__BL_04294047)
- descripcion: descripción del producto
- cantidad: número (ej: 4, 16, 20)
- unidad: unidad de medida (PC, KG, MT, G, L)
- peso_neto: peso neto en KG (número)
- unitario: precio unitario (número)
- total: precio total (número)
- origen: país de origen (ej: BRASIL, USA)

Retorná ÚNICAMENTE un array JSON válido, sin markdown, sin texto adicional.
Ejemplo: [{"codigo":"O__CAP01331691","descripcion":"CAP 3000","cantidad":4,"unidad":"PC","peso_neto":0.52,"unitario":11.42,"total":45.68,"origen":"BRASIL"}]"""

        for img in images:
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=90)
            img_b64 = base64.b64encode(buf.getvalue()).decode()
            response = client.chat.completions.create(
                model="meta-llama/llama-4-scout-17b-16e-instruct",
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}},
                        {"type": "text", "text": prompt}
                    ]
                }],
                max_tokens=3000
            )
            raw = response.choices[0].message.content.strip()
            # Limpiar posible markdown
            raw = raw.replace("```json", "").replace("```", "").strip()
            items_json = json.loads(raw)
            for it in items_json:
                todos_items.append({
                    "codigo": str(it.get("codigo", "")).strip(),
                    "descripcion": str(it.get("descripcion", "")).strip(),
                    "cantidad": float(it.get("cantidad", 0)),
                    "unidad_cod": get_codigo_unidad(str(it.get("unidad", "PC"))),
                    "unidad_raw": str(it.get("unidad", "PC")).upper(),
                    "peso_neto": float(it.get("peso_neto", 0)),
                    "unitario": float(it.get("unitario", 0)),
                    "total": float(it.get("total", 0)),
                    "origen": get_codigo_pais(str(it.get("origen", "BRASIL"))) or 203,
                    "procedencia": get_codigo_pais(str(it.get("origen", "BRASIL"))) or 203,
                    "moneda": "USD",
                })
        return todos_items
    except Exception as e:
        return []

def extraer_texto_pdf(pdf_bytes):
    """Extrae texto del PDF. Si está vacío retorna string vacío (se usará Groq Vision directamente)."""
    texto = ""
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                texto += t + "\n"
    return texto

def extraer_items_pdf(pdf_bytes, proveedor_detectado=None):
    """Extrae texto del PDF y detecta el tipo de factura."""
    texto = extraer_texto_pdf(pdf_bytes)

    # Si no hay texto → PDF escaneado → usar Groq Vision directamente
    if len(texto.strip()) < 50:
        items = extraer_items_groq_vision(pdf_bytes)
        return "escaneado_vision", items, ""

    # Detectar tipo de factura
    if "REFI CLI" in texto or "HCI" in texto.upper():
        return "hci", extraer_items_hci(texto), texto
    elif "Wärtsilä" in texto or "Wartsila" in texto:
        return "wartsila", extraer_items_wartsila(texto), texto
    elif "MATERIAL" in texto and "VENTA" in texto and "CANTIDAD" in texto and "Natura" in texto:
        return "natura", extraer_items_natura(texto), texto
    else:
        # Intentar HCI como fallback
        items = extraer_items_hci(texto)
        return "generico", items, texto

def leer_ncm(ncm_file_bytes, nombre_archivo):
    """Lee el Excel de NCMs y retorna diccionario codigo→NCM."""
    try:
        if nombre_archivo.endswith('.xlsm') or nombre_archivo.endswith('.xlsx'):
            # Intentar solapa Catálogo primero (Natura)
            try:
                df = pd.read_excel(io.BytesIO(ncm_file_bytes),
                                   sheet_name="Catálogo", dtype=str, skiprows=2)
                return dict(zip(
                    df["Código del artículo"].str.strip(),
                    df["NCM"].str.strip()
                ))
            except:
                pass
            # Intentar Hoja1 (AESA)
            try:
                df = pd.read_excel(io.BytesIO(ncm_file_bytes),
                                   sheet_name="Hoja1", dtype=str)
                cols = df.columns.tolist()
                cod_col = next((c for c in cols if "art" in c.lower() or "cod" in c.lower() or "material" in c.lower()), cols[0])
                ncm_col = next((c for c in cols if "ncm" in c.lower()), cols[1])
                return dict(zip(df[cod_col].str.strip(), df[ncm_col].str.strip()))
            except:
                pass
        # Intentar leer genérico
        df = pd.read_excel(io.BytesIO(ncm_file_bytes), dtype=str)
        cols = df.columns.tolist()
        cod_col = next((c for c in cols if "art" in str(c).lower() or "cod" in str(c).lower()), cols[0])
        ncm_col = next((c for c in cols if "ncm" in str(c).lower()), cols[1])
        return dict(zip(df[cod_col].astype(str).str.strip(), df[ncm_col].astype(str).str.strip()))
    except Exception as e:
        st.warning(f"Error leyendo NCMs: {e}")
        return {}

def leer_marcas_aesa(marcas_file_bytes):
    """Lee el Excel de marcas AESA (solapa Pos, columna MARCA)."""
    try:
        df = pd.read_excel(io.BytesIO(marcas_file_bytes),
                           sheet_name="Pos", dtype=str, skiprows=3)
        df = df[df["Pos"].str.match(r'^\d+$', na=False)].copy()
        col_marca = next((c for c in df.columns if "MARCA" in str(c).upper()), None)
        col_cod = next((c for c in df.columns if "SAP" in str(c).upper() or "Código" in str(c)), None)
        if col_marca and col_cod:
            return dict(zip(df[col_cod].str.strip(), df[col_marca].str.strip()))
    except Exception as e:
        st.warning(f"Error leyendo marcas: {e}")
    return {}

def generar_excel_cme(items, nombre_lote):
    """Genera Excel CME con una sola hoja."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Hoja1"

    headers = ["", "Articulo", "Descripcion", "NCM", "Cantidad", "Unitario",
               "Total", "Origen", "Procedencia", "Unidad de Venta",
               "Marca", "Modelo", "PN", "Marca/Modelo/Otro"]
    ws.append(headers)

    for item in items:
        ws.append([
            "",
            item.get("codigo", ""),
            item.get("descripcion", ""),
            item.get("ncm", "SIN NCM"),
            item.get("cantidad", 0),
            item.get("unitario", 0),
            item.get("total", 0),
            item.get("origen", ""),
            item.get("procedencia", ""),
            item.get("unidad_cod", 7),
            item.get("marca", "sin marca"),
            item.get("codigo", ""),       # Modelo = codigo
            item.get("peso_neto", 0),     # PN = peso neto
            item.get("marca_modelo_otro", ""),
        ])

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf

def generar_excel_sidom(items, nombre_lote):
    """Genera Excel SIDOM con una sola hoja."""
    # Leer template SIDOM
    template_path = os.path.join(os.path.dirname(__file__), "Lote_SIDOM.xlsx")
    wb = openpyxl.load_workbook(template_path)
    ws = wb.active

    # Limpiar filas de datos
    for row in ws.iter_rows(min_row=2, max_row=ws.max_row):
        for cell in row:
            cell.value = None

    for i, item in enumerate(items):
        row = i + 2
        unidad_sidom = UNIDAD_SIDOM.get(item.get("unidad_cod", 7), "07 - UNIDAD")
        ws.cell(row=row, column=1).value  = i + 1
        ws.cell(row=row, column=2).value  = item.get("codigo", "")
        ws.cell(row=row, column=3).value  = item.get("cantidad", 0)
        ws.cell(row=row, column=4).value  = unidad_sidom
        ws.cell(row=row, column=5).value  = item.get("unitario", 0)
        ws.cell(row=row, column=6).value  = item.get("total", 0)
        ws.cell(row=row, column=11).value = item.get("peso_neto", 0)
        ws.cell(row=row, column=14).value = item.get("origen_nombre", "")
        ws.cell(row=row, column=16).value = item.get("estado", "2 - NUEVO SIN USO IMPORTADO")
        ws.cell(row=row, column=17).value = item.get("ncm", "")
        ws.cell(row=row, column=21).value = "N"
        ws.cell(row=row, column=22).value = "N"
        ws.cell(row=row, column=23).value = "N"

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf

# ─── MAPEO INVERSO PAISES ──────────────────────────────────────────────────
PAISES_INV = {}
for nombre, cod in PAISES.items():
    if cod not in PAISES_INV:
        PAISES_INV[cod] = nombre

# ─── INICIO DE LA APP ──────────────────────────────────────────────────────
st.markdown('<div class="titulo-app">📦 CONSTRUCCIÓN DE LOTE</div>', unsafe_allow_html=True)

# Inicializar session state
if "paso" not in st.session_state:
    st.session_state.paso = 1
if "config" not in st.session_state:
    st.session_state.config = {}
if "items" not in st.session_state:
    st.session_state.items = []
if "alertas_marca" not in st.session_state:
    st.session_state.alertas_marca = []

# ══════════════════════════════════════════════════════════════════════════
# PASO 1 — CONFIGURACIÓN INICIAL
# ══════════════════════════════════════════════════════════════════════════
with st.expander("⚙️  CONFIGURACIÓN", expanded=(st.session_state.paso == 1)):
    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<div class="paso-header">01 — Número de Referencia</div>', unsafe_allow_html=True)
        nro_ref = st.text_input("Número de referencia del lote", 
                                 placeholder="Ej: 4508864970",
                                 key="nro_ref")

        st.markdown('<div class="paso-header">02 — Sistema</div>', unsafe_allow_html=True)
        sistema = st.radio("Sistema de despacho", ["CME", "SIDOM"], horizontal=True, key="sistema")

        st.markdown('<div class="paso-header">03 — Cliente</div>', unsafe_allow_html=True)
        if sistema == "CME":
            cliente = st.selectbox("Cliente", ["Natura", "AESA", "Otro"], key="cliente_cme")
        else:
            cliente = st.selectbox("Cliente", ["Genérico", "Otro"], key="cliente_sidom")

    with col2:
        tipo_ref = None
        if sistema == "CME" and cliente == "Natura":
            st.markdown('<div class="paso-header">04 — Tipo de Referencia</div>', unsafe_allow_html=True)
            tipo_ref = st.radio("Tipo de referencia", ["ARG", "Otro"], horizontal=True, key="tipo_ref")

        st.markdown('<div class="paso-header">05 — ¿Ítems Usados?</div>', unsafe_allow_html=True)
        tiene_usados = st.radio("¿Esta operación puede tener ítems usados?",
                                 ["No", "Sí"], horizontal=True, key="tiene_usados")

    if st.button("CONFIRMAR CONFIGURACIÓN →"):
        if not nro_ref:
            st.error("Ingresá el número de referencia")
        else:
            st.session_state.config = {
                "nro_ref": nro_ref,
                "sistema": sistema,
                "cliente": cliente,
                "tipo_ref": tipo_ref,
                "tiene_usados": tiene_usados == "Sí",
            }
            st.session_state.paso = 2
            st.rerun()

# ══════════════════════════════════════════════════════════════════════════
# PASO 2 — SUBIR ARCHIVOS
# ══════════════════════════════════════════════════════════════════════════
if st.session_state.paso >= 2:
    cfg = st.session_state.config
    with st.expander("📁  ARCHIVOS", expanded=(st.session_state.paso == 2)):
        st.markdown(f'<div class="info-box">Sistema: <b>{cfg["sistema"]}</b> | Cliente: <b>{cfg["cliente"]}</b> | Referencia: <b>{cfg["nro_ref"]}</b></div>', unsafe_allow_html=True)

        facturas = st.file_uploader(
            "Facturas PDF (una o más)",
            type=["pdf"],
            accept_multiple_files=True,
            key="facturas"
        )

        ncm_file = st.file_uploader(
            "Excel de NCMs",
            type=["xlsx", "xlsm", "xls"],
            key="ncm_file"
        )

        marcas_file = None
        if cfg["cliente"] == "AESA":
            marcas_file = st.file_uploader(
                "Excel de Marcas (AESA - solapa Pos)",
                type=["xlsx", "xlsm", "xls"],
                key="marcas_file"
            )

        modo_excel = "único"
        if facturas and len(facturas) > 1:
            st.markdown('<div class="paso-header">¿Cómo generar el Excel?</div>', unsafe_allow_html=True)
            modo_excel = st.radio(
                "Modo de generación",
                ["Un Excel por factura", "Un solo Excel con todas"],
                key="modo_excel"
            )
            modo_excel = "por_factura" if "por factura" in modo_excel else "único"

        if facturas and ncm_file:
            if cfg["cliente"] == "AESA" and not marcas_file:
                st.warning("⚠️ Falta el Excel de Marcas para AESA")
            elif st.button("PROCESAR FACTURAS →"):
                st.session_state.paso = 3
                st.session_state.config["modo_excel"] = modo_excel
                st.session_state.facturas_data = [(f.name, f.read()) for f in facturas]
                st.session_state.ncm_data = (ncm_file.name, ncm_file.read())
                st.session_state.marcas_data = (marcas_file.name, marcas_file.read()) if marcas_file else None
                st.rerun()

# ══════════════════════════════════════════════════════════════════════════
# PASO 3 — PROCESAMIENTO
# ══════════════════════════════════════════════════════════════════════════
if st.session_state.paso >= 3:
    cfg = st.session_state.config

    with st.expander("⚙️  PROCESAMIENTO", expanded=(st.session_state.paso == 3)):
        if st.session_state.paso == 3:
            # Leer NCMs
            ncm_nombre, ncm_bytes = st.session_state.ncm_data
            ncm_dict = leer_ncm(ncm_bytes, ncm_nombre)
            st.markdown(f'<div class="ok-box">✅ NCMs cargados: {len(ncm_dict)} registros</div>', unsafe_allow_html=True)

            # Leer marcas AESA
            marcas_dict = {}
            if st.session_state.marcas_data:
                m_nombre, m_bytes = st.session_state.marcas_data
                marcas_dict = leer_marcas_aesa(m_bytes)
                st.markdown(f'<div class="ok-box">✅ Marcas cargadas: {len(marcas_dict)} registros</div>', unsafe_allow_html=True)

            # Procesar cada factura
            todos_items = []
            facturas_items = {}

            for nombre_fac, pdf_bytes in st.session_state.facturas_data:
                tipo_fac, items_raw, texto = extraer_items_pdf(pdf_bytes)

                # Para AESA con PDF escaneado sin texto, extraer del Excel de marcas
                if cfg["cliente"] == "AESA" and len(items_raw) == 0 and st.session_state.marcas_data:
                    m_nombre, m_bytes = st.session_state.marcas_data
                    items_raw = extraer_items_aesa_desde_excel(m_bytes)
                    tipo_fac = "aesa_excel"

                st.markdown(f'<div class="info-box">📄 {nombre_fac} → {len(items_raw)} ítems detectados (tipo: {tipo_fac})</div>', unsafe_allow_html=True)
                if items_raw:
                    with st.expander(f"Ver ítems detectados ({len(items_raw)})"):
                        for it in items_raw:
                            st.write(f"`{it.get('codigo')}` | {str(it.get('descripcion',''))[:50]} | cant: {it.get('cantidad')} | total: {it.get('total')}")

                # Enriquecer ítems
                items_enriquecidos = []
                alertas_marca = []
                alertas_usados = []

                for item in items_raw:
                    cod = item["codigo"]

                    # NCM
                    item["ncm"] = ncm_dict.get(cod, "SIN NCM")

                    # Marca según cliente
                    if cfg["cliente"] == "Natura":
                        if cfg["tipo_ref"] == "ARG":
                            item["marca"] = "sin marca"
                        else:
                            desc = item["descripcion"].lower()
                            if "natura" in desc:
                                item["marca"] = "natura"
                            elif "avon" in desc:
                                item["marca"] = "avon"
                            else:
                                item["marca"] = None
                                alertas_marca.append(item)
                        item["marca_modelo_otro"] = cod

                    elif cfg["cliente"] == "AESA":
                        item["marca"] = marcas_dict.get(cod, "SIN MARCA")
                        if item["marca"] == "SIN MARCA":
                            alertas_marca.append(item)
                        item["marca_modelo_otro"] = ""

                    else:
                        # Genérico
                        item["marca"] = ""
                        item["marca_modelo_otro"] = ""

                    # Estado nuevo/usado
                    item["estado"] = "2 - NUEVO SIN USO IMPORTADO"
                    if cfg["tiene_usados"]:
                        desc_lower = item["descripcion"].lower()
                        if any(p in desc_lower for p in ["used", "usad", "reman", "recondition", "rebuilt", "gebraucht"]):
                            item["estado"] = "4 - USADO IMPORTADO, INCL. REACOND"
                            alertas_usados.append(item)

                    # Nombre del origen para SIDOM
                    item["origen_nombre"] = PAISES_INV.get(item.get("origen"), str(item.get("origen", "")))

                    items_enriquecidos.append(item)

                facturas_items[nombre_fac] = {
                    "items": items_enriquecidos,
                    "alertas_marca": alertas_marca,
                    "alertas_usados": alertas_usados,
                }
                todos_items.extend(items_enriquecidos)

            st.session_state.todos_items = todos_items
            st.session_state.facturas_items = facturas_items
            st.session_state.alertas_marca_global = [
                item for fac in facturas_items.values()
                for item in fac["alertas_marca"]
            ]
            st.session_state.alertas_usados_global = [
                item for fac in facturas_items.values()
                for item in fac["alertas_usados"]
            ]
            st.session_state.paso = 4
            st.rerun()

# ══════════════════════════════════════════════════════════════════════════
# PASO 4 — VALIDACIÓN Y ALERTAS
# ══════════════════════════════════════════════════════════════════════════
if st.session_state.paso >= 4:
    cfg = st.session_state.config
    alertas_marca = st.session_state.get("alertas_marca_global", [])
    alertas_usados = st.session_state.get("alertas_usados_global", [])

    with st.expander("⚠️  VALIDACIÓN", expanded=True):

        hay_alertas = False

        # Alertas de marca
        if alertas_marca:
            hay_alertas = True
            st.markdown(f'<div class="alerta-box">⚠️ {len(alertas_marca)} ítems sin marca detectada — completar antes de generar</div>', unsafe_allow_html=True)
            for item in alertas_marca:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f'`{item["codigo"]}` — {item["descripcion"][:80]}')
                with col2:
                    opciones = ["natura", "avon", "sin marca"] if cfg["cliente"] == "Natura" else ["SIN MARCA"]
                    marca_sel = st.selectbox(
                        "Marca",
                        opciones,
                        key=f"marca_sel_{item['codigo']}_{id(item)}"
                    )
                    item["marca"] = marca_sel
                    if cfg["cliente"] == "Natura":
                        item["marca_modelo_otro"] = item["codigo"]

        # Alertas de usados
        if alertas_usados:
            hay_alertas = True
            st.markdown(f'<div class="alerta-box">⚠️ {len(alertas_usados)} ítems detectados como posiblemente USADOS</div>', unsafe_allow_html=True)
            for item in alertas_usados:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f'`{item["codigo"]}` — {item["descripcion"][:80]}')
                with col2:
                    estado_sel = st.radio(
                        "Estado",
                        ["2 - NUEVO SIN USO IMPORTADO", "4 - USADO IMPORTADO, INCL. REACOND"],
                        key=f"estado_sel_{item['codigo']}_{id(item)}",
                        horizontal=False
                    )
                    item["estado"] = estado_sel

        # Ítems usados adicionales (si el operador quiere marcar más)
        if cfg["tiene_usados"]:
            st.markdown("---")
            st.markdown("**¿Hay algún ítem adicional que sea USADO y no fue detectado?**")
            todos_codigos = [it["codigo"] for it in st.session_state.todos_items]
            usados_extra = st.multiselect(
                "Seleccionar ítems usados adicionales",
                options=todos_codigos,
                key="usados_extra"
            )
            for cod in usados_extra:
                for item in st.session_state.todos_items:
                    if item["codigo"] == cod:
                        item["estado"] = "4 - USADO IMPORTADO, INCL. REACOND"

        if not hay_alertas:
            st.markdown('<div class="ok-box">✅ Sin alertas — todo listo para generar</div>', unsafe_allow_html=True)

        if st.button("GENERAR EXCEL →"):
            st.session_state.paso = 5
            st.rerun()

# ══════════════════════════════════════════════════════════════════════════
# PASO 5 — GENERACIÓN DEL EXCEL
# ══════════════════════════════════════════════════════════════════════════
if st.session_state.paso >= 5:
    cfg = st.session_state.config
    nro_ref = cfg["nro_ref"]
    sistema = cfg["sistema"]
    modo = cfg.get("modo_excel", "único")

    with st.expander("✅  RESULTADO", expanded=True):

        if modo == "por_factura":
            for nombre_fac, fac_data in st.session_state.facturas_items.items():
                items = fac_data["items"]
                nombre_archivo = f"Lote_{nro_ref}.{'xlsx' if sistema == 'SIDOM' else 'xlsx'}"

                if sistema == "CME":
                    buf = generar_excel_cme(items, nro_ref)
                else:
                    buf = generar_excel_sidom(items, nro_ref)

                st.markdown(f'<div class="ok-box">✅ {nombre_fac} → {len(items)} ítems</div>', unsafe_allow_html=True)
                st.download_button(
                    f"⬇️ Descargar {nombre_archivo}",
                    data=buf,
                    file_name=nombre_archivo,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key=f"dl_{nombre_fac}"
                )
        else:
            # Un solo Excel con todos los ítems
            todos = st.session_state.todos_items
            nombre_archivo = f"Lote_{nro_ref}.xlsx"

            if sistema == "CME":
                buf = generar_excel_cme(todos, nro_ref)
            else:
                buf = generar_excel_sidom(todos, nro_ref)

            st.markdown(f'<div class="ok-box">✅ {len(todos)} ítems procesados → {nombre_archivo}</div>', unsafe_allow_html=True)
            st.download_button(
                f"⬇️ Descargar {nombre_archivo}",
                data=buf,
                file_name=nombre_archivo,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="dl_unico"
            )

        if st.button("🔄 Nuevo Lote"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
