"""
Parser de la Declaración Jurada de SENASA (embalajes de madera) en PDF.

El formulario es un PDF con layout de 2 columnas (izquierda / derecha).
Se extraen las palabras con coordenadas (PyMuPDF) y se reconstruyen líneas
por columna para poder aplicar regex de forma confiable, sin depender del
orden de lectura plano de get_text().
"""

import re
import fitz

COL_SPLIT_X = 270  # separación aproximada entre columna izquierda y derecha

FIELDS = {
    "pais_origen": r"Pa[ií]s\s+de\s+or[ií]gen",
    "pais_procedencia": r"Pa[ií]s\s+de\s+procedencia",
    "punto_ingreso": r"Punto\s+de\s+ingreso",
    "medio_transporte": r"Medio\s+de\s+transporte",
    "lugar_destino": r"Lugar\s+de\s+destino\s+de\s+la\s+mercanc[ií]a\s+importada",
}


def _build_lines(words, x_min, x_max, y_tol=5):
    """Agrupa palabras de una columna en líneas usando su coordenada Y."""
    ws = [w for w in words if x_min <= w[0] < x_max]
    buckets = {}
    for w in ws:
        key = round(w[1] / y_tol)
        buckets.setdefault(key, []).append(w)

    lines = []
    for key in sorted(buckets.keys()):
        ws_line = sorted(buckets[key], key=lambda w: w[0])
        text = " ".join(w[4] for w in ws_line)
        y = min(w[1] for w in ws_line)
        lines.append((y, text))
    lines.sort(key=lambda t: t[0])
    return lines


def _find_value(lines, label_pattern):
    """Busca la línea que matchea el label y devuelve lo que sigue al ':'.
    Si no hay nada después del ':' en la misma línea, toma la línea
    siguiente (caso "Lugar de destino..." cuyo valor va en el renglón de abajo).
    """
    for i, (_, text) in enumerate(lines):
        m = re.search(label_pattern + r"\s*:?\s*(.*)", text, re.IGNORECASE)
        if m:
            val = m.group(1).strip()
            if not val and i + 1 < len(lines):
                val = lines[i + 1][1].strip()
            return val if val else None
    return None


def extract_dj_senasa(pdf_path: str) -> dict:
    """
    Devuelve un dict con: pais_origen, pais_procedencia, punto_ingreso,
    medio_transporte, lugar_destino, n_dj (nº de declaración), cuve.
    Cualquier campo no encontrado queda en None.
    """
    doc = fitz.open(pdf_path)
    page = doc[0]
    words = page.get_text("words")
    full_text = page.get_text()

    left = _build_lines(words, 0, COL_SPLIT_X)
    right = _build_lines(words, COL_SPLIT_X, 10000)
    all_lines = left + right

    data = {}
    for field, pattern in FIELDS.items():
        data[field] = _find_value(all_lines, pattern)

    # Datos adicionales de cabecera (no forman parte del cruce, pero
    # ayudan a mostrar contexto en la UI)
    m = re.search(r"N[°º]:\s*(\d+)", full_text)
    data["n_dj"] = m.group(1) if m else None

    m = re.search(r"(\d{6,})\s*\n?\s*N[°º]\s*CUVE", full_text)
    data["cuve"] = m.group(1) if m else None

    doc.close()
    return data
