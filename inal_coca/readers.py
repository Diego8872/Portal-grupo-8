"""Lectura de PDFs: texto cuando hay, imágenes cuando el PDF es un escaneo (sin PyMuPDF/OCR externo)."""
import datetime as _dt
import io
import re
from dataclasses import dataclass, field

import fitz  # PyMuPDF
import openpyxl

MAX_CHARS = 14000        # tope de texto enviado al modelo por documento
MAX_PAGINAS_IMG = 4      # tope de páginas escaneadas enviadas como imagen
_MIN_CHARS_TEXTO = 60    # menos que esto en todo el PDF => se trata como escaneo
_RUIDO_COPIA = re.compile(r"\b(original|copia|copy|duplicado|triplicado|cedible|cliente)\b", re.I)


@dataclass
class Doc:
    pages: list = field(default_factory=list)   # texto por página
    scanned: bool = False
    excel: bool = False
    images: list = field(default_factory=list)  # JPEG por página (solo si scanned)

    @property
    def text(self) -> str:
        return "\n\n".join(self.pages)

    @property
    def metodo(self) -> str:
        return "visión (escaneado)" if self.scanned else ("Excel" if self.excel else "texto")


def _limpiar(t: str, colapsar: bool = True) -> str:
    t = re.sub(r"\n\s*\n+", "\n", t)
    return (re.sub(r"[ \t]+", " ", t) if colapsar else t).strip()


def _texto_posicional(page, tol: float = 3.0, hueco: float = 14.0) -> str:
    """Texto como se ve en la hoja: las palabras de una misma altura quedan en la misma línea
    (columnas separadas por 3 espacios). Evita que en formularios (CRT, BL) el dato quede lejos de su casillero."""
    palabras = sorted(page.get_text("words"), key=lambda w: (w[1] + w[3]) / 2)
    lineas = []
    for w in palabras:
        yc = (w[1] + w[3]) / 2
        if lineas and abs(lineas[-1][0] - yc) <= tol:
            lineas[-1][1].append(w)
            lineas[-1][0] = (lineas[-1][0] + yc) / 2
        else:
            lineas.append([yc, [w]])
    out = []
    for _, l in lineas:
        l.sort(key=lambda w: w[0])
        txt = l[0][4]
        for a, b in zip(l, l[1:]):
            txt += ("   " if b[0] - a[2] > hueco else " ") + b[4]
        out.append(txt)
    return "\n".join(out)


def _sin_copias(pages: list) -> list:
    """Quita páginas que son copias de otra (ORIGINAL / COPIA CEDIBLE...), muy común en facturas."""
    vistos, out = set(), []
    for p in pages:
        clave = re.sub(r"\s+", " ", _RUIDO_COPIA.sub("", p.lower())).strip()
        if clave and clave not in vistos:
            vistos.add(clave)
            out.append(p)
    return out


_LEGAL = re.compile(r"(?i)general\s+terms\s+and\s+conditions|terms\s+and\s+conditions\s+of\s+(sale|supply)|condiciones\s+generales\s+de\s+(venta|suministro)")


def _sin_legales(pages: list) -> list:
    """Quita las páginas de condiciones generales (varias miles de caracteres sin datos), salvo que sean las únicas."""
    utiles = [p for p in pages if not _LEGAL.search(p[:300])]
    return utiles or pages


def _celda(v) -> str:
    if v is None:
        return ""
    if isinstance(v, (_dt.datetime, _dt.date)):
        return v.strftime("%d/%m/%Y")
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    return re.sub(r"\s+", " ", str(v)).strip()


def read_excel(data: bytes) -> Doc:
    """Excel como texto: una hoja por 'página', una fila por línea, celdas separadas por 3 espacios."""
    wb = openpyxl.load_workbook(io.BytesIO(data), data_only=True, read_only=True)
    pages = []
    for ws in wb.worksheets:
        filas = []
        for row in ws.iter_rows(values_only=True):
            celdas = [c for c in (_celda(v) for v in row) if c]
            if celdas:
                filas.append("   ".join(celdas))
        if filas:
            pages.append(f"[Hoja: {ws.title}]\n" + "\n".join(filas))
    return Doc(pages=pages, excel=True)


def read_doc(data: bytes, posicional: bool = False) -> Doc:
    """PDF o Excel (se distingue por el contenido, no por el nombre)."""
    if data[:2] == b"PK":
        return read_excel(data)
    if data[:4] == b"\xd0\xcf\x11\xe0":
        raise ValueError("Excel .xls antiguo: guardalo como .xlsx y volvé a subirlo")
    return read_pdf(data, posicional)


def read_pdf(data: bytes, posicional: bool = False) -> Doc:
    """posicional=True: texto respetando la posición en la hoja (para la IA). False: texto plano (para el PD)."""
    pdf = fitz.open(stream=data, filetype="pdf")
    pages = [_limpiar(_texto_posicional(p), colapsar=False) if posicional else _limpiar(p.get_text("text")) for p in pdf]
    if sum(len(p) for p in pages) >= _MIN_CHARS_TEXTO:
        return Doc(pages=_sin_copias(_sin_legales(pages)))
    # escaneo: se renderizan las páginas para que las lea el modelo de visión
    imgs = []
    for p in list(pdf)[:MAX_PAGINAS_IMG]:
        pix = p.get_pixmap(matrix=fitz.Matrix(2, 2))
        imgs.append(pix.tobytes("jpeg"))
    return Doc(pages=[], scanned=True, images=imgs)
