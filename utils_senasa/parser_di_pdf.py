"""
Parser de la Declaración de Importación (DI / SIM de ARCA) en PDF.

Se usa como FALLBACK cuando el despachante no tiene el Excel de la DI
a mano. El Excel (parser_di_excel.py) es la fuente preferida porque es
más confiable.

LIMITACIÓN CONOCIDA: este parser depende de coordenadas fijas (x,y) de
la hoja 1 del PDF estándar de ARCA (formato "IMPORTACION A CONSUMO CON
DOCUMENTO DE TRANSPORTE"). Si ARCA cambia el layout del formulario, o si
el PDF viene escaneado/rotado, hay que reajustar las bandas de coordenadas
de abajo (Y_BANDS). Probado contra el formato SIM vigente a jul/2026.
"""

import re
import fitz

# Bandas (y_min, y_max, x_min, x_max) calibradas contra el formulario SIM
# estándar de ARCA (hoja 1). Cada banda captura la fila de VALOR ubicada
# justo debajo del encabezado correspondiente, evitando invadir la fila
# de encabezado de arriba o el bloque de datos de abajo.
Y_BANDS = {
    "aduana": (28, 45, 80, 260),
    "via": (92, 107, 20, 130),
    "origen": (244, 258, 120, 230),
    "procedencia": (244, 258, 230, 335),
    "deposito": (137, 150, 225, 375),
}


def _value_in_band(words, y_min, y_max, x_min, x_max):
    ws = [w for w in words if y_min <= w[1] <= y_max and x_min <= w[0] <= x_max]
    ws.sort(key=lambda w: w[0])
    text = " ".join(w[4] for w in ws).strip()
    return text if text else None


def extract_di_pdf(pdf_path: str) -> dict:
    """
    Devuelve un dict con: aduana, via, pais_origen, pais_procedencia, deposito.
    Cualquier campo no encontrado queda en None.
    """
    doc = fitz.open(pdf_path)
    page = doc[0]
    words = page.get_text("words")
    full_text = page.get_text()

    data = {
        "aduana": _value_in_band(words, *Y_BANDS["aduana"]),
        "via": _value_in_band(words, *Y_BANDS["via"]),
        "pais_origen": _value_in_band(words, *Y_BANDS["origen"]),
        "pais_procedencia": _value_in_band(words, *Y_BANDS["procedencia"]),
        "deposito": _value_in_band(words, *Y_BANDS["deposito"]),
        "referencia": None,
    }

    m = re.search(r"Ref:\s*(\d+\s*-\s*[\w-]+)", full_text)
    if m:
        data["referencia"] = re.sub(r"\s*-\s*", " - ", m.group(1).strip())

    doc.close()
    return data
