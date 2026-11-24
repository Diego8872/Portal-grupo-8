"""Interfaz Streamlit. La usan app.py (standalone) y la página del portal."""
import os
import re

import pandas as pd
import streamlit as st

from .compare import ERROR, OK
from .config import TIPOS
from .excel import generar_excel, texto_resultado
from .llm import get_proveedor
from .pipeline import validar

_ICONO = {OK: "✅", ERROR: "❌", "revisar": "⚠️"}
# (clave, etiqueta, extensiones, obligatorio, varios archivos)
_CAMPOS = [("pd", "PD (PDF)", ["pdf"], True, False),
           ("listado", "Listado de importación (Excel)", ["xlsx", "xlsm"], True, False),
           ("factura", "Factura (PDF o Excel)", ["pdf", "xlsx", "xlsm"], False, False),
           ("transporte", "BL / Guía aérea / CRT (PDF o Excel)", ["pdf", "xlsx", "xlsm"], False, False),
           ("coa", "COA (PDF o Excel; uno por lote)", ["pdf", "xlsx", "xlsm"], False, True),
           ("packing", "Packing list / Delivery note (PDF o Excel)", ["pdf", "xlsx", "xlsm"], False, False)]


def _api_key() -> str:
    try:
        return st.secrets["GROQ_API_KEY"]
    except Exception:
        return os.environ.get("GROQ_API_KEY", "")


def _secret(nombre: str) -> str:
    try:
        return str(st.secrets.get(nombre, "") or "")
    except Exception:
        return os.environ.get(nombre, "")


def _proveedor():
    return get_proveedor("groq", _api_key(), modelo_texto=_secret("GROQ_MODEL_TEXT"),
                         modelo_vision=_secret("GROQ_MODEL_VISION"))


def _diagnostico():
    """Muestra qué modelos tiene disponibles la cuenta de Groq y prueba una llamada mínima."""
    with st.sidebar.expander("🔧 Diagnóstico de IA"):
        if st.button("Probar conexión con Groq"):
            try:
                p = _proveedor()
                disp = p.disponibles()
                st.write("Modelos disponibles:", ", ".join(disp) if disp else "no se pudo listar")
                st.write("Texto → se usaría:", p.candidatos(False)[0], "| Visión →", p.candidatos(True)[0])
                r = p.extraer_json('Devolvé {"ok": true}', "prueba")
                st.success(f"Respuesta OK de {p.ultimo_modelo}: {r}")
            except Exception as e:
                st.error(str(e))


def render():
    st.title("🧾 Corrector INAL – Coca-Cola")
    st.caption("Controla el PD de INAL contra factura, BL/guía/CRT, COA, packing list y listado de importación.")

    n = st.session_state.setdefault("inal_n", 0)   # cambia con "Nuevo análisis" y reinicia todos los campos

    def _nuevo():
        st.session_state["inal_n"] += 1
        st.session_state.pop("inal_res", None)
        st.session_state.pop("inal_detenido", None)

    st.button("🔄 Nuevo análisis", on_click=_nuevo, help="Borra los archivos, la referencia y el resultado")
    tipo = st.radio("Tipo de control", list(TIPOS), horizontal=True, index=None, key=f"inal_tipo_{n}",
                    format_func=lambda k: TIPOS[k].nombre)
    referencia = st.text_input("Número de referencia (será el nombre del Excel)", key=f"inal_ref_{n}",
                               placeholder="Ej.: 25001234")
    archivos = {}
    c1, c2 = st.columns(2)
    for i, (clave, etiqueta, ext, _, varios) in enumerate(_CAMPOS):
        with (c1 if i % 2 == 0 else c2):
            archivos[clave] = st.file_uploader(etiqueta, type=ext, key=f"inal_{clave}_{n}", accept_multiple_files=varios)

    _diagnostico()
    if not _api_key():
        st.error("Falta GROQ_API_KEY en los Secrets de Streamlit.")
    faltan_obl = [e for (c, e, _, obl, _) in _CAMPOS if obl and not archivos[c]]
    faltan_opc = [e for (c, e, _, obl, _) in _CAMPOS if not obl and not archivos[c]]
    if faltan_obl:
        st.info("Falta subir (obligatorio): " + ", ".join(faltan_obl))
    elif faltan_opc:
        st.warning("No subiste: " + ", ".join(faltan_opc) + ". Los campos que dependen de esos documentos quedarán como ⚠️.")

    if tipo is None:
        st.info("Elegí el tipo de control (345, Autorización o Aviso).")
    b1, b2, _ = st.columns([1, 1, 4])
    validar_click = b1.button("Validar", type="primary", disabled=bool(faltan_obl) or tipo is None or not _api_key())
    detener_click = b2.button("⏹ Detener", help="Frena el control en curso")
    if detener_click:
        st.session_state.pop("inal_res", None)
        st.warning("Validación detenida. Podés corregir los datos y volver a validar.")
    if validar_click:
        datos = {}
        for c, f in archivos.items():
            if isinstance(f, list):
                datos[c] = [x.getvalue() for x in f]
            elif f is not None:
                datos[c] = f.getvalue()
        try:
            proveedor = _proveedor()
            with st.status("Controlando…", expanded=False) as estado:
                res = validar(tipo, datos, proveedor, progreso=lambda msg: estado.update(label=msg))
                estado.update(label="Listo", state="complete")
            res["referencia"] = referencia.strip()
            st.session_state["inal_res"] = res
        except Exception as e:
            st.session_state.pop("inal_res", None)
            st.error(f"No se pudo completar el control: {e}")

    res = st.session_state.get("inal_res")
    if not res:
        return
    filas = res["filas"]
    ok, err, rev = (sum(1 for f in filas if f.estado == e) for e in (OK, ERROR, "revisar"))
    st.subheader(f"{res['tipo']} · {res['pd_numero'] or 'PD'}")
    m1, m2, m3 = st.columns(3)
    m1.metric("✅ Coinciden", ok)
    m2.metric("❌ No coinciden", err)
    m3.metric("⚠️ A revisar", rev)
    for a in res["avisos"]:
        st.warning(a)
    st.dataframe(pd.DataFrame([{"": _ICONO[f.estado], "Campo": f.campo, "PD": f.pd or "—",
                                "Documento fuente": f.fuente or "—", "Resultado": texto_resultado(f)}
                               for f in filas]), hide_index=True, use_container_width=True)
    ref = re.sub(r'[\\/:*?"<>|#\s]+', "_", res.get("referencia", "")).strip("._ ")
    nombre = (res["pd_numero"] or "PD").replace("#", "-")
    archivo = f"{ref}.xlsx" if ref else f"Control_{res['tipo'].replace(' ', '_')}_{nombre}.xlsx"
    st.download_button("⬇️ Descargar Excel", generar_excel(res), file_name=archivo,
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    with st.expander("Datos leídos de cada documento (para revisar)"):
        st.caption("Lectura: " + " · ".join(f"{k}: {v}" for k, v in res["lecturas"].items()))
        st.json({k: {a: b for a, b in v.items() if not a.startswith("_") or a == "_error"} for k, v in res["docs"].items()})
