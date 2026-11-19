"""Lee el PD (PDF con texto generado por VUCEA/GDE) y devuelve sus campos."""
import re

from .readers import read_pdf

# clave -> texto de la etiqueta (la línea debe empezar con la etiqueta y tener ':')
_ETIQUETAS = {
    "rne_importador": r"RNE\s+importador",
    "rne_elaborador": r"RNE\s+elaborador",
    "provincia": r"Provincia",
    "departamento": r"Departamento",
    "localidad": r"Localidad",
    "domicilio": r"Domicil\w*",
    "factura": r"Factura\s*n[°º]?",
    "transporte": r"Conocimiento\s+de\s+Embarque",
    "pais_procedencia": r"Pa[ií]s\s+de\s+procedencia",
    "pais_origen": r"Pa[ií]s\s+de\s+origen",
    "pais_aval": r"Pa[ií]s\s+de\s+aval\s+sanitario",
    "elaborador": r"Nombre\s+o\s+Raz[oó]n\s+social\s+del\s+Elaborador",
    "categoria": r"Categor[ií]a\s+de\s+Producto",
    "marca": r"Marca\s*/\s*Nombre\s+fantas[ií]a",
    "lote": r"Lote",
    "cantidad": r"Cantidad\s+de\s+unidades",
    "vencimiento": r"Fecha\s+de\s+vencimiento",
    "peso_bruto": r"Peso\s+Bruto\s*\(Kg\)",
    "peso_neto": r"Peso\s+Neto\s*\(Kg\)",
}
_RX = {k: re.compile(rf"^\s*{v}[^:\n]*:+\s*(.*)$", re.I) for k, v in _ETIQUETAS.items()}


def _lineas(texto: str) -> list:
    lineas = [l.strip() for l in texto.splitlines()]
    # una etiqueta larga puede venir cortada en varias líneas: se une hasta encontrar ':'
    out, i = [], 0
    while i < len(lineas):
        l = lineas[i]
        if re.match(r"(?i)^conocimiento\s+de\s+embarque", l) and ":" not in l:
            j = i
            while j + 1 < len(lineas) and ":" not in l and j - i < 3:
                j += 1
                l = f"{l} {lineas[j]}"
            i = j
        out.append(l)
        i += 1
    return out


_PRODUCTO = {"pais_origen", "pais_aval", "elaborador", "categoria", "denominacion", "marca", "lote",
             "cantidad", "vencimiento", "peso_bruto", "peso_neto"}
_BLOQUE = re.compile(r"(?i)^datos\s+de(?:l)?\s+producto\b")


def parse_pd(data: bytes) -> dict:
    """Devuelve {'campos': cabecera, 'lotes': [producto por lote], 'numero': 'PD-...', 'avisos': [...]}.

    El PD repite el bloque "Datos del Producto" una vez por lote. Los campos que no se encuentran quedan en None.
    """
    texto = "\n".join(read_pdf(data).pages)
    lineas = _lineas(texto)
    cab = {k: None for k in _ETIQUETAS if k not in _PRODUCTO}
    lotes, actual = [], None

    def nuevo():
        lotes.append({k: None for k in _PRODUCTO})
        return lotes[-1]

    for idx, l in enumerate(lineas):
        if _BLOQUE.match(l):
            # un nuevo bloque solo empieza si el actual ya tiene datos
            if actual is None or any(v for v in actual.values()):
                actual = nuevo()
            continue
        for clave, rx in _RX.items():
            m = rx.match(l)
            if not m:
                continue
            valor = m.group(1).strip() or None
            if clave in _PRODUCTO:
                if actual is None:
                    actual = nuevo()
                if clave == "lote" and actual["lote"] is not None:
                    actual = nuevo()          # segundo lote sin encabezado de bloque
                if actual[clave] is None:
                    actual[clave] = valor
            elif cab[clave] is None:
                cab[clave] = valor
            break
        # "Denominación" viene como título y el valor en la(s) línea(s) siguiente(s)
        if re.fullmatch(r"(?i)denominaci[oó]n", l):
            if actual is None:
                actual = nuevo()
            if actual["denominacion"] is None:
                partes = []
                for sig in lineas[idx + 1: idx + 4]:
                    if not sig or ":" in sig or re.match(r"(?i)^datos\s", sig):
                        if partes:
                            break
                        continue
                    partes.append(sig)
                actual["denominacion"] = " ".join(partes) or None

    if not lotes:
        lotes.append({k: None for k in _PRODUCTO})
    m = re.search(r"PD-\d{4}-\d+-[A-Z]+-[\w#]+", texto)
    return {"campos": {**cab, **lotes[0]}, "lotes": lotes, "numero": m.group(0) if m else None, "avisos": []}
