"""Configuración de los tres tipos de control INAL.

Para agregar un tipo nuevo o cambiar un dato fijo, solo se edita este archivo.
"""
from dataclasses import dataclass

_EZEIZA = [
    ("Provincia", "BUENOS AIRES"),
    ("Departamento", "EZEIZA"),
    ("Localidad", "CARLOS SPEGAZZINI"),
    ("Domicilio", "PUENTE DEL INCA 2450"),
]


@dataclass(frozen=True)
class Tipo:
    nombre: str
    fijos: list          # [(campo, valor)] datos que siempre son iguales y no están en la documentación
    aval_sanitario: bool  # si el tipo controla "País de Aval Sanitario"


TIPOS = {
    "345": Tipo(
        nombre="INAL 345",
        fijos=[
            ("RNE importador", "01000411"),
            ("RNE elaborador", "01000411"),
            ("Provincia", "CIUDAD DE BUENOS AIRES"),
            ("Departamento", "COMUNA 15"),
            ("Localidad", "PATERNAL"),
            ("Domicilio", "LUIS VIALE 2045"),
        ],
        aval_sanitario=False,
    ),
    "Autorización": Tipo(
        nombre="INAL Autorización",
        fijos=[("RNE importador", "00038636"), ("RNE elaborador", "01000411")] + _EZEIZA,
        aval_sanitario=False,
    ),
    "Aviso": Tipo(
        nombre="INAL Aviso",
        fijos=[("RNE elaborador", "01000411")] + _EZEIZA,
        aval_sanitario=True,
    ),
}

# Campo fijo -> clave del parser del PD
CLAVE_PD = {
    "RNE importador": "rne_importador",
    "RNE elaborador": "rne_elaborador",
    "Provincia": "provincia",
    "Departamento": "departamento",
    "Localidad": "localidad",
    "Domicilio": "domicilio",
}
