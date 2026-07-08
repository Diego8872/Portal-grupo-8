"""
Normalización de texto y lógica de cruce DJ SENASA vs DI.
"""

import unicodedata
import re

from .constants import get_rules_for_aduana


def normalize(text):
    """Mayúsculas, sin acentos, sin espacios/puntuación redundante."""
    if text is None:
        return ""
    text = str(text).upper().strip()
    text = "".join(
        c for c in unicodedata.normalize("NFKD", text) if not unicodedata.combining(c)
    )
    text = re.sub(r"[^A-Z0-9]+", " ", text).strip()
    return text


def merge_di_sources(di_excel: dict, di_pdf: dict) -> dict:
    """
    Combina los datos de DI Excel (prioritario) y DI PDF (fallback),
    campo por campo. Devuelve un dict con el mismo shape que ambos
    parsers más 'origen_dato' indicando de dónde salió cada campo.
    """
    fields = ["aduana", "pais_origen", "pais_procedencia", "deposito", "referencia"]
    merged = {}
    fuente = {}
    for f in fields:
        val_excel = (di_excel or {}).get(f)
        val_pdf = (di_pdf or {}).get(f)
        if val_excel:
            merged[f] = val_excel
            fuente[f] = "Excel"
        elif val_pdf:
            merged[f] = val_pdf
            fuente[f] = "PDF"
        else:
            merged[f] = None
            fuente[f] = None
    merged["_fuente"] = fuente
    return merged


def _check(nombre, valor_dj, valor_esperado, detalle_esperado=None):
    ok = normalize(valor_dj) == normalize(valor_esperado) and valor_dj is not None
    return {
        "campo": nombre,
        "valor_dj": valor_dj,
        "valor_esperado": valor_esperado,
        "detalle_esperado": detalle_esperado,
        "ok": bool(ok),
    }


def _check_deposito(nombre, valor_dj, valor_di, equivalencias):
    """
    Compara Lugar de destino (DJ) vs Depósito (DI) usando la tabla de
    equivalencias de la aduana (mismo lugar físico, nombre distinto en
    cada documento). Si el valor de la DJ no está en la tabla, compara
    texto exacto como respaldo.
    """
    dj_norm = normalize(valor_dj)
    di_norm = normalize(valor_di)

    ok = False
    for eq in equivalencias:
        if normalize(eq["dj"]) == dj_norm:
            ok = di_norm in [normalize(d) for d in eq["di"]]
            break
    else:
        ok = dj_norm == di_norm and valor_dj is not None

    return {
        "campo": nombre,
        "valor_dj": valor_dj,
        "valor_esperado": valor_di,
        "detalle_esperado": "Depósito declarado en la DI",
        "ok": bool(ok),
    }


def validate(dj_data: dict, di_data: dict) -> dict:
    """
    Compara la DJ SENASA contra la DI y devuelve:
      {
        "aduana_key": "EZEIZA" | "BUENOS AIRES" | None,
        "checks": [ {campo, valor_dj, valor_esperado, detalle_esperado, ok}, ... ],
        "aduana_reconocida": bool,
      }
    """
    from .constants import DEPOSITO_EQUIVALENCIAS

    aduana_texto = di_data.get("aduana")
    aduana_key, rules = get_rules_for_aduana(aduana_texto)

    checks = []

    if rules is None:
        return {
            "aduana_key": None,
            "aduana_texto": aduana_texto,
            "aduana_reconocida": False,
            "checks": checks,
        }

    # 1. Punto de ingreso (constante)
    checks.append(
        _check("Punto de ingreso", dj_data.get("punto_ingreso"), rules["puerto_ingreso"])
    )

    # 2. Medio de transporte (constante)
    checks.append(
        _check("Medio de transporte", dj_data.get("medio_transporte"), rules["medio_transporte"])
    )

    # 3. Lugar de destino: constante o cruce contra Depósito de la DI
    #    (usando la tabla de equivalencias, porque no siempre coincide el texto)
    if rules["lugar_destino"] is not None:
        checks.append(
            _check("Lugar de destino de la mercadería", dj_data.get("lugar_destino"), rules["lugar_destino"])
        )
    else:
        equivalencias = DEPOSITO_EQUIVALENCIAS.get(aduana_key, [])
        checks.append(
            _check_deposito(
                "Lugar de destino de la mercadería",
                dj_data.get("lugar_destino"),
                di_data.get("deposito"),
                equivalencias,
            )
        )

    # 4. País de procedencia (DJ vs DI)
    checks.append(
        _check(
            "País de procedencia",
            dj_data.get("pais_procedencia"),
            di_data.get("pais_procedencia"),
            detalle_esperado="Según DI",
        )
    )

    # 5. País de origen (DJ vs DI)
    checks.append(
        _check(
            "País de origen",
            dj_data.get("pais_origen"),
            di_data.get("pais_origen"),
            detalle_esperado="Según DI",
        )
    )

    return {
        "aduana_key": aduana_key,
        "aduana_texto": aduana_texto,
        "aduana_reconocida": True,
        "checks": checks,
    }
