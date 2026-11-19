"""Lectura de PDFs: texto cuando hay, imágenes cuando el PDF es un escaneo (sin PyMuPDF/OCR externo)."""
import re
from dataclasses import dataclass, field

import fitz  # PyMuPDF

MAX_CHARS = 14000        # tope de texto enviado al modelo por documento
MAX_PAGINAS_IMG = 4      # tope de páginas escaneadas enviadas como imagen
_MIN_CHARS_TEXTO = 60    # menos que esto en todo el PDF => se trata como escaneo
_RUIDO_COPIA = re.compile(r"\b(original|copia|copy|duplicado|triplicado|cedible|cliente)\b", re.I)


@dataclass
class Doc:
    pages: list = field(default_factory=list)   # texto por página
    scanned: bool = False
    images: list = field(default_factory=list)  # JPEG por página (solo si scanned)

    @property
    def text(self) -> str:
        return "\n\n".join(self.pages)

    @property
    def metodo(self) -> str:
        return "visión (escaneado)" if self.scanned else "texto"


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
