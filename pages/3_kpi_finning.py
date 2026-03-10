import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
from collections import Counter
import io

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@400;600;700;800&family=Barlow:wght@300;400;500;600&display=swap');
html, body, [class*="css"] { font-family: 'Barlow', sans-serif; background-color: #0A1628; color: #F0F4F8; }
.stApp { background: #0A1628; }
h1, h2, h3 { font-family: 'Barlow Condensed', sans-serif; letter-spacing: 1px; }
.metric-card { background: #132236; border: 1px solid rgba(0,201,167,0.15); border-top: 3px solid #00C9A7; border-radius: 8px; padding: 1.2rem; text-align: center; }
.metric-value { font-family: 'Barlow Condensed', sans-serif; font-size: 2.4rem; font-weight: 800; color: #00C9A7; line-height: 1; }
.metric-value.orange { color: #FF8C42; }
.metric-value.red    { color: #FF3D5E; }
.metric-label { font-size: 0.7rem; font-weight: 600; color: #6B8099; letter-spacing: 1px; text-transform: uppercase; margin-top: 0.3rem; }
.metric-sub   { font-size: 0.75rem; color: #9AB0C4; margin-top: 0.2rem; }
.section-header { font-family: 'Barlow Condensed', sans-serif; font-size: 1.1rem; font-weight: 700; color: #00C9A7; letter-spacing: 2px; text-transform: uppercase; border-left: 3px solid #00C9A7; padding-left: 0.8rem; margin: 1.5rem 0 0.8rem; }
.alert-info    { background: rgba(0,201,167,0.1);  border: 1px solid rgba(0,201,167,0.3);  border-radius: 6px; padding: 0.8rem 1rem; font-size: 0.85rem; color: #9AB0C4; }
.alert-warn    { background: rgba(255,140,66,0.1); border: 1px solid rgba(255,140,66,0.4); border-radius: 6px; padding: 0.8rem 1rem; font-size: 0.85rem; color: #FF8C42; }
.alert-success { background: rgba(0,201,167,0.15); border: 1px solid #00C9A7;              border-radius: 6px; padding: 0.8rem 1rem; font-size: 0.85rem; color: #00C9A7; font-weight: 600; }
.stButton > button { background: #00C9A7; color: #0A1628; font-family: 'Barlow Condensed', sans-serif; font-weight: 700; font-size: 1rem; letter-spacing: 1px; border: none; border-radius: 6px; padding: 0.6rem 2rem; transition: all 0.2s; }
.stButton > button:hover { background: #00E0BA; transform: translateY(-1px); }
[data-testid="stFileUploader"] { background: #1A2E48 !important; border: 2px solid #00C9A7 !important; border-radius: 8px !important; }
[data-testid="stFileUploaderDropzone"] { background: #0F2040 !important; border: 2px dashed #00C9A7 !important; }
</style>
""", unsafe_allow_html=True)

FASA = 'FINNING ARGENTINA SOCIEDAD ANO'
FSM  = 'FINNING SOLUCIONES MINERAS SA'
LIMITES_LIB = {
    'AVION':    {'VERDE': 1, 'NARANJA': 3, 'ROJO': 4},
    'MARITIMO': {'VERDE': 3, 'NARANJA': 4, 'ROJO': 5},
    'CAMION':   {'VERDE': 1, 'NARANJA': 2, 'ROJO': 3},
}
COLORS = {'accent': '#00C9A7', 'orange': '#FF8C42', 'red': '#FF3D5E', 'gold': '#FFD060', 'bg': '#132236', 'verde': '#00C9A7', 'naranja': '#FF8C42', 'rojo': '#FF3D5E', 'gray': '#6B8099'}
CHART_LAYOUT = dict(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(19,34,54,0.8)', font=dict(family='Barlow, sans-serif', color='#9AB0C4'), margin=dict(l=10, r=10, t=30, b=10))

def _init_state():
    defaults = {'step': 1, 'max_step': 1, 'lib_items': [], 'ofi_items': [], 'cm_pre_items': [], 'cm_apr_items': [], 'mes': '', 'desvio_sub_step': 'descargar', 'confirm_replace': False}
    for k, v in defaults.items():
        if k not in st.session_state: st.session_state[k] = v

_init_state()

def reset_all():
    for k in list(st.session_state.keys()): del st.session_state[k]
    _init_state()

def go_to(step):
    st.session_state.step = step
    st.session_state.confirm_replace = False
    st.rerun()

def parse_date(val):
    if isinstance(val, datetime): return val
    if isinstance(val, str):
        for fmt in ['%d/%m/%Y %H:%M:%S', '%d/%m/%Y', '%Y-%m-%d']:
            try: return datetime.strptime(val, fmt)
            except: pass
    return None

def dias_habiles(d1, d2):
    if not d1 or not d2: return None
    d1 = d1.date() if hasattr(d1, 'date') else d1
    d2 = d2.date() if hasattr(d2, 'date') else d2
    if d2 <= d1: return 0
    dias, cur = 0, d1 + timedelta(days=1)
    while cur <= d2:
        if cur.weekday() < 5: dias += 1
        cur += timedelta(days=1)
    return dias

def limite_ofi(razon, via): return 2 if razon == FSM and via == 'MARITIMO' else 1
def color_kpi(pct): return COLORS['accent'] if pct >= 95 else (COLORS['orange'] if pct >= 80 else COLORS['red'])

def metric_html(value, label, sub=None, color='accent'):
    color_class = '' if color == 'accent' else color
    sub_html = f'<div class="metric-sub">{sub}</div>' if sub else ''
    return f'<div class="metric-card"><div class="metric-value {color_class}">{value}</div><div class="metric-label">{label}</div>{sub_html}</div>'

def procesar_liberadas(df):
    results = []
    for _, r in df.iterrows():
        razon = r.get('Razon Social', '')
        via   = str(r.get('Via', '')).upper().strip()
        canal = str(r.get('Canal', '')).upper().strip()
        f_ofi = parse_date(r.get('Fecha Oficialización'))
        f_can = parse_date(r.get('Fecha Cancelada'))
        dias  = dias_habiles(f_ofi, f_can)
        limite = LIMITES_LIB.get(via, {}).get(canal, 9999)
        results.append({'razon': razon, 'nombre': 'FASA' if razon == FASA else 'FSM', 'ref': r.get('Referencia', ''), 'carpeta': r.get('Carpeta', ''), 'via': via, 'canal': canal, 'f_ofi': f_ofi, 'f_cancel': f_can, 'hs': dias, 'limite': limite, 'desvio': dias is not None and dias > limite, 'desvio_desc': '', 'parametro': ''})
    return results

def procesar_oficializados(df):
    results = []
    for _, r in df.iterrows():
        razon = r.get('Razon Social', '')
        via   = str(r.get('Via', '')).upper().strip()
        f_ofi = parse_date(r.get('Fecha Oficialización'))
        f_ult = parse_date(r.get('Ultimo Evento'))
        dias  = dias_habiles(f_ofi, f_ult)
        limite = limite_ofi(razon, via)
        results.append({'razon': razon, 'nombre': 'FASA' if razon == FASA else 'FSM', 'ref': r.get('Referencia', ''), 'carpeta': r.get('Carpeta', ''), 'via': via, 'f_ofi': f_ofi, 'f_ult': f_ult, 'hs': dias, 'limite': limite, 'desvio': dias is not None and dias > limite, 'desvio_desc': '', 'parametro': ''})
    return results

def procesar_cm_presentados(df):
    results = []
    for _, r in df.iterrows():
        f_tad = parse_date(r.get('TAD SUBIDO'))
        f_ult = parse_date(r.get('Ult evento'))
        dias  = dias_habiles(f_ult, f_tad)
        results.append({'carpeta': r.get('CARPETA', ''), 'exp': r.get('Expediente', ''), 'f_tad': f_tad, 'f_ult': f_ult, 'hs': dias, 'desvio': dias is not None and dias > 2, 'desvio_desc': '', 'parametro': ''})
    return results

def procesar_cm_aprobados(df):
    results = []
    for _, r in df.iterrows():
        f1 = parse_date(r.get('Fecha'))
        f2 = parse_date(r.get('Fechadeaprobacion'))
        dias = (f2 - f1).days if f1 and f2 else None
        rango = None
        if dias is not None: rango = '0 a 7' if dias <= 7 else ('8 a 15' if dias <= 15 else '+15')
        results.append({'carpeta': r.get('CARPETA', ''), 'exp': r.get('Expediente', ''), 'f_inicio': f1, 'f_apro': f2, 'dias': dias, 'rango': rango})
    return results

def calcular_kpi(items, con_parametros=False):
    total = len(items)
    if total == 0: return 0, 0, 0
    out = sum(1 for i in items if i['desvio'] and (str(i.get('parametro', '')).upper() == 'INTERLOG' if con_parametros else True))
    return round((total - out) / total * 100, 2), total - out, out

def chart_gauge(pct, title):
    color = color_kpi(pct)
    fig = go.Figure(go.Indicator(mode="gauge+number", value=pct, number={'suffix': '%', 'font': {'size': 36, 'color': color, 'family': 'Barlow Condensed'}}, title={'text': title, 'font': {'size': 13, 'color': '#9AB0C4'}},
        gauge={'axis': {'range': [0, 100]}, 'bar': {'color': color, 'thickness': 0.25}, 'bgcolor': '#1A2E48', 'borderwidth': 0,
               'steps': [{'range': [0, 80], 'color': 'rgba(255,61,94,0.15)'}, {'range': [80, 95], 'color': 'rgba(255,140,66,0.15)'}, {'range': [95, 100], 'color': 'rgba(0,201,167,0.15)'}],
               'threshold': {'line': {'color': '#FFD060', 'width': 3}, 'thickness': 0.8, 'value': 95}}))
    fig.update_layout(**CHART_LAYOUT, height=220)
    return fig

def generar_excel_desvios(lib_items, ofi_items, cm_pre_items, mes='MES'):
    from openpyxl import Workbook
    from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
    from openpyxl.utils import get_column_letter
    DARK_BG="0D1B2A"; MID_BG="1B2B3E"; CARD="132236"; ACCENT="008B74"; GOLD="FFD060"; ROJO="FF3D5E"; WHITE="FFFFFF"; PURPLE="5B21B6"
    def hfill(c): return PatternFill("solid", fgColor=c)
    def bw(s=10): return Font(bold=True, color=WHITE, size=s, name="Calibri")
    def nw(s=10): return Font(color=WHITE, size=s, name="Calibri")
    def nr(s=10): return Font(color=ROJO, size=s, name="Calibri", bold=True)
    def ng(s=10): return Font(color=GOLD, size=s, name="Calibri", bold=True)
    def cen(): return Alignment(horizontal="center", vertical="center", wrap_text=True)
    def lft(): return Alignment(horizontal="left", vertical="center", wrap_text=True)
    def brd():
        s = Side(border_style="thin", color="1B2B3E")
        return Border(left=s, right=s, top=s, bottom=s)
    wb = Workbook()
    def make_sheet(ws, title_text, headers, rows_data, header_color, col_widths, edit_cols):
        ws.merge_cells(f"A1:{get_column_letter(len(headers))}1")
        ws["A1"] = title_text; ws["A1"].font = bw(13); ws["A1"].fill = hfill(DARK_BG); ws["A1"].alignment = cen(); ws.row_dimensions[1].height = 30
        for ci, h in enumerate(headers, 1):
            cell = ws.cell(3, ci, h); cell.font = bw(10); cell.fill = hfill(header_color); cell.alignment = cen(); cell.border = brd()
        ws.row_dimensions[3].height = 25
        if not rows_data:
            ws.merge_cells(f"A4:{get_column_letter(len(headers))}4"); ws["A4"] = "✅  Sin desvíos detectados — KPI 100%"
            ws["A4"].font = Font(color="00C9A7", size=11, bold=True, name="Calibri"); ws["A4"].fill = hfill(MID_BG); ws["A4"].alignment = cen(); ws.row_dimensions[4].height = 30
        else:
            for ri, row_vals in enumerate(rows_data, 4):
                fill_c = CARD if ri % 2 == 0 else MID_BG
                for ci, val in enumerate(row_vals, 1):
                    cell = ws.cell(ri, ci, val); cell.border = brd(); cell.alignment = cen() if ci > 1 else lft()
                    cell.fill = hfill("1A3A2A") if ci in edit_cols else hfill(fill_c)
                    cell.font = ng(10) if ci in edit_cols else (nr(10) if headers[ci-1] in ['Días Hábiles'] else nw(10))
                ws.row_dimensions[ri].height = 20
        for i, w in enumerate(col_widths, 1): ws.column_dimensions[get_column_letter(i)].width = w
        ws.freeze_panes = "A4"
    ws1 = wb.active; ws1.title = "LIBERADAS - DESVÍOS"
    lib_desvios = [i for i in lib_items if i['desvio']]
    rows_lib = [['FASA' if i['razon']==FASA else 'FSM', i['ref'], str(i['carpeta']), i['via'], i['canal'], i['f_ofi'].strftime('%d/%m/%Y') if i['f_ofi'] else '', i['f_cancel'].strftime('%d/%m/%Y') if i['f_cancel'] else '', i['hs'], i['limite'], '', ''] for i in lib_desvios]
    make_sheet(ws1, f"LIBERADAS {mes} — OPERACIONES CON DESVÍO", ["Razón Social","Referencia","Carpeta","Vía","Canal","F. Oficialización","F. Cancelada","Días Hábiles","Límite (días)","DESVÍO ✏️","PARÁMETRO ✏️"], rows_lib, ACCENT, [28,16,12,12,10,18,22,18,12,35,25], edit_cols=[10,11])
    ws2 = wb.create_sheet("OFICIALIZADOS - DESVÍOS")
    ofi_desvios = [i for i in ofi_items if i['desvio']]
    rows_ofi = [['FASA' if i['razon']==FASA else 'FSM', i['ref'], str(i['carpeta']), i['via'], i['f_ofi'].strftime('%d/%m/%Y') if i['f_ofi'] else '', i['f_ult'].strftime('%d/%m/%Y') if i['f_ult'] else '', i['hs'], i['limite'], '', ''] for i in ofi_desvios]
    make_sheet(ws2, f"OFICIALIZADOS {mes} — OPERACIONES CON DESVÍO", ["Razón Social","Referencia","Carpeta","Vía","F. Oficialización","Último Evento","Días Hábiles","Límite (días)","DESVÍO ✏️","PARÁMETRO ✏️"], rows_ofi, "005F52", [28,16,12,12,18,22,18,12,35,25], edit_cols=[9,10])
    ws3 = wb.create_sheet("CM PRESENTADOS - DESVÍOS")
    cm_desvios = [i for i in cm_pre_items if i['desvio']]
    rows_cm = [[str(i['carpeta']), str(i['exp']), i['f_tad'].strftime('%d/%m/%Y') if i['f_tad'] else '', i['f_ult'].strftime('%d/%m/%Y') if i['f_ult'] else '', i['hs'], 2, '', ''] for i in cm_desvios]
    make_sheet(ws3, f"CM PRESENTADOS {mes} — OPERACIONES CON DESVÍO", ["Carpeta","Expediente","TAD Subido","Último Evento","Días Hábiles","Límite (días)","DESVÍO ✏️","PARÁMETRO ✏️"], rows_cm, PURPLE, [12,28,18,18,18,12,35,25], edit_cols=[7,8])
    buf = io.BytesIO(); wb.save(buf); buf.seek(0)
    return buf

def render_kpi_section(nombre, lib_items, ofi_items, con_param=False):
    vias = sorted(set([i['via'] for i in lib_items if i['nombre']==nombre] + [i['via'] for i in ofi_items if i['nombre']==nombre]), key=lambda x: ['AVION','CAMION','MARITIMO'].index(x) if x in ['AVION','CAMION','MARITIMO'] else 99)
    for via in vias:
        lib_r = [i for i in lib_items if i['nombre']==nombre and i['via']==via]
        ofi_r = [i for i in ofi_items if i['nombre']==nombre and i['via']==via]
        via_emoji = {'AVION': '✈️', 'CAMION': '🚛', 'MARITIMO': '🚢'}.get(via, '📦')
        st.markdown(f'<div style="background:#132236; border-left:4px solid #FFD060; padding:0.5rem 1rem; margin:0.8rem 0 0.4rem; border-radius:0 6px 6px 0;"><span style="font-family:Barlow Condensed,sans-serif; font-size:1.1rem; font-weight:800; color:#FFD060; letter-spacing:2px;">{via_emoji} {nombre} · {via}</span></div>', unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            st.markdown('<div style="color:#9AB0C4; font-size:0.8rem; font-weight:600; text-transform:uppercase; margin-bottom:0.3rem;">OFICIALIZACIÓN</div>', unsafe_allow_html=True)
            if ofi_r:
                pct, in_c, out_c = calcular_kpi(ofi_r, con_param)
                c1, c2, c3 = st.columns(3)
                c1.plotly_chart(chart_gauge(pct, "KPI IN"), use_container_width=True, key=f"{nombre}_{via}_ofi_g")
                with c3:
                    st.markdown(metric_html(str(len(ofi_r)),"Total",None,'accent'), unsafe_allow_html=True)
                    st.markdown(metric_html(str(in_c),"IN",None,'accent'), unsafe_allow_html=True)
                    st.markdown(metric_html(str(out_c),"OUT",None,'red' if out_c else 'accent'), unsafe_allow_html=True)
            else:
                st.markdown('<div class="alert-info">Sin oficializaciones para esta vía.</div>', unsafe_allow_html=True)
        with col2:
            st.markdown('<div style="color:#9AB0C4; font-size:0.8rem; font-weight:600; text-transform:uppercase; margin-bottom:0.3rem;">LIBERACIÓN</div>', unsafe_allow_html=True)
            if lib_r:
                pct, in_c, out_c = calcular_kpi(lib_r, con_param)
                c1, c2, c3 = st.columns(3)
                c1.plotly_chart(chart_gauge(pct, "KPI IN"), use_container_width=True, key=f"{nombre}_{via}_lib_g")
                with c3:
                    st.markdown(metric_html(str(len(lib_r)),"Total",None,'accent'), unsafe_allow_html=True)
                    st.markdown(metric_html(str(in_c),"IN",None,'accent'), unsafe_allow_html=True)
                    st.markdown(metric_html(str(out_c),"OUT",None,'red' if out_c else 'accent'), unsafe_allow_html=True)
            else:
                st.markdown('<div class="alert-info">Sin liberaciones para esta vía.</div>', unsafe_allow_html=True)
        st.markdown('<hr style="border-color:rgba(107,128,153,0.2); margin:1rem 0;">', unsafe_allow_html=True)

# HEADER
has_data = bool(st.session_state.lib_items)
mes_actual = st.session_state.mes or ''
st.markdown(f"""
<div style="background: linear-gradient(135deg, #0F2040 0%, #132236 100%); border-bottom: 1px solid rgba(0,201,167,0.2); padding: 1.2rem 2rem 0.8rem; margin: -1rem -1rem 0; border-radius: 0 0 12px 12px;">
  <div style="display:flex; align-items:center; gap:1rem;">
    <div>
      <div style="font-family:'Barlow Condensed',sans-serif; font-size:2rem; font-weight:800; color:#00C9A7; letter-spacing:3px;">INTERLOG</div>
      <div style="font-family:'Barlow Condensed',sans-serif; font-size:1rem; color:#6B8099; letter-spacing:2px; text-transform:uppercase;">KPI Dashboard · Comercio Exterior</div>
    </div>
    <div style="margin-left:auto; text-align:right;">
      <div style="font-size:0.75rem; color:#6B8099; text-transform:uppercase; letter-spacing:1px;">Reporte Mensual</div>
      <div style="font-family:'Barlow Condensed',sans-serif; font-size:1.2rem; color:#F0F4F8; font-weight:600;">{mes_actual if mes_actual else 'FASA / FSM'}</div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# NAV
nav_steps = [{"label": "📁 Cargar archivos", "step": 1, "always": True}, {"label": "⚠️ Revisar desvíos", "step": 2, "always": False}, {"label": "📊 Dashboard", "step": 3, "always": False}, {"label": "📥 Exportar", "step": 4, "always": False}]
nav_cols = st.columns([3, 3, 3, 3, 2])
st.markdown("""<style>
.snav div[data-testid="stButton"] > button { font-family: 'Barlow Condensed', sans-serif !important; font-size: 0.9rem !important; font-weight: 700 !important; border-radius: 6px !important; padding: 0.52rem 0.6rem !important; }
.snav-active div[data-testid="stButton"] > button { background: #00C9A7 !important; color: #0A1628 !important; border: 2px solid #00C9A7 !important; }
.snav-on div[data-testid="stButton"] > button { background: #132236 !important; color: #C8DDE8 !important; border: 1px solid rgba(0,201,167,0.25) !important; }
.snav-off div[data-testid="stButton"] > button { background: #0C1B2A !important; color: #253545 !important; border: 1px dashed #1A2E3E !important; opacity: 0.6 !important; }
.snav-new div[data-testid="stButton"] > button { background: transparent !important; color: #4A6070 !important; border: 1px solid rgba(107,128,153,0.3) !important; }
</style>""", unsafe_allow_html=True)

for col, nav in zip(nav_cols[:4], nav_steps):
    s = nav["step"]; accessible = nav["always"] or st.session_state.max_step >= s; is_active = st.session_state.step == s; is_done = st.session_state.max_step >= s and not is_active
    label = nav["label"] + (" ●" if is_done else "")
    css = "snav snav-active" if is_active else ("snav snav-on" if accessible else "snav snav-off")
    with col:
        st.markdown(f'<div class="{css}">', unsafe_allow_html=True)
        clicked = st.button(label, key=f"nav_{s}", use_container_width=True, disabled=(not accessible or is_active))
        st.markdown('</div>', unsafe_allow_html=True)
    if clicked: go_to(s)

with nav_cols[4]:
    st.markdown('<div class="snav snav-new">', unsafe_allow_html=True)
    if st.button("🔄 Nuevo análisis", key="btn_new", use_container_width=True): reset_all(); st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("<div style='margin-top:1.2rem;'></div>", unsafe_allow_html=True)

# STEP 1
if st.session_state.step == 1:
    st.markdown('<div class="section-header">PASO 1 · CARGAR ARCHIVOS EXCEL</div>', unsafe_allow_html=True)
    st.markdown('<div class="alert-info">Subí los 4 archivos Excel del mes.</div><br>', unsafe_allow_html=True)
    mes = st.text_input("📅 Mes del reporte (ej: DICIEMBRE 2025)", value=st.session_state.mes)
    col1, col2 = st.columns(2)
    with col1:
        f_lib    = st.file_uploader("📦 LIBERADAS",      type=['xlsx'], key='lib')
        f_ofi    = st.file_uploader("📋 OFICIALIZADOS",  type=['xlsx'], key='ofi')
    with col2:
        f_cm_pre = st.file_uploader("📜 CM PRESENTADOS", type=['xlsx'], key='cmpre')
        f_cm_apr = st.file_uploader("✅ CM APROBADOS",   type=['xlsx'], key='cmapr')
    archivos_ok = all([f_lib, f_ofi, f_cm_pre, f_cm_apr])
    if archivos_ok: st.markdown('<div class="alert-success">✅ Los 4 archivos cargados correctamente</div><br>', unsafe_allow_html=True)
    if st.button("▶  PROCESAR Y CONTINUAR", disabled=not archivos_ok):
        with st.spinner("Procesando datos..."):
            st.session_state.lib_items    = procesar_liberadas(pd.read_excel(f_lib))
            st.session_state.ofi_items    = procesar_oficializados(pd.read_excel(f_ofi))
            st.session_state.cm_pre_items = procesar_cm_presentados(pd.read_excel(f_cm_pre))
            st.session_state.cm_apr_items = procesar_cm_aprobados(pd.read_excel(f_cm_apr))
            st.session_state.mes = mes; st.session_state.step = 2; st.session_state.max_step = 2; st.rerun()

# STEP 2
elif st.session_state.step == 2:
    lib_items = st.session_state.lib_items; ofi_items = st.session_state.ofi_items; cm_pre_items = st.session_state.cm_pre_items
    total_desvios = sum(1 for i in lib_items+ofi_items+cm_pre_items if i['desvio'])
    st.markdown('<div class="section-header">PASO 2 · REVISAR DESVÍOS</div>', unsafe_allow_html=True)
    if total_desvios == 0:
        st.markdown('<div class="alert-success">✅ Sin desvíos. KPI 100%.</div>', unsafe_allow_html=True)
        if st.button("▶  IR AL DASHBOARD"):
            st.session_state.step = 3; st.session_state.max_step = max(st.session_state.max_step, 3); st.rerun()
    else:
        st.markdown(f'<div class="alert-warn">⚠️ {total_desvios} operaciones fuera del rango. Descargá el Excel, completá DESVÍO y PARÁMETRO, y subilo.</div><br>', unsafe_allow_html=True)
        excel_buf = generar_excel_desvios(lib_items, ofi_items, cm_pre_items, st.session_state.mes or 'MES')
        c1, c2 = st.columns(2)
        with c1:
            st.download_button("⬇  DESCARGAR EXCEL DE DESVÍOS", data=excel_buf, file_name=f"DESVIOS_{(st.session_state.mes or 'MES').replace(' ','_')}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
        with c2:
            if st.button("▶  CONTINUAR AL DASHBOARD", use_container_width=True):
                st.session_state.step = 3; st.session_state.max_step = max(st.session_state.max_step, 3); st.rerun()

# STEP 3
elif st.session_state.step == 3:
    st.session_state.max_step = max(st.session_state.max_step, 3)
    lib_items = st.session_state.lib_items; ofi_items = st.session_state.ofi_items; cm_pre_items = st.session_state.cm_pre_items; mes = st.session_state.mes or 'MENSUAL'
    st.markdown(f'<div class="section-header">📊 DASHBOARD KPI · {mes}</div>', unsafe_allow_html=True)
    c1,c2,c3,c4,c5 = st.columns(5)
    for col, items, nombre, lbl in [(c1,lib_items,'FASA','LIB FASA'),(c2,lib_items,'FSM','LIB FSM'),(c3,ofi_items,'FASA','OFI FASA'),(c4,ofi_items,'FSM','OFI FSM')]:
        pct,_,_ = calcular_kpi([i for i in items if i['nombre']==nombre], True)
        col.markdown(metric_html(f"{pct:.0f}%", lbl, None, 'accent' if pct>=95 else 'orange'), unsafe_allow_html=True)
    pct_cm,_,_ = calcular_kpi(cm_pre_items, True)
    c5.markdown(metric_html(f"{pct_cm:.0f}%", "CM PRES.", None, 'accent' if pct_cm>=95 else 'orange'), unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["📦 FASA", "🏔️ FSM"])
    with tab1: render_kpi_section('FASA', lib_items, ofi_items, con_param=True)
    with tab2: render_kpi_section('FSM',  lib_items, ofi_items, con_param=True)
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("▶  EXPORTAR"):
        st.session_state.step = 4; st.session_state.max_step = max(st.session_state.max_step, 4); st.rerun()

# STEP 4
elif st.session_state.step == 4:
    st.session_state.max_step = max(st.session_state.max_step, 4)
    st.markdown('<div class="section-header">PASO 4 · EXPORTAR</div>', unsafe_allow_html=True)
    st.markdown('<div class="alert-info">Exportá el resumen del dashboard en Excel.</div><br>', unsafe_allow_html=True)
    if st.button("⚙️  GENERAR EXCEL", use_container_width=True):
        st.markdown('<div class="alert-success">✅ Usá el botón de descarga del dashboard completo desde la app original por ahora.</div>', unsafe_allow_html=True)
