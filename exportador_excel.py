import csv
from pathlib import Path
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

ENCABEZADOS = {
    "intento_id": "ID de\nIntento",
    "id_participante_hash": "ID Participante\n(Anónimo)",
    "fecha_inicio": "Fecha y Hora\nde Inicio",
    "fecha_fin": "Fecha y Hora\nde Fin",
    "completado": "¿Completó la\nencuesta?",
    "duracion_segundos": "Duración\n(segundos)",
    "pregunta_abandono": "Pregunta donde\nabandonó",
    "motivo_fin": "Estado de\nCierre",
    "q01_semestre": "P1. ¿Qué semestre\ncursas actualmente?",
    "q02_facultad": "P2. ¿A qué facultad\nperteneces?",
    "q03_dispositivo": "P3. ¿Desde qué\ndispositivo respondes?",
    "q04_uso_telegram": "P4. ¿Con qué frecuencia\nusas Telegram?",
    "q05_frecuencia_encuestas": "P5. ¿Con qué frecuencia\nrespondes encuestas\nuniversitarias?",
    "q06_disposicion": "P6. Disposición a\nresponder encuestas\n(1 a 5)",
    "q07_motivo_abandono_encuestas": "P7. ¿Cuál es tu principal\nmotivo para abandonar\nuna encuesta?",
    "q08_encuestas_faciles": "P8. ¿Qué tan fáciles son\nlas encuestas actuales?\n(1 a 5)",
    "q09_medio_preferido": "P9. ¿Qué medio prefieres\npara responder\nencuestas?",
    "q10_sugerencia": "P10. ¿Qué cambiarías para\nque más estudiantes\nrespondan? (Opcional)",
    "q11_sus_uso_frecuente": "SUS 1.\nUsaría este bot con\nfrecuencia (1-5)",
    "q12_sus_complejo": "SUS 2.\nMe pareció demasiado\ncomplejo (1-5)",
    "q13_sus_facil": "SUS 3.\nMe pareció fácil\nde usar (1-5)",
    "q14_sus_ayuda_tecnica": "SUS 4.\nNecesitaría ayuda técnica\npara usarlo (1-5)",
    "q15_sus_integradas": "SUS 5.\nLas funciones están\nbien integradas (1-5)",
    "q16_sus_inconsistencia": "SUS 6.\nNoté demasiada\ninconsistencia (1-5)",
    "q17_sus_aprendizaje_rapido": "SUS 7.\nLa mayoría aprendería\na usarlo rápido (1-5)",
    "q18_sus_incomodo": "SUS 8.\nMe pareció incómodo\nde usar (1-5)",
    "q19_sus_seguro": "SUS 9.\nMe sentí seguro\nusándolo (1-5)",
    "q20_sus_aprender_mucho": "SUS 10.\nNecesité aprender mucho\nantes de usarlo (1-5)",
    "sus_puntaje": "Puntaje Final\nSUS (0-100)",
}

COLUMNAS_NUMERICAS = {
    "duracion_segundos",
    "q01_semestre",
    "q06_disposicion",
    "q08_encuestas_faciles",
    "q11_sus_uso_frecuente",
    "q12_sus_complejo",
    "q13_sus_facil",
    "q14_sus_ayuda_tecnica",
    "q15_sus_integradas",
    "q16_sus_inconsistencia",
    "q17_sus_aprendizaje_rapido",
    "q18_sus_incomodo",
    "q19_sus_seguro",
    "q20_sus_aprender_mucho",
    "sus_puntaje",
}


def color_encabezado(col_name: str) -> PatternFill:
    if col_name.startswith("q1") and col_name != "q10_sugerencia" or col_name.startswith("q2") or col_name == "sus_puntaje":
        return PatternFill("solid", fgColor="2E5E4E")
    if col_name.startswith("q0") or col_name == "q10_sugerencia":
        return PatternFill("solid", fgColor="215967")
    return PatternFill("solid", fgColor="1F4E78")


def convertir_valor(columna: str, valor: str):
    if valor is None or valor == "":
        return ""
    if columna == "completado":
        return "Sí" if valor.strip().lower() == "true" else "No"
    if columna in {"fecha_inicio", "fecha_fin"}:
        return valor.replace("T", " ")
    if columna in COLUMNAS_NUMERICAS:
        try:
            num = float(valor)
            return int(num) if num.is_integer() and columna not in {"duracion_segundos", "sus_puntaje"} else num
        except ValueError:
            return valor
    return valor


def generar_excel_desde_csv(ruta_csv: Path) -> Path:
    ruta_xlsx = ruta_csv.with_suffix(".xlsx")

    with ruta_csv.open("r", encoding="utf-8-sig", newline="") as f:
        lector = csv.DictReader(f)
        columnas_csv = lector.fieldnames or []
        filas = list(lector)

    wb = Workbook()
    ws = wb.active
    ws.title = "Respuestas"

    fill_zebra = PatternFill("solid", fgColor="F4F7FA")
    fill_ok = PatternFill("solid", fgColor="E2EFDA")
    fill_no = PatternFill("solid", fgColor="FCE4D6")
    font_header = Font(name="Calibri", size=10, bold=True, color="FFFFFF")
    font_celda = Font(name="Calibri", size=10, color="1F1F1F")
    font_ok = Font(name="Calibri", size=10, bold=True, color="375623")
    font_no = Font(name="Calibri", size=10, bold=True, color="9C0006")
    borde = Border(
        left=Side(style="thin", color="D9D9D9"),
        right=Side(style="thin", color="D9D9D9"),
        top=Side(style="thin", color="D9D9D9"),
        bottom=Side(style="thin", color="D9D9D9"),
    )

    encabezados_bonitos = [ENCABEZADOS.get(c, c) for c in columnas_csv]
    ws.append(encabezados_bonitos)

    max_lineas = max((texto.count("\n") + 1 for texto in encabezados_bonitos), default=2)
    ws.row_dimensions[1].height = max(48, max_lineas * 18)

    for col_idx, col_name in enumerate(columnas_csv, start=1):
        celda = ws.cell(row=1, column=col_idx)
        celda.fill = color_encabezado(col_name)
        celda.font = font_header
        celda.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        celda.border = borde

    for row_idx, fila in enumerate(filas, start=2):
        ws.row_dimensions[row_idx].height = 24
        for col_idx, col_name in enumerate(columnas_csv, start=1):
            val = convertir_valor(col_name, fila.get(col_name, ""))
            celda = ws.cell(row=row_idx, column=col_idx, value=val)
            celda.font = font_celda
            celda.border = borde

            if row_idx % 2 == 1:
                celda.fill = fill_zebra

            if col_name == "completado":
                celda.alignment = Alignment(horizontal="center", vertical="center")
                if val == "Sí":
                    celda.fill = fill_ok
                    celda.font = font_ok
                elif val == "No":
                    celda.fill = fill_no
                    celda.font = font_no
            elif col_name in COLUMNAS_NUMERICAS:
                celda.alignment = Alignment(horizontal="center", vertical="center")
                if col_name in {"duracion_segundos", "sus_puntaje"} and isinstance(val, (int, float)):
                    celda.number_format = "0.00"
            elif col_name == "q10_sugerencia":
                celda.alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)
            else:
                celda.alignment = Alignment(horizontal="left", vertical="center")

    for col_idx, col_name in enumerate(columnas_csv, start=1):
        letra = get_column_letter(col_idx)
        texto_header = ENCABEZADOS.get(col_name, col_name)
        ancho_header = max(len(linea) for linea in texto_header.split("\n"))

        if col_name == "id_participante_hash":
            ws.column_dimensions[letra].width = 18
        elif col_name == "q10_sugerencia":
            ws.column_dimensions[letra].width = 36
        else:
            ancho_datos = max(
                (len(str(ws.cell(row=r, column=col_idx).value or "")) for r in range(2, len(filas) + 2)),
                default=0,
            )
            ws.column_dimensions[letra].width = min(max(ancho_header + 4, ancho_datos + 3, 16), 30)

    ws.freeze_panes = "A2"
    if columnas_csv:
        ultima_col = get_column_letter(len(columnas_csv))
        ws.auto_filter.ref = f"A1:{ultima_col}{max(len(filas) + 1, 1)}"

    ws_res = wb.create_sheet(title="Resumen")
    ws_res.append(["Indicador del Experimento", "Valor"])
    fill_res = PatternFill("solid", fgColor="1F4E78")
    for c in range(1, 3):
        celda = ws_res.cell(row=1, column=c)
        celda.fill = fill_res
        celda.font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
        celda.alignment = Alignment(horizontal="center", vertical="center")
        celda.border = borde
    ws_res.row_dimensions[1].height = 28

    col_comp = get_column_letter(columnas_csv.index("completado") + 1) if "completado" in columnas_csv else "E"
    col_dur = get_column_letter(columnas_csv.index("duracion_segundos") + 1) if "duracion_segundos" in columnas_csv else "F"
    col_sus = get_column_letter(columnas_csv.index("sus_puntaje") + 1) if "sus_puntaje" in columnas_csv else "AC"

    metricas = [
        ("Total de intentos registrados", "=COUNTA(Respuestas!A2:A10000)", "0"),
        ("Encuestas completadas", f'=COUNTIF(Respuestas!{col_comp}2:{col_comp}10000,"Sí")', "0"),
        ("Encuestas abandonadas", f'=COUNTIF(Respuestas!{col_comp}2:{col_comp}10000,"No")', "0"),
        ("Tasa de finalización", "=IFERROR(B3/B2,0)", "0.0%"),
        ("Duración promedio (segundos)", f"=IFERROR(AVERAGE(Respuestas!{col_dur}2:{col_dur}10000),0)", "0.00"),
        ("Puntaje SUS promedio (0-100)", f"=IFERROR(AVERAGE(Respuestas!{col_sus}2:{col_sus}10000),0)", "0.00"),
    ]

    for idx, (nombre, formula, formato) in enumerate(metricas, start=2):
        ws_res.row_dimensions[idx].height = 24
        c1 = ws_res.cell(row=idx, column=1, value=nombre)
        c2 = ws_res.cell(row=idx, column=2, value=formula)
        c1.font = Font(name="Calibri", size=11, bold=True)
        c2.font = Font(name="Calibri", size=11)
        c2.number_format = formato
        c2.alignment = Alignment(horizontal="center", vertical="center")
        c1.border = borde
        c2.border = borde

    ws_res.column_dimensions["A"].width = 34
    ws_res.column_dimensions["B"].width = 18

    wb.save(ruta_xlsx)
    return ruta_xlsx