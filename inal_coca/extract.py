"""Prompts y extracción de datos de cada documento de soporte."""
import re

from .llm import Proveedor
from .readers import MAX_CHARS, Doc

_REGLAS = ("Reglas: transcribí los datos tal cual figuran en el documento, no inventes ni completes. "
           "Si un dato no figura, devolvé null. Devolvé SOLO un objeto JSON con estas claves:")

PROMPTS = {
    "factura": f"""Documento: FACTURA COMERCIAL de importación (puede estar en español, inglés o portugués; las páginas repetidas son copias).
{_REGLAS}
- "invoice_number": número de factura (figura como Invoice number, Invoice No., Folio, Factura N°, Nº). Solo el número o código.
- "item_code": código de material del producto. Si figura "Customer Material No." (o material del cliente), usá ese; si no, el de la columna Artículo/Código/Item/Material. null si no hay.
- "description": descripción del producto tal como figura en el detalle.
- "quantity": cantidad de unidades tal como figura (columna Cantidad / Qty / Quantity).
- "quantity_unit": unidad de medida de esa cantidad (KG, L, UN, etc.).
- "batches": si la factura detalla lotes con su cantidad (BATCHES, Lote, Batch), una lista de objetos {{"lot": "...", "quantity": "..."}} (cantidad tal como figura); si no los detalla, [].
- "net_weight_kg": peso neto en kilos tal como figura (Peso neto, Kilos netos, Net weight). Si no hay y la unidad de la cantidad es KG, usá la cantidad.""",

    "transporte": f"""Documento: BL (conocimiento de embarque), guía aérea (HAWB/AWB) o CRT (carta de porte por carretera).
{_REGLAS}
- "document_type": "BL", "HAWB" o "CRT".
- "transport_doc_number": número del documento. En un BL es el "B/L No." (no "Consol Ref." ni "Reference No."); en una guía aérea el número HAWB; en un CRT el casillero 2 "Número".
- "procedencia_pais": país de procedencia (el país, no la ciudad), en español. En un BL tomalo de "Place of Receipt"; en una guía aérea HAWB de "Airport of Departure (Addr. of First Carrier) and Requested Routing"; en un CRT del casillero 2 "Número", cuyo sufijo indica el país (CH=Chile, BR=Brasil, UY=Uruguay, PY=Paraguay, BO=Bolivia, PE=Perú, AR=Argentina) y, si no alcanza, del casillero 7 (lugar y país donde el porteador se hace cargo).
- "procedencia_evidencia": el texto breve del documento en el que te basaste.""",

    "coa": f"""Documento: COA (certificado de análisis) de un producto alimenticio o aditivo.
{_REGLAS}
- "lot": lote (figura como Batch, Lot, Lote, Número de Batch).
- "expiry_date": fecha de vencimiento en formato YYYY-MM-DD (Best before date, Expiry/Expire date, EXP DATE, Retest date, Fecha Expiración, Vencimiento). Respetá el formato que el propio documento indica (p. ej. "dd/mm/yy"; un año de 2 dígitos es 20xx). null si no hay una fecha explícita.
- "expiry_raw": esa fecha tal como figura escrita en el documento, o null.
- "manufacture_date": fecha de elaboración/manufactura en formato YYYY-MM-DD, o null.
- "shelf_life": si el documento solo informa una vida útil (p. ej. "2 años desde la fecha de elaboración"), ese texto; si no, null.
- "country_of_origin": país de origen, en español: generalmente el país que emite el certificado (por la dirección del emisor en el encabezado o pie de página), o el declarado en "Originally produced by".
- "health_guarantee_country": país de aval sanitario, en español: generalmente el país que emite el certificado, o el de "Originally produced by".
- "manufacturer": nombre del elaborador: el apartado manufacturer/elaborador/fabricante o "Originally produced by"; si no existe, la empresa que emite el certificado (logo, encabezado, pie de página o dominio del correo) o que declara haber preparado el producto.
- "product": nombre del producto tal como figura.
- "item_code": código de material si figura (MATERIAL #, Material No.), o null.""",

    "packing": f"""Documento: PACKING LIST (lista de empaque).
{_REGLAS}
- "gross_weights": lista con TODOS los valores de peso bruto que figuran (GROSS WEIGHT, Peso bruto, GROSS WT), cada uno como texto tal cual figura, incluido el total.
- "unit": unidad de esos pesos (KG, LB, etc.).""",
}


# Un CRT numera con el código del país de emisión: 085TERRA/CH2026 -> Chile
_PAIS_CRT = {"AR": "Argentina", "BO": "Bolivia", "BR": "Brasil", "CH": "Chile", "PY": "Paraguay", "PE": "Perú", "UY": "Uruguay"}
_NUM_CRT = re.compile(r"\b([A-Z0-9]{2,}[A-Z0-9/\-]*?/(" + "|".join(_PAIS_CRT) + r")\d{2,4})\b")


def _respaldo_crt(datos: dict, texto: str) -> None:
    """Si la IA no encontró el número o el país de un CRT, se sacan del número (sufijo con código de país)."""
    if not re.search(r"(?i)carta\s+de\s+porte|\bCRT\b", texto):
        return
    m = _NUM_CRT.search(texto)
    if not m:
        return
    if not datos.get("transport_doc_number"):
        datos["transport_doc_number"] = m.group(1)
        datos["_respaldo"] = "número del CRT tomado por patrón"
    if not datos.get("procedencia_pais"):
        datos["procedencia_pais"] = _PAIS_CRT[m.group(2)]
        datos["procedencia_evidencia"] = f"sufijo {m.group(2)} del número {m.group(1)}"


def extraer(clave: str, doc: Doc, proveedor: Proveedor) -> dict:
    """Extrae los datos del documento. Usa texto si el PDF lo tiene y visión si es un escaneo."""
    if doc.scanned:
        datos = proveedor.extraer_json(PROMPTS[clave], imagenes=doc.images)
    else:
        datos = proveedor.extraer_json(PROMPTS[clave], contenido=doc.text[:MAX_CHARS])
    if clave == "transporte" and not doc.scanned:
        _respaldo_crt(datos, doc.text)
    datos["_metodo"] = doc.metodo
    datos["_modelo"] = getattr(proveedor, "ultimo_modelo", None)
    return datos


def elegir_material(candidatos: list, producto: str, hs: set, proveedor: Proveedor) -> tuple:
    """Cuando el código de la factura no está en el listado: la IA elige entre los candidatos por descripción."""
    lista = "\n".join(f"{c} | {i['denominacion']} | {i['categoria'] or '-'}" for c, i in candidatos)
    instr = (
        "Tenés que identificar a qué material del LISTADO DE IMPORTACIÓN corresponde un producto de una factura "
        "(los nombres pueden estar en otro idioma o en forma abreviada).\n"
        f"Producto de la factura/COA: {producto}\nPosición arancelaria informada: {', '.join(sorted(hs)) or 'sin dato'}\n\n"
        f"Candidatos (código | denominación | categoría):\n{lista}\n\n"
        'Devolvé SOLO un JSON: {"codigo": "<código del candidato que corresponde, o null si ninguno corresponde claramente>", '
        '"motivo": "<explicación breve>"}. No inventes códigos que no estén en la lista.')
    r = proveedor.extraer_json(instr)
    cod = str(r.get("codigo") or "").strip()
    validos = dict(candidatos)
    return (cod, validos[cod]) if cod in validos else (None, None)
