"""
Genera el reporte de la revisión en PDF, para descargar desde la app.
"""

import io
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

OK_COLOR = colors.HexColor("#1a7f37")
ERROR_COLOR = colors.HexColor("#c0392b")


def build_report_pdf(resultado: dict, di_data: dict) -> bytes:
    """
    Arma el PDF del reporte a partir del resultado de validate() y los
    datos combinados de la DI. Devuelve los bytes del PDF.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "TitleCustom", parent=styles["Title"], fontSize=18, spaceAfter=4
    )
    subtitle_style = ParagraphStyle(
        "SubtitleCustom", parent=styles["Normal"], fontSize=10, textColor=colors.grey
    )

    elements = []
    elements.append(Paragraph("Corrector SENASA — Reporte de revisión", title_style))

    referencia = di_data.get("referencia") or "sin datos"
    fecha = datetime.now().strftime("%d/%m/%Y %H:%M")
    elements.append(
        Paragraph(
            f"Referencia despacho: {referencia} &nbsp;&nbsp;|&nbsp;&nbsp; "
            f"Aduana: {resultado.get('aduana_key') or '-'} &nbsp;&nbsp;|&nbsp;&nbsp; "
            f"Generado: {fecha}",
            subtitle_style,
        )
    )
    elements.append(Spacer(1, 0.6 * cm))

    checks = resultado["checks"]
    errores = [c for c in checks if not c["ok"]]

    resumen_style = ParagraphStyle(
        "Resumen",
        parent=styles["Normal"],
        fontSize=11,
        textColor=ERROR_COLOR if errores else OK_COLOR,
        spaceAfter=10,
    )
    if errores:
        resumen_txt = f"⚠ Se encontraron {len(errores)} de {len(checks)} campos con diferencias."
    else:
        resumen_txt = f"✔ Los {len(checks)} campos revisados coinciden correctamente."
    elements.append(Paragraph(resumen_txt, resumen_style))

    # --- Tabla de detalle ---
    header = ["Campo", "DJ SENASA", "Esperado / DI", "Resultado"]
    data_rows = [header]
    for c in checks:
        data_rows.append(
            [
                Paragraph(c["campo"], styles["Normal"]),
                Paragraph(c["valor_dj"] or "(no detectado)", styles["Normal"]),
                Paragraph(c["valor_esperado"] or "(no detectado)", styles["Normal"]),
                "OK" if c["ok"] else "ERROR",
            ]
        )

    table = Table(data_rows, colWidths=[3.8 * cm, 5 * cm, 5 * cm, 2.2 * cm])
    style_cmds = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f0f0f0")),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#dddddd")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
    ]
    for i, c in enumerate(checks, start=1):
        color = OK_COLOR if c["ok"] else ERROR_COLOR
        style_cmds.append(("TEXTCOLOR", (3, i), (3, i), color))
        style_cmds.append(("FONTNAME", (3, i), (3, i), "Helvetica-Bold"))
    table.setStyle(TableStyle(style_cmds))
    elements.append(table)

    elements.append(Spacer(1, 0.8 * cm))
    elements.append(
        Paragraph(
            "Reporte generado automáticamente por el Corrector SENASA. "
            "Verificar siempre contra la documentación original.",
            subtitle_style,
        )
    )

    doc.build(elements)
    return buffer.getvalue()
