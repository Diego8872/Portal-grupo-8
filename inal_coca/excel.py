"""Genera el Excel de resultado: Campo / PD / Documento fuente / Resultado."""
import io

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side

from .compare import ERROR, OK

_ESTILO = {  # estado: (texto inicial, color de relleno, color de letra)
    OK: ("✅ Coincide", "C6EFCE", "006100"),
    ERROR: ("❌ No coincide", "FFC7CE", "9C0006"),
    "revisar": ("⚠️ Revisar", "FFEB9C", "7F6000"),
}


def texto_resultado(f) -> str:
    base = _ESTILO[f.estado][0]
    if f.estado == OK:
        return f"{base} – {f.detalle}" if f.detalle else base
    return f"{base}: {f.detalle}" if f.detalle else base


def generar_excel(res: dict) -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.title = f"Control {res['tipo']}"[:31]
    borde = Border(*(Side(style="thin", color="BFBFBF"),) * 4)
    ws.append(["Campo", "PD", "Documento fuente", "Resultado"])
    for c in ws[1]:
        c.font = Font(bold=True, color="FFFFFF")
        c.fill = PatternFill("solid", fgColor="1F3864")
        c.alignment = Alignment(horizontal="center", vertical="center")
        c.border = borde
    for f in res["filas"]:
        ws.append([f.campo, f.pd or "—", f.fuente or "—", texto_resultado(f)])
        _, relleno, letra = _ESTILO[f.estado]
        celda = ws.cell(ws.max_row, 4)
        celda.fill = PatternFill("solid", fgColor=relleno)
        celda.font = Font(bold=True, color=letra)
        for c in ws[ws.max_row]:
            c.alignment = Alignment(wrap_text=True, vertical="top")
            c.border = borde
    for col, ancho in zip("ABCD", (38, 42, 52, 60)):
        ws.column_dimensions[col].width = ancho
    ws.freeze_panes = "A2"

    r = wb.create_sheet("Resumen")
    n = lambda e: sum(1 for f in res["filas"] if f.estado == e)
    for fila in (["Tipo de control", res["tipo"]], ["PD", res["pd_numero"] or "—"],
                 ["Material del listado", (f"{res['material']} (por {res.get('material_metodo')})" if res.get("material") else "no encontrado")],
                 ["✅ Coinciden", n(OK)], ["❌ No coinciden", n(ERROR)], ["⚠️ A revisar", n("revisar")],
                 [], ["Lectura de documentos", ""]):
        r.append(fila)
    for k, v in res["lecturas"].items():
        r.append([k, v])
    for a in res["avisos"]:
        r.append(["Aviso", a])
    r.column_dimensions["A"].width = 26
    r.column_dimensions["B"].width = 60
    for row in r.iter_rows(min_col=1, max_col=1):
        row[0].font = Font(bold=True)

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()
