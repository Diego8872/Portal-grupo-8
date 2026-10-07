import io
import re
import unicodedata
from collections import defaultdict, deque
from datetime import datetime

import pandas as pd
import streamlit as st
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

try:
    import pymupdf as fitz
except ImportError:
    import fitz


# =====================================================================
# TABLA DE PAÍSES (fija) — "LOCAL" = BA
# =====================================================================
PAISES = {
    'BURKINA FASO': 101, 'ARGELIA': 102, 'BOTSWANA': 103, 'BURUNDI': 104,
    'CAMERUN': 105, 'REP. CENTROAFRICANA.': 107, 'REP.CENTROAFRICANA': 107, 'EMIRATOS ARABES': 42,
    'CONGO': 108, 'PAISES BAJOS': 423, 'REP.DEMOCRAT.DEL CONGO EX ZAIRE': 109, 'REP. DEMOCRAT. DEL CONGO EX ZAIRE': 109,
    'DINAMARCA': 409, 'COSTA DE MARFIL': 110, 'CHAD': 111, 'ESTADOS UNIDOS': 212,
    'BENIN': 112, 'ALEMANIA,REP.FED.': 438, 'EGIPTO': 113, 'GABON': 115,
    'REPUBLICA CHECA': 451, 'GAMBIA': 116, 'FINLANDIA': 411, 'GHANA': 117,
    'GUINEA': 118, 'FRANCIA': 412, 'GUINEA ECUATORIAL': 119, 'KENYA': 120,
    'ESPANA': 410, 'LESOTHO': 121, 'LIBERIA': 122, 'LIBIA': 123,
    'TAIWAN': 313, 'MADAGASCAR': 124, 'MALAWI': 125, 'MALI': 126,
    'AUSTRIA': 405, 'MARRUECOS': 127, 'MAURICIO,ISLAS': 128, 'MAURITANIA': 129,
    'INDONESIA': 316, 'NIGER': 130, 'NIGERIA': 131, 'ZIMBABWE': 132,
    'REINO UNIDO': 426, 'RWANDA': 133, 'INDIA': 315, 'SENEGAL': 134,
    'COLOMBIA': 205, 'SIERRA LEONA': 135, 'SOMALIA': 136, 'SWAZILANDIA': 137,
    'SUDAN': 138, 'TANZANIA': 139, 'TOGO': 140, 'TUNEZ': 141,
    'UGANDA': 142, 'REPUBLICA DE SUDAFRICA': 143, 'ZAMBIA': 144, 'TERRIT.VINCULADOS AL R UNIDO': 145,
    'AFRICA': 145, 'TERRIT.VINCULADOS A ESPANA': 146, 'TERRIT.VINCULADOS A FRANCIA': 147, 'IRLANDA': 415,
    'TERRIT.VINCULADOS A PORTUGAL': 148, 'ANGOLA': 149, 'SUECIA': 429, 'CABO VERDE': 150,
    'ISLAS': 150, 'MOZAMBIQUE': 151, 'ITALIA': 417, 'SEYCHELLES': 152,
    'DJIBOUTI': 153, 'COMORAS': 155, 'GUINEA BISSAU': 156, 'STO.TOME Y PRINCIPE': 157,
    'NAMIBIA': 158, 'SUDAFRICA': 159, 'ERITREA': 160, 'ETIOPIA': 161,
    'RESTO (AFRICA)': 197, 'INDETERMINADO (AFRICA)': 198, 'INDETERMINADO AFRICA)': 198, 'BARBADOS': 201,
    'BOLIVIA': 202, 'BRASIL': 203, 'CANADA': 204, 'COSTA RICA': 206,
    'CUBA': 207, 'CHILE': 208, 'DOMINICANA,REP.': 209, 'ECUADOR': 210,
    'EL SALVADOR': 211, 'GUATEMALA': 213, 'GUYANA': 214, 'HAITI': 215,
    'HONDURAS': 216, 'JAMAICA': 217, 'MEXICO': 218, 'NICARAGUA': 219,
    'PANAMA': 220, 'PARAGUAY': 221, 'PERU': 222, 'PUERTO RICO': 223,
    'ESTADO ASOCIADO': 223, 'TRINIDAD Y -TOBAGO': 224, 'TRINIDAD Y TOBAGO': 224, 'URUGUAY': 225,
    'VENEZUELA': 226, 'TERRIT.VINCULADO AL R.UNIDO': 227, 'AMERICA': 227, 'TER.VINCULADOS A DINAMARCA': 228,
    'TERRIT.VINCULADOS A FRANCIA AMERIC.': 229, 'TERRIT. HOLANDESES': 230, 'TER.VINCULADOS A ESTADOS UNIDOS': 231, 'SURINAME': 232,
    'DOMINICA': 233, 'SANTA LUCIA': 234, 'SAN VICENTE Y LAS GRANADINS': 235, 'SAN VICENTE Y LAS GRANADINAS': 235,
    'BELICE': 236, 'ANTIGUA Y BARBUDA': 237, 'S.CRISTOBAL Y NEVIS': 238, 'BAHAMAS': 239,
    'GRANADA': 240, 'ANTILLAS HOLANDESAS': 241, 'TERRI.VINC.A PAISES BAJOS': 241, 'ARUBA': 242,
    'TIERRA DEL FUEGO': 250, '(AAE)': 250, 'ZF LA PLATA': 251, 'BUENOS AIRES': 251,
    'ZF JUSTO DARACT': 252, 'SAN LUIS': 252, 'ZF RIO GALLEGOS': 253, 'SANTA CRUZ': 253,
    'ISLAS MALVINAS': 254, 'ZF TUCUMAN': 255, 'TUCUMAN': 255, 'ZF CORDOBA': 256,
    'CORDOBA': 256, 'ZF MENDOZA': 257, 'MENDOZA': 257, 'ZF GENERAL PICO': 258,
    'LA PAMPA': 258, 'ZF COMODORO RIVADAVIA': 259, 'CHUBUT': 259, 'ZF IQUIQUE': 260,
    'ZF PUNTA ARENAS': 261, 'ZF SALTA': 262, 'SALTA': 262, 'ZF PASO DE LOS LIBRES': 263,
    'CORRIENTES': 263, 'ZF PUERTO IGUAZU': 264, 'MISIONES': 264, 'SECTOR ANTARTICO ARG.': 265,
    'ZF COLON': 270, 'ZF WINNER (STA. C.DE LA SIERRA': 271, 'ZF COLONIA': 280, 'ZF FLORIDA': 281,
    'ZF LIBERTAD': 282, 'ZF ZONAMERICA': 283, 'EX MONTEVIDEO URUGUAY': 283, 'ZF NUEVA HELVECIA': 284,
    'ZF NUEVA PALMIRA': 285, 'ZF RIO NEGRO': 286, 'ZF RIVERA': 287, 'ZF SAN JOSE': 288,
    'ZF MANAOS': 291, 'MAR ARG ZONA ECO.EX': 295, 'RIOS ARG NAVEG INTER': 296, 'RESTO AMERICA': 297,
    'INDETERMINADO.(AMERICA)': 298, 'AFGANISTAN': 301, 'ARABIA SAUDITA': 302, 'BAHREIN': 303,
    'MYANMAR(EX-BIRMANIA)': 304, 'BUTAN': 305, 'CAMBODYA(EX-KAMPUCHE': 306, 'SRI LANKA': 307,
    'COREA DEMOCRATICA': 308, 'COREA REPUBLICANA': 309, 'CHINA': 310, 'CHIPRE': 311,
    'FILIPINAS': 312, 'GAZA': 314, 'IRAK': 317, 'IRAN': 318,
    'ISRAEL': 319, 'JAPON': 320, 'JORDANIA': 321, 'QATAR': 322,
    'KUWAIT': 323, 'LAOS': 324, 'LIBANO': 325, 'MALASIA': 326,
    'MALDIVAS ISLAS': 327, 'OMAN': 328, 'MONGOLIA': 329, 'NEPAL': 330,
    'EMIRATOS ARABES,UNID': 331, 'PAKISTAN': 332, 'SINGAPUR': 333, 'SIRIA': 334,
    'THAILANDIA': 335, 'TURQUIA': 336, 'VIETNAM': 337, 'HONG KONG': 341,
    'REG.ADM.ESP. DE CHINA': 341, 'MACAO': 344, 'MACAO(REG.ADM.ESPEC)': 344, 'BANGLADESH': 345,
    'BRUNEI': 346, 'REPUBLICA DE YEMEN': 348, 'ARMENIA': 349, 'AZERBAIJAN': 350,
    'GEORGIA': 351, 'KAZAJSTAN': 352, 'KIRGUIZISTAN': 353, 'TAYIKISTAN': 354,
    'TURKMENISTAN': 355, 'UZBEKISTAN': 356, 'TERR. AU. PALESTINOS': 357, 'GAZA Y JERICO': 357,
    'TIMOR ORIENTAL': 358, 'RESTO DE ASIA': 397, 'INDET.(ASIA)': 398, 'ALBANIA': 401,
    'ALEMANIA FEDERAL': 402, 'ALEMANIA ORIENTAL': 403, 'ANDORRA': 404, 'BELGICA': 406,
    'BULGARIA': 407, 'CHECOSLOVAQUIA': 408, 'GRECIA': 413, 'HUNGRIA': 414,
    'ISLANDIA': 416, 'LIECHTENSTEIN': 418, 'LUXEMBURGO': 419, 'MALTA': 420,
    'MONACO': 421, 'NORUEGA': 422, 'POLONIA': 424, 'PORTUGAL': 425,
    'RUMANIA': 427, 'SAN MARINO': 428, 'SUIZA': 430, 'VATICANO(SANTA SEDE)': 431,
    'VATICANO(SENTA SEDE)': 431, 'YUGOSLAVIA': 432, 'POS.BRIT.(EUROPA)': 433, 'HOLANDA': 434,
    'BIELORRUSIA': 439, 'ESTONIA': 440, 'LETONIA': 441, 'LITUANIA': 442,
    'MOLDAVIA': 443, 'RUSIA': 444, 'UCRANIA': 445, 'BOSNIA HERZEGOVINA': 446,
    'CROACIA': 447, 'ESLOVAQUIA': 448, 'ESLOVENIA': 449, 'MACEDONIA': 450,
    'FED. SER Y MONT YOGOE': 452, 'MONTENEGRO': 453, 'SERBIA': 454, 'RESTO EUROPA': 497,
    'INDET.(EUROPA)': 498, 'AUSTRALIA': 501, 'NAURU': 503, 'NUEVA ZELANDIA': 504,
    'VANATU': 505, 'SAMOA OCCIDENTAL': 506, 'TERRITORIO VINCULADOS A AUSTRALIA': 507, 'OCEANIA': 507,
    'TERRITORIOS VINCULADOS AL R. UNIDO': 508, 'TERRITORIOS VINCULADOS A FRANCIA': 509, 'TER VINCULADOS A NUEVA. ZELANDA': 510, 'TER. VINCULADOS A ESTADOS UNIDOS': 511,
    'FIJI, ISLAS': 512, 'PAPUA NUEVA GUINEA': 513, 'KIRIBATI, ISLAS': 514, 'MICRONESIA,EST.FEDER': 515,
    'PALAU': 516, 'TUVALU': 517, 'SALOMON,ISLAS': 518, 'TONGA': 519,
    'MARSHALL,ISLAS': 520, 'MARIANAS,ISLAS': 521, 'RESTO OCEANIA': 597, 'INDET.(OCEANIA)': 598,
    'URSS': 601, 'ANGUILA (TERRITORIO NO AUTONOMO DEL R. UNIDO)': 652, 'ANTILLAS HOLANDESAS (TERRITORIO DE PAISES BAJOS)': 659, 'ARUBA (TERRITORIO DE PAISES BAJOS)': 653,
    'ASCENCION': 662, 'BERMUDAS (TERRITORIO NO AUTONOMO DEL R UNIDO)': 663, 'CAMPIONE DITALIA': 664, 'COLONIA DE GIBRALTAR': 665,
    'GROENLANDIA': 666, 'GUAM (TERRITORIO NO AUTONOMO DE LOS ESTADO UNIDOS': 667, 'HONG KONG (TERRITORIO DE CHINA)': 668, 'ISLAS AZORES': 669,
    'ISLAS DEL CANAL (GUERNESEY, JERSEY, ALDERNEY,G.STARK, L.SARK, ETC)': 670, 'ISLAS CAIMAN (TERRITORIO NO AUTONOMO DE R UNIDO)': 671, 'ISLA CHRISTMAS': 672, 'ISLA DE COCOS O KEELING': 673,
    'ISLA DE COOK (TERRITORIO AUTONOMO ASOCIADO A NUEVA ZELANDA)': 654, 'ISLA DE MAN (TERRITORIO DEL REINO UNIDO)': 676, 'ISLA DE NORFOLK (TERRITORIO DEL R UNIDO)': 677, 'ISALAS TURKAS Y CAICOS (TERRITORIO NO AUTONOMO DEL REINO UNIDO)': 678,
    'ISLAS PACIFICO': 679, 'ISLAS DE SAN PEDRO Y MIGUELON': 680, 'ISLA QESHM': 681, 'ISLAS VIRGENES BRITANICAS (TERRITORIO NO AUTONOMO DEL REINO UNIDO)': 682,
    'ISLAS VIRGENES DE ESTADOS UNIDOS DE AMERICA': 683, 'LABUAM': 684, 'MADEIRA (TERRITORIO DE PORTUGAL)': 685, 'MONSERRAT (TERRITORIO NO AUTONOMO DEL REINO UNIDO)': 686,
    'NIUE': 687, 'PATAU': 655, 'PITCAIRN': 690, 'POLINESI FRANCESA (TERRITORIO DE ULTRAMAR DE FRANCIA)': 656,
    'REGIMEN APLICABLE A LAS SA FINANCIERAS (LEY 11073 DE LA ROU)': 693, 'SANTA ELENA': 694, 'SAMAO AMERICANA (TERRITORIO NO AUTONOMO DE LOS ESTADOS UNIDOS)': 695, 'ARCHIPIELAGO DE SVBALBARD': 696,
    'TRISTAN DACUNHA': 697, 'TRIESTE (ITALIA)': 698, 'TOKELAU': 699, 'ZONA LIBRE DE OSTRAVA (CIUDAD DE LA ATIGUA CHECOSLOVAQUIA)': 700,
    'RESTO CONTINENTE': 997, 'INDET.(CONTINENTE)': 998, 'OTROS PAISES': 999, 'LOCAL': 'BA',
    'USA': 212, 'U.S.A.': 212, 'EEUU': 212, 'EE.UU.': 212,
    'EE UU': 212, 'ESTADOS UNIDOS DE AMERICA': 212,
}

ENCABEZADOS = [
    "", "ARTICULO", "DESCRIPCION", "NCM", "Cantidad", "Precio Unitario", "TOTAL",
    "Carpeta Impo.", "07", "Marca", "ARTICULO", "Peso total", "Insumos a Consumo",
    "NORMAS", "", "Nro. Linea", "V.INSUMO", "Carpeta Impo.", "DJO", "FECHA",
]

ROJO = PatternFill("solid", start_color="FF9999", end_color="FF9999")


# =====================================================================
# UTILIDADES
# =====================================================================
def norm_txt(x):
    s = unicodedata.normalize("NFD", str(x or "").upper())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return " ".join(s.replace("\xa0", " ").split())


def norm_parte(x):
    """'Parte 1B' / 'Part 1B' / 'P1B' / 'Parte 1 B' / 'Parte 2:' -> '1B'"""
    s = norm_txt(x).replace(":", "")
    s = re.sub(r"^(PARTE|PART|P)\s*", "", s)
    return s.replace(" ", "")


def a_int(x):
    try:
        return int(float(str(x).strip()))
    except (ValueError, TypeError):
        return None


def a_num_ar(s):
    """'1.112,45' -> 1112.45"""
    s = str(s).strip()
    if not re.fullmatch(r"[\d.]+,\d+|\d+", s):
        return None
    return float(s.replace(".", "").replace(",", "."))


def a_float(x):
    if isinstance(x, (int, float)) and not isinstance(x, bool):
        return float(x)
    s = str(x or "").strip().replace("\xa0", "")
    try:
        return float(s.replace(",", "."))
    except ValueError:
        return None


# =====================================================================
# LECTORES
# =====================================================================
def leer_picking(file_bytes):
    """Devuelve lista de kits [{kit, cantidad, materiales:set, lotes:set[(material, lote)]}] en orden.
    Un mismo kit puede aparecer más de una vez (con distinto Kit Quant)."""
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    kits = []
    actual = None
    for page in doc:
        spans = []
        for b in page.get_text("dict")["blocks"]:
            for l in b.get("lines", []):
                for s in l["spans"]:
                    t = s["text"].strip()
                    if t:
                        bold = bool(s["flags"] & 16) or "BOLD" in s["font"].upper()
                        spans.append((s["bbox"][0], s["bbox"][1], t, bold))
        spans.sort(key=lambda z: (round(z[1]), z[0]))
        for x, y, t, bold in spans:
            if not re.fullmatch(r"\d{7}", t) or x > 90:
                continue
            misma = [z for z in spans if abs(z[1] - y) < 3 and z[0] > x]
            if bold and any(z[2].upper().startswith("KIT") for z in misma):
                cant = None
                for z in misma:
                    if z[3] and 230 < z[0] < 300 and re.fullmatch(r"\d+", z[2]):
                        cant = int(z[2])
                actual = {"kit": int(t), "cantidad": cant, "materiales": set(), "lotes": set()}
                kits.append(actual)
            elif not bold and actual is not None:
                actual["materiales"].add(int(t))
                lote = next((z[2] for z in misma if re.fullmatch(r"\d{10}", z[2])), None)
                if lote:
                    actual["lotes"].add((int(t), lote))
    return kits


def leer_factura(file_bytes):
    """Devuelve la lista de renglones de PARTES (sin cajas), en orden de aparición:
    {codigo, parte, pu, st, qt, usado}"""
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    if "PRO-FORMA" in norm_txt(doc[0].get_text()):
        return leer_proforma(doc)
    renglones = []
    for page in doc:
        words = page.get_text("words")
        x_pu = next((w[2] for w in words if w[4] == "Unitario"), 433)
        x_st = next((w[2] for w in words if w[4] == "Subtotal"), 563)
        x_qt = next((w[2] for w in words if w[4] == "Cantidad"), 325)
        for w in words:
            if w[0] < 70 and re.fullmatch(r"\d{7}", w[4]):
                linea = sorted([z for z in words if abs(z[1] - w[1]) < 3], key=lambda z: z[0])
                desc = " ".join(z[4] for z in linea if w[2] < z[0] < x_qt - 40)
                if norm_txt(desc).startswith("CAJA"):
                    continue
                pu = next((a_num_ar(z[4]) for z in linea
                           if abs(z[2] - x_pu) < 15 and a_num_ar(z[4]) is not None), None)
                st_ = next((a_num_ar(z[4]) for z in linea
                            if abs(z[2] - x_st) < 15 and a_num_ar(z[4]) is not None), None)
                qt = next((a_num_ar(z[4]) for z in linea
                           if abs(z[2] - x_qt) < 20 and re.fullmatch(r"[\d.]+", z[4])), None)
                m = re.match(r"(?:PARTE|PART)\s*(\d+[A-Z]?)", norm_txt(desc))
                if pu is not None or st_ is not None:
                    renglones.append({"codigo": int(w[4]), "parte": m.group(1) if m else None,
                                      "pu": pu, "st": st_, "qt": qt, "usado": False})
    return renglones


def leer_proforma(doc):
    """Factura Pro-Forma: cada ítem viene como bloque de líneas
    código / descripción / Peso Neto / Peso Bruto / cantidad / EA / empaque / P.Unitario / subtotal.
    Se usa el subtotal impreso (validado contra cantidad x P.Unitario)."""
    lineas = []
    for page in doc:
        lineas += [l.strip() for l in page.get_text().split("\n")]
    num = re.compile(r"^[\d.]+(,\d+)?$")
    renglones = []
    i = 0
    while i < len(lineas):
        if not re.fullmatch(r"\d{7}", lineas[i]):
            i += 1
            continue
        codigo = int(lineas[i])
        j = i + 1
        desc = []
        while j < len(lineas) and not lineas[j].upper().startswith("PESO") and not num.match(lineas[j]):
            desc.append(lineas[j])
            j += 1
        while j < len(lineas) and lineas[j].upper().startswith("PESO"):
            j += 1
        bloque = lineas[j:j + 5]  # cantidad, UM, empaque, P.Unitario, subtotal
        i = j
        if len(bloque) < 4 or not num.match(bloque[0]) or not num.match(bloque[3]):
            continue
        qt, pu = a_num_ar(bloque[0]), a_num_ar(bloque[3])
        descripcion = norm_txt(" ".join(desc))
        if descripcion.startswith("CAJA"):
            continue
        m = re.match(r"(?:PARTE|PART)\s*(\d+[A-Z]?)", descripcion)
        st_ = round(qt * pu, 2) if qt is not None and pu is not None else None
        if len(bloque) >= 5 and num.match(bloque[4]):
            impreso = a_num_ar(bloque[4]) if "," in bloque[4] else float(bloque[4].replace(".", ""))
            if st_ is None or abs(impreso - st_) < 1:
                st_ = impreso
        renglones.append({"codigo": codigo, "parte": m.group(1) if m else None,
                          "pu": pu, "st": st_, "qt": qt, "usado": False})
    return renglones


def leer_origenes(file_bytes):
    ws = load_workbook(io.BytesIO(file_bytes), data_only=True).active
    # Celdas combinadas: se replica el valor en todas las filas del rango
    # (salvo la columna B "Sabor", que marca el inicio de cada bloque de kit)
    for rango in list(ws.merged_cells.ranges):
        if rango.min_col == 2 and rango.max_col == 2:
            continue
        valor = ws.cell(rango.min_row, rango.min_col).value
        ws.unmerge_cells(str(rango))
        for fila in range(rango.min_row, rango.max_row + 1):
            for col in range(rango.min_col, rango.max_col + 1):
                ws.cell(fila, col).value = valor
    filas = []
    kit_actual = None
    bloque = 0
    for r in ws.iter_rows(min_row=2, values_only=True):
        r = list(r) + [None] * 14
        mat = a_int(r[0])
        if mat is None:
            continue
        nums = re.findall(r"\b\d{7}\b", str(r[1] or ""))
        if nums:
            kit_actual = int(nums[-1])
            bloque += 1
        filas.append({
            "material": mat, "kit_origen": kit_actual, "bloque": bloque,
            "lote": str(r[7] or "").strip(),
            "parte": " ".join(str(r[2] or "").split()),
            "denominacion": " ".join(str(r[3] or "").split()),
            "caja": a_int(r[4]), "cantidad": r[8], "origen": " ".join(str(r[10] or "").split()),
            "peso_total": r[12],
        })
    return filas


def leer_exportaciones(file_bytes):
    wb = load_workbook(io.BytesIO(file_bytes), data_only=True, read_only=True)
    ws = wb["Precio por Parte"] if "Precio por Parte" in wb.sheetnames else wb.worksheets[0]
    idx = {}
    for r in ws.iter_rows(min_row=2, values_only=True):
        r = list(r) + [None] * 12
        kit = a_int(r[0])
        if kit is None or r[3] is None:
            continue
        clave = (kit, norm_parte(r[3]))
        if clave not in idx:
            idx[clave] = {
                "ident": str(r[2] or "").replace("\xa0", " ").strip(),
                "ncm": str(r[5] or "").replace("\xa0", "").replace(" ", "").strip(),
                "valor": a_float(r[11]),
            }
    return idx


def leer_djo(file_bytes):
    wb = load_workbook(io.BytesIO(file_bytes), data_only=True, read_only=True)
    idx = {}
    for ws in wb.worksheets:
        for r in ws.iter_rows(min_row=2, values_only=True):
            r = list(r) + [None] * 4
            txt = str(r[0] or "").replace("\xa0", " ")
            m = re.match(r"\s*(\d{7})\s*/\s*(\d{7})\s*/?\s*(.+)", txt)
            if not m:
                continue
            clave = (int(m.group(1)), int(m.group(2)), norm_parte(m.group(3)))
            fecha = r[3] if isinstance(r[3], datetime) else None
            reg = {"normas": r[1], "nro": r[2], "fecha": fecha}
            prev = idx.get(clave)
            if prev is None or (fecha and (prev["fecha"] is None or fecha > prev["fecha"])):
                idx[clave] = reg
    return idx


# =====================================================================
# ARMADO DEL LOTE
# =====================================================================
def armar_lote(origenes, kits, factura, export, djo):
    avisos = []

    # 1) Resolver a qué kit del Picking (kit + Kit Quant) pertenece cada fila de Orígenes.
    #    Si el kit aparece más de una vez en el Picking, se decide por caja/bidón + lote;
    #    si no alcanza, por el orden de los bloques del kit en Orígenes.
    bloques_por_kit = defaultdict(list)
    for o in origenes:
        if o["bloque"] not in bloques_por_kit[o["kit_origen"]]:
            bloques_por_kit[o["kit_origen"]].append(o["bloque"])

    for o in origenes:
        occ = [i for i, k in enumerate(kits) if k["kit"] == o["kit_origen"]]
        if not occ:
            occ = [i for i, k in enumerate(kits) if o["caja"] in k["materiales"]]
            if not occ:
                avisos.append(f"Material {o['material']}: kit no encontrado en el Picking List.")
        if len(occ) > 1:
            por_lote = [i for i in occ if (o["caja"], o["lote"]) in kits[i]["lotes"]]
            if len(por_lote) == 1:
                occ = por_lote
            else:
                n = bloques_por_kit[o["kit_origen"]].index(o["bloque"])
                occ = [occ[min(n, len(occ) - 1)]]
        o["occ"] = occ[0] if occ else None
        o["kit"] = kits[o["occ"]]["kit"] if occ else o["kit_origen"]

    # 2) Unificar: mismo kit + mismo Kit Quant + mismo material + misma parte -> una línea (suma E y L)
    grupos = {}
    for o in origenes:
        clave = (o["occ"], o["kit"], o["material"], norm_parte(o["parte"]))
        if clave in grupos:
            g = grupos[clave]
            g["cantidad"] = (a_float(g["cantidad"]) or 0) + (a_float(o["cantidad"]) or 0)
            g["peso_total"] = (a_float(g["peso_total"]) or 0) + (a_float(o["peso_total"]) or 0)
            g["unificadas"] += 1
        else:
            grupos[clave] = dict(o, unificadas=1)
    unificadas = [g for g in grupos.values() if g["unificadas"] > 1]
    for g in unificadas:
        avisos.append(f"{g['material']} {g['kit']} {g['parte']}: se unificaron {g['unificadas']} filas de Orígenes.")

    # 3) Armar las filas del LOTE
    filas = []
    kit_prev, nro_kit = None, 0
    # Mantener juntas las líneas de cada kit (kit + Kit Quant), respetando el orden de Orígenes
    orden_occ = {}
    for o in grupos.values():
        orden_occ.setdefault((o["occ"], o["kit"]), len(orden_occ))
    lineas = sorted(grupos.values(), key=lambda o: orden_occ[(o["occ"], o["kit"])])

    for o in lineas:
        kit = o["kit"]
        kit_info = kits[o["occ"]] if o["occ"] is not None else {}

        col_a = None
        if (o["occ"], kit) != kit_prev:
            nro_kit += 1
            col_a = nro_kit
            kit_prev = (o["occ"], kit)

        articulo = f"{o['material']} {kit or ''} {o['parte']}".strip()
        exp = export.get((kit, norm_parte(o["parte"])), {})
        if not exp:
            avisos.append(f"{articulo}: sin coincidencia en Exportaciones (NCM/Marca/V.Insumo en blanco).")

        # Factura: renglones del material (en orden) hasta cubrir la cantidad de Orígenes.
        # Si el código no figura, se busca un renglón libre con la misma parte y cantidad.
        pu, st_ = None, None
        objetivo = a_float(o["cantidad"])
        for r in factura:
            r.setdefault("resto", r["qt"])
        libres = [r for r in factura if not r["usado"] and r["codigo"] == o["material"]]
        if not libres and not any(r["codigo"] == o["material"] for r in factura):
            libres = [r for r in factura if not r["usado"] and r["parte"] == norm_parte(o["parte"])
                      and objetivo is not None and r["qt"] is not None and abs(r["qt"] - objetivo) < 1e-6]
            if libres:
                avisos.append(f"{articulo}: el código no figura en la Factura; se tomó el renglón "
                              f"{libres[0]['codigo']} (misma parte y cantidad). Verificar.")
        if libres:
            acum = 0.0
            for r in libres:
                if pu is None:
                    pu = r["pu"]
                falta = None if objetivo is None else objetivo - acum
                if falta is not None and r["resto"] and r["resto"] > falta + 1e-6 and r["pu"] is not None:
                    # El renglón de la Factura cubre más de lo necesario: se toma solo una parte
                    st_ = (st_ or 0) + falta * r["pu"]
                    r["resto"] -= falta
                    acum += falta
                    break
                r["usado"] = True
                parcial = r["resto"] is not None and r["qt"] and r["resto"] < r["qt"] - 1e-6
                st_ = (st_ or 0) + ((r["resto"] * r["pu"]) if parcial and r["pu"] is not None else (r["st"] or 0))
                acum += r["resto"] or 0
                if objetivo is None or r["qt"] is None or acum >= objetivo - 1e-6:
                    break
            if objetivo is not None and acum and abs(acum - objetivo) > 1e-6:
                avisos.append(f"{articulo}: cantidad Orígenes ({objetivo:g}) ≠ Factura ({acum:g}).")
        else:
            avisos.append(f"{articulo}: no encontrado en la Factura Final.")

        origen_n = norm_txt(o["origen"])
        pais = PAISES.get(origen_n)
        if pais is None:
            pais = PAISES.get(re.sub(r"\bREP\b\.?\s*", "REPUBLICA ", origen_n).strip())
        if pais is None and origen_n:
            avisos.append(f"{articulo}: país '{o['origen']}' no encontrado en la tabla.")

        valor = exp.get("valor")
        dj = djo.get((o["material"], kit, norm_parte(o["parte"])), {})
        peso = a_float(o["peso_total"])

        filas.append({
            "A": col_a, "B": articulo, "C": o["denominacion"], "D": exp.get("ncm") or None,
            "E": int(o["cantidad"]) if isinstance(o["cantidad"], float) and o["cantidad"].is_integer() else o["cantidad"], "F": pu, "G": round(st_, 2) if st_ is not None else None,
            "H": pais, "I": 7, "J": exp.get("ident") or None, "K": articulo,
            "L": round(peso, 3) if peso is not None else o["peso_total"],
            "N": dj.get("normas"),
            "O": 1 if origen_n == "LOCAL" else (2 if origen_n else None),
            "P": kit_info.get("cantidad") if valor is not None else None,
            "Q": valor, "R": o["origen"] or None, "S": dj.get("nro"), "T": dj.get("fecha"),
        })

    sobrantes = [r["codigo"] for r in factura if not r["usado"] and (r["pu"] or 0) > 0]
    return filas, avisos, sobrantes


def generar_excel(filas):
    wb = Workbook()
    ws = wb.active
    ws.title = "Hoja1"
    fuente = Font(name="Arial", size=10)
    negrita = Font(name="Arial", size=10, bold=True)
    borde = Border(*(Side(style="thin", color="BFBFBF"),) * 4)

    for i, h in enumerate(ENCABEZADOS, start=1):
        c = ws.cell(row=1, column=i, value=h or None)
        c.font = negrita
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        c.fill = PatternFill("solid", start_color="D9E1F2", end_color="D9E1F2")

    for n, f in enumerate(filas, start=2):
        for col in "ABCDEFGHIJKLNOPQRST":
            ws[f"{col}{n}"] = f.get(col)
        ws[f"M{n}"] = f'=IF(AND(ISNUMBER(P{n}),ISNUMBER(Q{n})),P{n}*Q{n},"")'
        for col in range(1, 21):
            c = ws.cell(row=n, column=col)
            c.font = fuente
            c.border = borde
        ws[f"F{n}"].number_format = "#,##0.00"
        ws[f"G{n}"].number_format = "#,##0.00"
        ws[f"L{n}"].number_format = "#,##0.000"
        ws[f"M{n}"].number_format = "#,##0.00"
        ws[f"Q{n}"].number_format = "#,##0.00"
        ws[f"T{n}"].number_format = "DD/MM/YYYY"
        if f.get("H") != "BA":
            ws[f"H{n}"].fill = ROJO

    anchos = {"A": 5, "B": 26, "C": 42, "D": 18, "E": 10, "F": 13, "G": 13, "H": 12,
              "I": 6, "J": 16, "K": 26, "L": 11, "M": 14, "N": 9, "O": 4, "P": 10,
              "Q": 11, "R": 12, "S": 8, "T": 12}
    for col, w in anchos.items():
        ws.column_dimensions[col].width = w
    ws.freeze_panes = "B2"

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


# =====================================================================
# INTERFAZ
# =====================================================================
st.title("📦 Armado de LOTE — Coca-Cola")
st.caption("Genera el Excel LOTE a partir de Orígenes, Picking List, Factura Final, Exportaciones y DJO.")

referencia = st.text_input("Referencia (nombre del archivo de salida)", placeholder="Ej: 26001EC01000123A").strip()
ref_archivo = re.sub(r'[\\/:*?"<>|]+', "-", referencia)

c1, c2 = st.columns(2)
with c1:
    f_orig = st.file_uploader("Orígenes (Excel)", type=["xlsx"])
    f_pick = st.file_uploader("Picking List (PDF)", type=["pdf"])
    f_fact = st.file_uploader("Factura Final (PDF)", type=["pdf"])
with c2:
    f_expo = st.file_uploader("Exportaciones - Descripción y NCM (Excel)", type=["xlsx"])
    f_djo = st.file_uploader("DJO (Excel)", type=["xlsx"])

faltan = [n for n, f in [("Orígenes", f_orig), ("Picking List", f_pick), ("Factura Final", f_fact),
                          ("Exportaciones", f_expo), ("DJO", f_djo)] if not f]
if not referencia:
    faltan.append("Referencia")
if faltan:
    st.info("Falta completar: " + ", ".join(faltan))

if st.button("Generar LOTE", type="primary", use_container_width=True, disabled=bool(faltan)):
    with st.spinner("Procesando documentos..."):
        try:
            origenes = leer_origenes(f_orig.getvalue())
            kits = leer_picking(f_pick.getvalue())
            factura = leer_factura(f_fact.getvalue())
            export = leer_exportaciones(f_expo.getvalue())
            djo = leer_djo(f_djo.getvalue())
            filas, avisos, sobrantes = armar_lote(origenes, kits, factura, export, djo)
            st.session_state["lote_filas"] = filas
            st.session_state["lote_avisos"] = avisos
            st.session_state["lote_sobrantes"] = sobrantes
            st.session_state["lote_kits"] = kits
        except Exception as e:
            st.error(f"Error al procesar: {e}")

if st.session_state.get("lote_filas"):
    filas = st.session_state["lote_filas"]
    kits = st.session_state["lote_kits"]
    avisos = st.session_state["lote_avisos"]
    sobrantes = st.session_state["lote_sobrantes"]

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Partes", len(filas))
    m2.metric("Kits", len(kits))
    m3.metric("Total factura (partes)", f"{sum(f['G'] or 0 for f in filas):,.2f}")
    m4.metric("Con DJO", sum(1 for f in filas if f.get("S")))

    df = pd.DataFrame(filas)
    df["M"] = [(f["P"] * f["Q"]) if f["P"] is not None and f["Q"] is not None else None for f in filas]
    df = df[list("ABCDEFGHIJKLMNOPQRST")]
    st.dataframe(df, use_container_width=True, hide_index=True)

    if sobrantes:
        avisos = avisos + [f"Código {c} de la Factura (con precio) no se usó en ninguna fila de Orígenes."
                           for c in sobrantes]
    if avisos:
        with st.expander(f"⚠️ Avisos ({len(avisos)})"):
            for a in avisos:
                st.write("• " + a)

    st.download_button(
        f"⬇️ Descargar LOTE_{ref_archivo}.xlsx" if ref_archivo else "⬇️ Descargar LOTE (falta referencia)",
        data=generar_excel(filas),
        file_name=f"LOTE_{ref_archivo}.xlsx" if ref_archivo else "LOTE.xlsx",
        disabled=not ref_archivo,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        type="primary",
        use_container_width=True,
    )
