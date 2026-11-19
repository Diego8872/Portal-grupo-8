"""Listado de importación (Excel): col A = código de material, C = Denominación, D = Categoría."""
import io
import re

import openpyxl

from .compare import norm_texto


def _codigo(v) -> str | None:
    if v is None:
        return None
    s = str(v).strip()
    if re.fullmatch(r"\d+\.0", s):
        s = s[:-2]
    return s if re.fullmatch(r"\d{5,10}", s) else None


def cargar_listado(data: bytes) -> dict:
    """{codigo: {'denominacion':..., 'categoria':...}}. Si un código se repite, prefiere la fila con categoría."""
    wb = openpyxl.load_workbook(io.BytesIO(data), read_only=True, data_only=True)
    ws = wb.worksheets[0]
    out = {}
    for fila in ws.iter_rows(min_row=2, values_only=True):
        cod = _codigo(fila[0] if len(fila) > 0 else None)
        if not cod:
            continue
        hs = re.sub(r"\D", "", str(fila[1])) if len(fila) > 1 and fila[1] else ""
        den = str(fila[2]).strip() if len(fila) > 2 and fila[2] else None
        cat = str(fila[3]).strip() if len(fila) > 3 and fila[3] else None
        if cod not in out or (cat and not out[cod]["categoria"]):
            out[cod] = {"denominacion": den, "categoria": cat, "hs": hs}
    return out


def buscar_material(listado: dict, *textos: str) -> tuple:
    """Busca en los textos (factura, COA) el primer código de material que esté en el listado."""
    for t in textos:
        for cod in re.findall(r"\b\d{5,10}\b", t or ""):
            if cod in listado:
                return cod, listado[cod]
    return None, None


_HS_RX = re.compile(r"(?i)(?:hs\s*code|nandina|ncm|tariff|partida|arancel\w*)\W{0,40}?(\d[\d.\s]{4,14}\d)")


def prefijos_hs(*textos: str) -> set:
    """Posiciones arancelarias (6 dígitos) que figuran en los documentos (HS CODE, NANDINA, NCM...)."""
    out = set()
    for t in textos:
        for m in _HS_RX.finditer(t or ""):
            d = re.sub(r"\D", "", m.group(1))
            if len(d) >= 6:
                out.add(d[:6])
    return out


def _stems(texto: str) -> set:
    return {w[:5] for w in norm_texto(texto).split() if len(w) >= 4}


def sugerir_materiales(listado: dict, producto: str, hs: set, maximo: int = 15) -> list:
    """Candidatos del listado para un producto cuyo código no figura: coincidencia de posición arancelaria y/o palabras."""
    prod = _stems(producto)
    pun = []
    for cod, info in listado.items():
        coincide_hs = any(info.get("hs", "").startswith(h) for h in hs)
        solapadas = len(prod & _stems(info.get("denominacion") or ""))
        if coincide_hs or solapadas >= 2:
            pun.append((coincide_hs, solapadas, cod))
    pun.sort(reverse=True)
    return [(cod, listado[cod]) for _, _, cod in pun[:maximo]]
