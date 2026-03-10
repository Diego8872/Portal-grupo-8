import streamlit as st
import pandas as pd
import openpyxl
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
import re
import io

st.title("Corrector Descripciones Finning")

archivo = st.file_uploader(
    "Subí tu Excel (Columna A = Código | Columna B = Descripción)",
    type=["xlsx"]
)

def procesar_descripcion(texto):
    texto = str(texto)

    correcciones = {
        "hidraulico": "hidráulico",
        "hidraulica": "hidráulica",
        "presion": "presión",
        "transmision": "transmisión",
        "direccion": "dirección",
        "valvula": "válvula",
        "valvulas": "válvulas"
    }

    errores = []

    for k,v in correcciones.items():
        if k in texto.lower():
            texto = texto.lower().replace(k,v)
            errores.append(f"{k}→{v}")

    if texto:
        texto = texto[0].upper() + texto[1:]

    resumen = " | ".join(errores) if errores else "Sin errores"

    return texto, resumen

def generar_excel(resultados):

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Correcciones"

    headers = [
        "Código",
        "Descripción Original",
        "Errores Detectados",
        "Descripción Corregida"
    ]

    ws.append(headers)

    for r in resultados:
        ws.append([
            r["codigo"],
            r["original"],
            r["errores"],
            r["corregida"]
        ])

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    return buffer


if archivo:

    df = pd.read_excel(archivo)

    col_codigo = df.columns[0]
    col_desc = df.columns[1]

    resultados = []

    for _,row in df.iterrows():

        codigo = str(row[col_codigo])
        desc = str(row[col_desc])

        corregida, errores = procesar_descripcion(desc)

        resultados.append({
            "codigo": codigo,
            "original": desc,
            "errores": errores,
            "corregida": corregida
        })

    df_out = pd.DataFrame(resultados)

    st.dataframe(df_out)

    excel = generar_excel(resultados)

    st.download_button(
        "Descargar Excel corregido",
        data=excel,
        file_name="correcciones.xlsx"
    )
