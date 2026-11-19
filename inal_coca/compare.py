"""Normalización y comparación PD vs documentos. Todo acá es determinista (sin IA)."""
import re
import unicodedata
from dataclasses import dataclass
from datetime import date
from difflib import SequenceMatcher

from .config import CLAVE_PD, TIPOS

OK, ERROR, REVISAR = "ok", "error", "revisar"
NOMBRES = {"factura": "la factura", "transporte": "el BL/guía/CRT", "coa": "el COA", "packing": "el packing list"}
CORTO = {"factura": "Factura", "transporte": "BL/Guía/CRT", "coa": "COA", "packing": "Packing list"}


@dataclass
class Fila:
    campo: str
    pd: str | None
    fuente: str
    estado: str
    detalle: str = ""


# ---------- normalización ----------
def sin_acentos(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", str(s)) if unicodedata.category(c) != "Mn")


def norm_texto(s) -> str:
    return re.sub(r"[^a-z0-9]+", " ", sin_acentos(s).lower()).strip()


def norm_id(s) -> str:
    return re.sub(r"[^A-Z0-9]", "", sin_acentos(s).upper())


def parse_numero(s) -> float | None:
    """Acepta 24000, 24.000,00, 24,000.00, 24.000,000. Un único separador con 3 decimales se toma como miles."""
    if s is None:
        return None
    if isinstance(s, (int, float)):
        return float(s)
    t = re.sub(r"[^\d.,-]", "", str(s))
    if not re.search(r"\d", t):
        return None
    if "." in t and "," in t:
        dec = "," if t.rfind(",") > t.rfind(".") else "."
        mil = "." if dec == "," else ","
        t = t.replace(mil, "").replace(dec, ".")
    elif "." in t or "," in t:
        sep = "." if "." in t else ","
        partes = t.lstrip("-").split(sep)
        # miles válidos: grupos de 3 dígitos y entero inicial de 1 a 3 cifras distinto de 0 (24.000 -> 24000)
        # cualquier otro caso es decimal (20000.000 -> 20000; 0,500 -> 0.5; 12,5 -> 12.5)
        miles = (len(partes) > 2 or len(partes[-1]) == 3) and 1 <= len(partes[0]) <= 3 and partes[0] != "0" \
            and all(len(x) == 3 for x in partes[1:])
        t = "".join(t.split(sep)) if miles else t.replace(sep, ".")
    try:
        return float(t)
    except ValueError:
        return None


def parse_fecha(s) -> date | None:
    if not s:
        return None
    m = re.search(r"(\d{4})-(\d{1,2})-(\d{1,2})", str(s))
    if m:
        a, mes, d = map(int, m.groups())
    else:
        m = re.search(r"(\d{1,2})[/.-](\d{1,2})[/.-](\d{4})", str(s))
        if not m:
            return None
        d, mes, a = map(int, m.groups())
    try:
        return date(a, mes, d)
    except ValueError:
        return None


def sumar_meses(f: date, meses: int) -> date:
    y, m = divmod(f.month - 1 + meses, 12)
    y, m = f.year + y, m + 1
    for d in (f.day, 30, 29, 28):
        try:
            return date(y, m, d)
        except ValueError:
            continue
    return date(y, m, 28)


def fmt_fecha(f: date) -> str:
    return f.strftime("%d/%m/%Y")


_SUFIJOS = {"sa", "srl", "ltda", "ltd", "inc", "llc", "spa", "sas", "gmbh", "corp", "limited", "co", "cia"}


def norm_empresa(s) -> list:
    t = norm_texto(s).split()
    while t:
        if t[-2:] == ["s", "a"] or t[-2:] == ["s", "l"]:
            t = t[:-2]
        elif t[-3:] == ["s", "r", "l"] or t[-3:] == ["s", "a", "s"]:
            t = t[:-3]
        elif t[-1] in _SUFIJOS:
            t = t[:-1]
        else:
            break
    return t


def _singular(tokens: list) -> list:
    return [t[:-1] if len(t) > 3 and t.endswith("s") else t for t in tokens]


# ---------- países ----------
_PAISES = {
    "AR": "argentina", "CL": "chile", "BR": "brasil|brazil", "UY": "uruguay", "PY": "paraguay", "BO": "bolivia",
    "PE": "peru", "CO": "colombia", "EC": "ecuador", "VE": "venezuela", "MX": "mexico",
    "US": "estados unidos|united states|usa|eeuu|ee uu|us", "CA": "canada", "CN": "china", "IN": "india",
    "DE": "alemania|germany", "ES": "espana|spain", "IT": "italia|italy", "FR": "francia|france",
    "GB": "reino unido|united kingdom|uk|inglaterra|england", "NL": "paises bajos|netherlands|holanda",
    "BE": "belgica|belgium", "CH": "suiza|switzerland", "JP": "japon|japan", "KR": "corea del sur|south korea|korea",
    "AU": "australia", "NZ": "nueva zelanda|new zealand", "ZA": "sudafrica|south africa", "TH": "tailandia|thailand",
    "VN": "vietnam", "ID": "indonesia", "MY": "malasia|malaysia", "SG": "singapur|singapore", "TR": "turquia|turkey",
    "IL": "israel", "DK": "dinamarca|denmark", "SE": "suecia|sweden", "NO": "noruega|norway", "FI": "finlandia|finland",
    "AT": "austria", "IE": "irlanda|ireland", "PT": "portugal", "PL": "polonia|poland", "HU": "hungria|hungary",
    "CZ": "republica checa|czech republic|chequia", "CR": "costa rica", "GT": "guatemala", "PA": "panama",
    "DO": "republica dominicana|dominican republic", "CU": "cuba", "HN": "honduras", "SV": "el salvador",
    "NI": "nicaragua", "TW": "taiwan", "HK": "hong kong", "PH": "filipinas|philippines", "PK": "pakistan",
    "EG": "egipto|egypt", "MA": "marruecos|morocco", "GR": "grecia|greece", "RU": "rusia|russia",
}
_PAIS_ISO = {norm_texto(n): iso for iso, ns in _PAISES.items() for n in ns.split("|")}


def iso_pais(s) -> str | None:
    """Devuelve el código ISO de un país escrito como 'Chile', 'Chile - CL', 'CL', 'Brazil'..."""
    if not s:
        return None
    s = str(s)
    m = re.search(r"-\s*([A-Z]{2})\s*$", s.strip())
    if m:
        return m.group(1)
    n = norm_texto(s)
    if n in _PAIS_ISO:
        return _PAIS_ISO[n]
    for nombre, iso in sorted(_PAIS_ISO.items(), key=lambda x: -len(x[0])):
        if len(nombre) > 3 and re.search(rf"\b{nombre}\b", n):
            return iso
    return None


# ---------- comparadores: (pd, fuente) -> (estado, detalle) ----------
def c_igual_texto(pd, src):
    return (OK, "") if norm_texto(pd) == norm_texto(src) else (ERROR, f"PD: {pd} / dato esperado: {src}")


def c_id(pd, src, nombre_doc):
    if norm_id(pd) == norm_id(src):
        return OK, ("" if str(pd).strip().upper() == str(src).strip().upper()
                    else "coincide (el PD no admite espacios/caracteres especiales)")
    return ERROR, f"PD: {pd} / {nombre_doc}: {src}"


def c_pais(pd, src, nombre_doc):
    a, b = iso_pais(pd), iso_pais(src)
    if a and b:
        return (OK, "") if a == b else (ERROR, f"PD: {pd} / {nombre_doc}: {src}")
    return (OK, "") if norm_texto(pd) == norm_texto(src) else (REVISAR, f"No se pudo comparar el país (PD: {pd} / {nombre_doc}: {src})")


def c_empresa(pd, src, nombre_doc):
    a, b = norm_empresa(pd), norm_empresa(src)
    if a and b and (a == b or SequenceMatcher(None, " ".join(a), " ".join(b)).ratio() >= 0.92):
        return OK, ""
    sa, sb = " ".join(a), " ".join(b)
    if sa and sb and (sa in sb or sb in sa):
        return OK, "coincide (el nombre del documento incluye texto adicional)"
    return ERROR, f"PD: {pd} / {nombre_doc}: {src}"


def c_denominacion(pd, src):
    return (OK, "") if _singular(norm_texto(pd).split()) == _singular(norm_texto(src).split()) \
        else (ERROR, f"PD: {pd} / listado: {src}")


def c_marca(pd, src):
    a, b = norm_texto(pd), norm_texto(src)
    return (OK, "") if a and (a == b or a in b or b in a) else (ERROR, f"PD: {pd} / factura: {src}")


def c_numero(pd, src, nombre_doc, unidad=""):
    a, b = parse_numero(pd), parse_numero(src)
    if a is None or b is None:
        return REVISAR, f"No se pudo interpretar el número (PD: {pd} / {nombre_doc}: {src})"
    pd_txt = f"{pd:g}" if isinstance(pd, (int, float)) else pd
    return (OK, "") if abs(a - b) < 0.005 else (ERROR, f"PD: {pd_txt} / {nombre_doc}: {b:g}{unidad}")


def c_fecha(pd, f_src, nombre_doc):
    f_pd = parse_fecha(pd)
    if not f_pd:
        return REVISAR, f"No se pudo interpretar la fecha del PD ({pd})"
    return (OK, "") if f_pd == f_src else (ERROR, f"PD: {fmt_fecha(f_pd)} / {nombre_doc}: {fmt_fecha(f_src)}")


# ---------- armado de filas ----------
def _dato(d, doc, clave):
    """Valor `clave` del documento extraído `d`, o (None, motivo)."""
    if d is None:
        return None, f"No hay {NOMBRES[doc]} para este dato"
    if "_error" in d:
        return None, f"No se pudo leer {NOMBRES[doc]}: {d['_error']}"
    v = d.get(clave)
    if v in (None, "", [], "null", "None"):
        return None, f"No figura / no se pudo leer en {NOMBRES[doc]}"
    return v, None


def _vencimiento(d):
    """Fecha de vencimiento del COA: explícita o calculada desde elaboración + vida útil."""
    if d is None:
        return None, "", "No hay COA para este lote"
    if "_error" in d:
        return None, "", f"No se pudo leer el COA: {d['_error']}"
    f = parse_fecha(d.get("expiry_date"))
    if f:
        raw = d.get("expiry_raw")
        return f, f"COA: {fmt_fecha(f)}" + (f" ({raw})" if raw and str(raw) != fmt_fecha(f) else ""), None
    fe, vida = parse_fecha(d.get("manufacture_date")), str(d.get("shelf_life") or "")
    m = re.search(r"(\d+)\s*(a[nñ]os?|years?|mes(?:es)?|months?)", sin_acentos(vida), re.I)
    if fe and m:
        n = int(m.group(1)) * (12 if m.group(2).lower().startswith(("a", "y")) else 1)
        f = sumar_meses(fe, n)
        return f, f"COA: {fmt_fecha(f)} (calculado: elaboración {fmt_fecha(fe)} + {vida})", None
    return None, "", "El COA no informa una fecha de vencimiento utilizable"


def _elegir_coa(coas: list, lote_pd):
    """COA que corresponde al lote del PD (por número de lote). Con un solo COA se usa ese."""
    if lote_pd:
        for c in coas:
            if "_error" not in c and c.get("lot") and norm_id(c["lot"]) == norm_id(lote_pd):
                return c
    return coas[0] if len(coas) == 1 else None


def _bruto_packing(pk):
    """(mayor peso bruto en kg, texto de todos los valores, motivo_de_error)."""
    lista, err = _dato(pk, "packing", "gross_weights")
    if err:
        return None, "", err
    nums = [n for n in (parse_numero(x) for x in (lista if isinstance(lista, list) else [lista])) if n is not None]
    unidad = str(pk.get("unit") or "KG").upper()
    if not nums:
        return None, "", "No se pudo interpretar el peso bruto del packing list"
    if not unidad.startswith(("KG", "KILO")):
        return None, "", f"El packing list está en {unidad}, no en kg"
    return max(nums), ", ".join(f"{n:g}" for n in nums), None


def comparar(tipo_key: str, pd: dict, docs: dict, material: tuple) -> list:
    """pd = salida de parse_pd; docs = {'factura','transporte','packing': dict, 'coas': [dict]};
    material = (codigo, info_listado[, metodo])."""
    tipo, h, lotes, filas = TIPOS[tipo_key], pd["campos"], pd["lotes"], []
    fa, tr, pk, coas = docs["factura"], docs["transporte"], docs["packing"], docs["coas"]
    multi = len(lotes) > 1

    def agregar(campo, pdv, fuente, res):
        estado, detalle = res
        filas.append(Fila(campo, pdv, fuente, estado, detalle))

    def con(campo, pdv, doc, d, clave, fn, fuente_fn=None):
        if pdv is None:
            return agregar(campo, None, "", (REVISAR, "No se encontró el campo en el PD"))
        src, err = _dato(d, doc, clave)
        if err:
            return agregar(campo, pdv, "", (REVISAR, err))
        if clave in (d.get("_no_encontrado") or []):
            return agregar(campo, pdv, f"{CORTO[doc]}: {src}",
                           (REVISAR, "El valor leído no aparece en el texto del documento: verificar manualmente"))
        agregar(campo, pdv, fuente_fn(src) if fuente_fn else f"{CORTO[doc]}: {src}", fn(pdv, src))

    # 1) datos fijos
    for campo, esperado in tipo.fijos:
        pdv = h.get(CLAVE_PD[campo])
        fuente = f"Dato fijo ({tipo.nombre}): {esperado}"
        if pdv is None:
            agregar(campo, None, fuente, (REVISAR, "No se encontró el campo en el PD"))
        else:
            agregar(campo, pdv, fuente, c_igual_texto(pdv, esperado))

    # 2) datos generales del PD
    con("Factura n°", h.get("factura"), "factura", fa, "invoice_number", lambda a, b: c_id(a, b, "factura"),
        lambda s: f"Factura: {s}")
    tipo_tr = (tr or {}).get("document_type") or "BL/Guía/CRT"
    con("Conocimiento de Embarque/Guía Aérea/CRT N°", h.get("transporte"), "transporte", tr, "transport_doc_number",
        lambda a, b: c_id(a, b, "documento"), lambda s: f"{tipo_tr}: {s}")
    evid = (tr or {}).get("procedencia_evidencia")
    con("País de procedencia", h.get("pais_procedencia"), "transporte", tr, "procedencia_pais",
        lambda a, b: c_pais(a, b, "documento"), lambda s: f"{tipo_tr}: {s}" + (f" ({evid})" if evid else ""))

    # 3) un bloque de controles por lote del PD
    cod, info = material[:2]
    como = ", por descripción/arancel" if len(material) > 2 and material[2] != "código" else ""
    lotes_coa = ", ".join(str(c.get("lot")) for c in coas if c.get("lot")) or "ninguno leído"
    for i, lp in enumerate(lotes):
        suf = f" [lote {lp.get('lote') or i + 1}]" if multi else ""
        coa = _elegir_coa(coas, lp.get("lote"))
        sin_coa = None if coa is not None else {"_error": "ninguno de los COA subidos corresponde a este lote"}

        con("País de origen" + suf, lp["pais_origen"], "coa", coa or sin_coa, "country_of_origin",
            lambda a, b: c_pais(a, b, "COA"), lambda s: f"COA: {s}")
        if tipo.aval_sanitario:
            con("País de Aval Sanitario" + suf, lp["pais_aval"], "coa", coa or sin_coa, "health_guarantee_country",
                lambda a, b: c_pais(a, b, "COA"), lambda s: f"COA: {s}")
        con("Nombre o Razón social del Elaborador" + suf, lp["elaborador"], "coa", coa or sin_coa, "manufacturer",
            lambda a, b: c_empresa(a, b, "COA"), lambda s: f"COA: {s}")

        for campo, clave_pd, clave_info, fn in (("Categoría de Producto", "categoria", "categoria", c_igual_texto),
                                                ("Denominación", "denominacion", "denominacion", c_denominacion)):
            pdv, val = lp[clave_pd], (info or {}).get(clave_info)
            if pdv is None:
                agregar(campo + suf, None, "", (REVISAR, "No se encontró el campo en el PD"))
            elif not cod:
                agregar(campo + suf, pdv, "Listado de importación",
                        (REVISAR, "No se encontró en el listado ningún código de material de la factura/COA"))
            elif not val:
                agregar(campo + suf, pdv, f"Listado de importación (material {cod})",
                        (REVISAR, "El material figura en el listado sin ese dato"))
            else:
                agregar(campo + suf, pdv, f"Listado de importación (material {cod}{como}): {val}", fn(pdv, val))

        con("Marca / Nombre fantasía" + suf, lp["marca"], "factura", fa, "description", c_marca,
            lambda s: f"Factura: {s}")

        # lote
        if coa is None and lp["lote"]:
            agregar("Lote" + suf, lp["lote"], "COA", (ERROR, f"El lote no figura en los COA subidos (lotes leídos: {lotes_coa})"))
        else:
            con("Lote" + suf, lp["lote"], "coa", coa, "lot", lambda a, b: c_id(a, b, "COA"), lambda s: f"COA: {s}")

        # cantidad y peso neto: de la factura, por lote si la factura lo detalla
        lote_n = norm_id(lp.get("lote"))
        lote_fa = next((b for b in (fa or {}).get("batches") or []
                        if isinstance(b, dict) and norm_id(b.get("lot")) == lote_n and lote_n), None)
        unidad = str((fa or {}).get("quantity_unit") or "").strip()
        if lote_fa:
            q = lote_fa.get("quantity")
            agregar("Cantidad de unidades" + suf, lp["cantidad"], f"Factura (lote): {q} {unidad}".strip(),
                    c_numero(lp["cantidad"], q, "factura") if lp["cantidad"] is not None else (REVISAR, "No se encontró el campo en el PD"))
            agregar("Peso Neto (Kg)" + suf, lp["peso_neto"], f"Factura (lote): {q} {unidad}".strip(),
                    c_numero(lp["peso_neto"], q, "factura", " kg") if lp["peso_neto"] is not None else (REVISAR, "No se encontró el campo en el PD"))
        elif multi:
            msg = (REVISAR, "La factura no detalla la cantidad de este lote")
            agregar("Cantidad de unidades" + suf, lp["cantidad"], "", msg)
            agregar("Peso Neto (Kg)" + suf, lp["peso_neto"], "", msg)
        else:
            con("Cantidad de unidades", lp["cantidad"], "factura", fa, "quantity",
                lambda a, b: c_numero(a, b, "factura"), lambda s: f"Factura: {s} {unidad}".strip())
            con("Peso Neto (Kg)", lp["peso_neto"], "factura", fa, "net_weight_kg",
                lambda a, b: c_numero(a, b, "factura", " kg"), lambda s: f"Factura: {s} kg")

        # vencimiento
        f, fuente, err = _vencimiento(coa or sin_coa)
        if lp["vencimiento"] is None:
            agregar("Fecha de vencimiento" + suf, None, "", (REVISAR, "No se encontró el campo en el PD"))
        elif err:
            agregar("Fecha de vencimiento" + suf, lp["vencimiento"], "", (REVISAR, err))
        else:
            agregar("Fecha de vencimiento" + suf, lp["vencimiento"], fuente, c_fecha(lp["vencimiento"], f, "COA"))

        # peso bruto: 1 lote -> el mayor del packing list; varios lotes -> se prorratea el total (ver abajo)
        if not multi:
            mayor, lista, err = _bruto_packing(pk)
            if lp["peso_bruto"] is None:
                agregar("Peso Bruto (Kg)", None, "", (REVISAR, "No se encontró el campo en el PD"))
            elif err:
                agregar("Peso Bruto (Kg)", lp["peso_bruto"], "", (REVISAR, err))
            else:
                agregar("Peso Bruto (Kg)", lp["peso_bruto"], f"Packing list: {mayor:g} kg (mayor de {lista})",
                        c_numero(lp["peso_bruto"], mayor, "packing list", " kg"))

    # 4) varios lotes: totales contra factura/packing y bruto por lote prorrateado
    if multi:
        suma = lambda k: (sum(parse_numero(l[k]) for l in lotes) if all(parse_numero(l[k]) is not None for l in lotes) else None)
        mayor, lista, err = _bruto_packing(pk)
        tot_bruto, tot_neto, tot_cant = suma("peso_bruto"), suma("peso_neto"), suma("cantidad")

        def total(campo, suma_pd, ref, fuente, fn_err):
            if suma_pd is None:
                agregar(campo, None, "", (REVISAR, "Algún lote del PD no tiene este dato"))
            elif ref is None:
                agregar(campo, f"{suma_pd:g}", "", (REVISAR, fn_err))
            else:
                agregar(campo, f"{suma_pd:g}", fuente, c_numero(suma_pd, ref, "documento", " kg"))

        q_fa, e1 = _dato(fa, "factura", "quantity")
        n_fa, e2 = _dato(fa, "factura", "net_weight_kg")
        total("Cantidad de unidades – total de lotes", tot_cant, parse_numero(q_fa) if not e1 else None,
              f"Factura: {q_fa}", e1 or "")
        total("Peso Neto (Kg) – total de lotes", tot_neto, parse_numero(n_fa) if not e2 else None,
              f"Factura: {n_fa} kg", e2 or "")
        total("Peso Bruto (Kg) – total de lotes", tot_bruto, mayor, f"Packing list: {mayor if mayor is None else format(mayor, 'g')} kg", err or "")
        for i, lp in enumerate(lotes):
            suf = f" [lote {lp.get('lote') or i + 1}]"
            pdv, neto = parse_numero(lp["peso_bruto"]), parse_numero(lp["peso_neto"])
            if pdv is None:
                agregar("Peso Bruto (Kg)" + suf, lp["peso_bruto"], "", (REVISAR, "No se encontró el campo en el PD"))
            elif mayor is None or not tot_neto or neto is None:
                agregar("Peso Bruto (Kg)" + suf, lp["peso_bruto"], "", (REVISAR, err or "No se puede prorratear"))
            else:
                esperado = mayor * neto / tot_neto
                ok = abs(pdv - esperado) <= 0.5
                agregar("Peso Bruto (Kg)" + suf, lp["peso_bruto"],
                        f"Packing list: total {mayor:g} kg, prorrateado por peso neto = {esperado:.2f} kg",
                        (OK, "el packing list informa solo el total; coincide con el prorrateo por peso neto") if ok else
                        (REVISAR, f"PD: {lp['peso_bruto']} / prorrateo esperado: {esperado:.2f} (el packing list no informa bruto por lote)"))
    return filas
