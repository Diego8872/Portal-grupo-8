import tempfile
import os

import streamlit as st

from utils_senasa.parser_dj_senasa import extract_dj_senasa
from utils_senasa.parser_di_excel import extract_di_excel
from utils_senasa.parser_di_pdf import extract_di_pdf
from utils_senasa.validator import validate, merge_di_sources
from utils_senasa.report_pdf import build_report_pdf

# NOTA: no se llama st.set_page_config acá — ya lo define el portal
# una única vez en su archivo principal.

# --- Estado (prefijado p19_ para no chocar con las demás páginas del portal) ---
if "p19_resultado" not in st.session_state:
    st.session_state.p19_resultado = None
    st.session_state.p19_dj_data = None
    st.session_state.p19_di_data = None
if "p19_uploader_key" not in st.session_state:
    st.session_state.p19_uploader_key = 0
if "p19_referencia_input" not in st.session_state:
    st.session_state.p19_referencia_input = ""


def nuevo_analisis():
    st.session_state.p19_resultado = None
    st.session_state.p19_dj_data = None
    st.session_state.p19_di_data = None
    st.session_state.p19_referencia_input = ""
    st.session_state.p19_uploader_key += 1  # fuerza a recrear los file_uploader vacíos


st.title("Corrector SENASA")
st.caption(
    "Cruza la Declaración Jurada de SENASA (embalajes de madera) contra la DI. "
    "Aduanas soportadas en esta v1: **Ezeiza** y **Buenos Aires**."
)

if st.session_state.p19_resultado is None:
    st.markdown("### 1. Referencia del despacho")
    st.text_input(
        "Referencia (para identificar el reporte)",
        key="p19_referencia_input",
        placeholder="Ej: 999792 - D-7418",
    )

    st.markdown("### 2. Subí la Declaración Jurada de SENASA (PDF)")
    dj_file = st.file_uploader(
        "DJ SENASA (PDF)", type=["pdf"], key=f"p19_dj_{st.session_state.p19_uploader_key}"
    )

    st.markdown("### 3. Subí la DI")
    col1, col2 = st.columns(2)
    with col1:
        di_excel_file = st.file_uploader(
            "DI (Excel) — recomendado",
            type=["xlsx", "xls"],
            key=f"p19_di_excel_{st.session_state.p19_uploader_key}",
        )
    with col2:
        di_pdf_file = st.file_uploader(
            "DI (PDF) — opcional / fallback",
            type=["pdf"],
            key=f"p19_di_pdf_{st.session_state.p19_uploader_key}",
        )

    if st.button("Revisar", type="primary", key="p19_btn_revisar"):
        if not dj_file or (not di_excel_file and not di_pdf_file):
            st.warning("Subí la DJ SENASA y al menos un formato de la DI (Excel o PDF).")
            st.stop()

        with tempfile.TemporaryDirectory() as tmp:
            dj_path = os.path.join(tmp, "dj.pdf")
            with open(dj_path, "wb") as f:
                f.write(dj_file.getbuffer())
            dj_data = extract_dj_senasa(dj_path)

            di_excel_data = {}
            if di_excel_file:
                di_excel_path = os.path.join(tmp, "di.xlsx")
                with open(di_excel_path, "wb") as f:
                    f.write(di_excel_file.getbuffer())
                di_excel_data = extract_di_excel(di_excel_path)

            di_pdf_data = {}
            if di_pdf_file:
                di_pdf_path = os.path.join(tmp, "di.pdf")
                with open(di_pdf_path, "wb") as f:
                    f.write(di_pdf_file.getbuffer())
                di_pdf_data = extract_di_pdf(di_pdf_path)

            di_data = merge_di_sources(di_excel_data, di_pdf_data)

        resultado = validate(dj_data, di_data)

        st.session_state.p19_resultado = resultado
        st.session_state.p19_dj_data = dj_data
        st.session_state.p19_di_data = di_data
        # Si el operador no cargó referencia a mano, se usa la detectada
        # automáticamente en la DI como respaldo.
        if not st.session_state.p19_referencia_input:
            st.session_state.p19_referencia_input = di_data.get("referencia") or ""
        st.rerun()

else:
    resultado = st.session_state.p19_resultado
    dj_data = st.session_state.p19_dj_data
    di_data = st.session_state.p19_di_data

    st.divider()

    if not resultado["aduana_reconocida"]:
        st.error(
            f"No se reconoció la aduana informada en la DI "
            f"('{resultado.get('aduana_texto') or 'no detectada'}'). "
            f"Esta v1 solo soporta Ezeiza y Buenos Aires."
        )
        st.button("Nuevo análisis", on_click=nuevo_analisis, type="primary", key="p19_btn_nuevo_error")
        st.stop()

    checks = resultado["checks"]
    errores = [c for c in checks if not c["ok"]]

    st.caption(f"Referencia del despacho: **{st.session_state.p19_referencia_input or '(sin referencia)'}**")

    st.markdown(f"### Resumen general — Aduana: **{resultado['aduana_key']}**")
    if errores:
        st.error(f"⚠️ Se encontraron {len(errores)} de {len(checks)} campos con diferencias.")
    else:
        st.success(f"✅ Los {len(checks)} campos revisados coinciden correctamente.")

    st.markdown("### Detalle por campo")
    for c in checks:
        icon = "✅" if c["ok"] else "❌"
        with st.container(border=True):
            st.markdown(f"{icon} **{c['campo']}**")
            cols = st.columns(2)
            with cols[0]:
                st.caption("DJ SENASA")
                st.write(c["valor_dj"] or "*(no detectado)*")
            with cols[1]:
                label = c["detalle_esperado"] or "Valor esperado"
                st.caption(label)
                st.write(c["valor_esperado"] or "*(no detectado)*")

    with st.expander("Ver datos crudos extraídos"):
        st.write("**DJ SENASA:**", dj_data)
        st.write("**DI (combinada):**", di_data)

    st.divider()

    di_data_para_pdf = dict(di_data)
    di_data_para_pdf["referencia"] = st.session_state.p19_referencia_input

    pdf_bytes = build_report_pdf(resultado, di_data_para_pdf)

    col_a, col_b = st.columns(2)
    with col_a:
        st.download_button(
            "⬇️ Descargar reporte (PDF)",
            data=pdf_bytes,
            file_name=f"corrector_senasa_{(st.session_state.p19_referencia_input or 'reporte').replace(' ', '_')}.pdf",
            mime="application/pdf",
            use_container_width=True,
            key="p19_btn_download",
        )
    with col_b:
        st.button("🔄 Nuevo análisis", on_click=nuevo_analisis, use_container_width=True, key="p19_btn_nuevo")
