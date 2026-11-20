"""Orquesta el control completo: PD + documentos -> filas de resultado."""
import re

from .compare import comparar, norm_id
from .config import TIPOS
from .extract import elegir_material, extraer
from .listado import buscar_material, cargar_listado, prefijos_hs, sugerir_materiales
from .pd_parser import parse_pd
from .readers import read_doc

_IDS = {"factura": ["invoice_number"], "transporte": ["transport_doc_number"], "coa": ["lot"], "packing": []}
# campos "identificadores" que deben aparecer literalmente en el texto del documento (anti-alucinación)


def _no_aparecen(datos: dict, texto: str, claves: list) -> list:
    t = norm_id(texto)
    return [c for c in claves if datos.get(c) and norm_id(datos[c]) not in t]


def _leer(clave: str, data: bytes, proveedor):
    """Lee y extrae un documento. Devuelve (datos, texto, método). Un fallo no frena el resto del control."""
    doc = read_doc(data, posicional=True)
    datos = extraer(clave, doc, proveedor)
    if not doc.scanned:
        datos["_no_encontrado"] = _no_aparecen(datos, doc.text, _IDS[clave])
    return datos, doc.text, doc.metodo


def validar(tipo: str, archivos: dict, proveedor, progreso=None) -> dict:
    """archivos: {'pd','listado'} obligatorios; 'factura','transporte','packing' opcionales (bytes);
    'coa' = bytes o lista de bytes (un COA por lote). -> dict con filas y datos leídos."""
    avance = progreso or (lambda *_: None)
    avance("Leyendo el PD…")
    pd = parse_pd(archivos["pd"])

    docs, textos, lecturas = {}, {}, {}
    for clave, etiqueta in (("factura", "la factura"), ("transporte", "el BL/guía/CRT"), ("packing", "el packing list")):
        if not archivos.get(clave):
            docs[clave] = {"_error": "no se subió el archivo"}
            continue
        avance(f"Leyendo {etiqueta}…")
        try:
            docs[clave], textos[clave], lecturas[clave] = _leer(clave, archivos[clave], proveedor)
        except Exception as e:
            docs[clave] = {"_error": str(e)}

    coa_files = archivos.get("coa") or []
    coa_files = [coa_files] if isinstance(coa_files, (bytes, bytearray)) else list(coa_files)
    docs["coas"] = []
    for n, data in enumerate(coa_files, 1):
        avance(f"Leyendo COA {n} de {len(coa_files)}…")
        try:
            datos, texto, metodo = _leer("coa", data, proveedor)
            textos[f"coa{n}"], lecturas[f"coa{n}"] = texto, metodo
        except Exception as e:
            datos = {"_error": str(e)}
        docs["coas"].append(datos)
    if not docs["coas"]:
        docs["coas"] = [{"_error": "no se subió el archivo"}]

    avance("Buscando el material en el listado…")
    listado = cargar_listado(archivos["listado"])
    cod = re.sub(r"\D", "", str(docs["factura"].get("item_code") or ""))
    metodo = "código"
    material = (cod, listado[cod]) if cod in listado else buscar_material(listado, *textos.values())
    if not material[0]:
        # el código de la factura suele ser el del proveedor: se busca por descripción y posición arancelaria
        hs = prefijos_hs(*textos.values())
        producto = " / ".join(str(x) for x in (docs["factura"].get("description"), docs["coas"][0].get("product")) if x)
        cand = sugerir_materiales(listado, producto, hs)
        if cand:
            try:
                avance("Eligiendo el material en el listado…")
                material, metodo = elegir_material(cand, producto, hs, proveedor), "descripción/arancel"
            except Exception:
                material = (None, None)
    material = (*material, metodo)

    filas = comparar(tipo, pd, docs, material)
    return {"tipo": TIPOS[tipo].nombre, "pd_numero": pd["numero"], "filas": filas, "pd": pd,
            "docs": {k: v for k, v in docs.items() if k != "coas"} | {f"coa{n}": c for n, c in enumerate(docs["coas"], 1)},
            "lecturas": lecturas, "avisos": pd["avisos"], "material": material[0], "material_metodo": material[2]}
