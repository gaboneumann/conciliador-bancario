"""
writer.py — Escritura de archivos Excel de resultado (v2).

Responsabilidad: tomar el DataFrame clasificado y producir
los archivos Excel de salida con formato aplicado.

Estructura visual de cada hoja:
    Fila 1 → encabezados agrupados (Cartola | Libro | Resultado)
    Fila 2 → encabezados de columna individuales
    Fila 3+ → datos con color según tipo_match
"""
import pandas as pd
from openpyxl import Workbook
from openpyxl.utils import get_column_letter

from config.config import ARCHIVO_RESULTADO, ARCHIVO_SIN_CONCILIAR, OUTPUT_DIR
from reporting.formatter import (
    estilo_encabezado,
    estilo_encabezado_bloque,
    estilo_fila,
    estilo_numero,
    estilo_fecha,
    ANCHOS_RESULTADO,
    ANCHOS_SIN_CONCILIAR,
    BLOQUES_RESULTADO,
    BLOQUES_SIN_CONCILIAR,
)
from utils.logger import get_logger
from utils.exceptions import ConciliadorError

logger = get_logger(__name__)


# ─── Verificación de archivo disponible ──────────────────────────────────────

def _verificar_archivo_disponible(ruta) -> None:
    """
    Verifica que el archivo no esté bloqueado por otro proceso (ej: Excel abierto).
    Si está bloqueado, lanza ConciliadorError con un mensaje claro.

    Args:
        ruta: Path del archivo a verificar
    """
    if ruta.exists():
        try:
            ruta.unlink()
        except PermissionError:
            raise ConciliadorError(
                f"El archivo '{ruta.name}' está abierto en Excel. "
                f"Ciérralo e intenta de nuevo."
            )


# ─── Definición de columnas v2 ────────────────────────────────────────────────

# Reporte principal: 7 cartola + 7 libro + 10 resultado = 24 columnas
ENCABEZADOS_RESULTADO = [
    # — Cartola (7) —
    "Fecha Operación", "Fecha Valor", "Glosa Cartola",
    "RUT Cartola", "Monto Cartola", "Nº Documento", "Banco",
    # — Libro (7) —
    "Fecha Contable", "Glosa Libro",
    "RUT Libro", "Monto Libro", "Nº Referencia", "Nº Comprobante", "Código Tx",
    # — Resultado (10) —
    "Tipo Match", "Certeza", "Regla Aplicada",
    "Dif. Monto", "Dif. Días",
    "Flag Conciliación", "Flag IVA",
    "Días Antigüedad", "Tramo Antigüedad", "Acción Recomendada",
]

COLUMNAS_RESULTADO = [
    # — Cartola (7) —
    "fecha_operacion_cartola", "fecha_valor_cartola", "glosa_cartola",
    "rut_cartola", "monto_cartola", "nro_documento_cartola", "banco_cartola",
    # — Libro (7) —
    "fecha_contable_libro", "glosa_libro",
    "rut_libro", "monto_libro", "nro_referencia_libro",
    "nro_comprobante_libro", "codigo_tx_libro",
    # — Resultado (10) —
    "tipo_match", "certeza", "regla_aplicada",
    "diff_monto", "diff_dias",
    "flag_conciliacion", "flag_iva",
    "dias_antiguedad", "tramo_antiguedad", "accion_recomendada",
]

# Reporte sin conciliar: 7 cartola + 3 diagnóstico = 10 columnas
ENCABEZADOS_SIN_CONCILIAR = [
    # — Cartola (7) —
    "Fecha Operación", "Fecha Valor", "Glosa Cartola",
    "RUT Cartola", "Monto Cartola", "Nº Documento", "Banco",
    # — Diagnóstico (3) —
    "Motivo", "Monto Más Cercano", "Dif. Monto Cercano",
]

COLUMNAS_SIN_CONCILIAR = [
    # — Cartola (7) —
    "fecha_operacion_cartola", "fecha_valor_cartola", "glosa_cartola",
    "rut_cartola", "monto_cartola", "nro_documento_cartola", "banco_cartola",
    # — Diagnóstico (3) —
    "motivo", "monto_cercano", "diff_monto_cercano",
]

# Columnas que reciben formato especial
COLS_MONTO = {
    "monto_cartola", "monto_libro", "diff_monto",
    "monto_cercano", "diff_monto_cercano",
}
COLS_FECHA = {
    "fecha_operacion_cartola", "fecha_valor_cartola",
    "fecha_contable_libro", "fecha_cercana",
}


# ─── Función interna: fila de encabezados agrupados ──────────────────────────

def _escribir_fila_bloques(ws, bloques: list) -> None:
    """
    Escribe la fila 1 con encabezados agrupados y merge de celdas.

    Args:
        ws     : Hoja de openpyxl activa
        bloques: Lista de dicts con nombre, bloque, col_inicio, col_fin
    """
    ws.row_dimensions[1].height = 22

    for bloque in bloques:
        col_ini = bloque["col_inicio"]
        col_fin = bloque["col_fin"]
        nombre  = bloque["nombre"]
        tipo    = bloque["bloque"]

        if col_ini < col_fin:
            ws.merge_cells(
                start_row=1, start_column=col_ini,
                end_row=1,   end_column=col_fin,
            )

        celda = ws.cell(row=1, column=col_ini, value=nombre)
        estilo = estilo_encabezado_bloque(tipo)
        celda.font      = estilo["font"]
        celda.fill      = estilo["fill"]
        celda.alignment = estilo["alignment"]
        celda.border    = estilo["border"]


# ─── Función interna: escritura de hoja ──────────────────────────────────────

def _escribir_hoja(
    ws,
    df: pd.DataFrame,
    columnas: list,
    encabezados: list,
    anchos: dict,
    bloques: list,
) -> None:
    """
    Escribe datos y aplica estilos en una hoja de Excel.

    Estructura:
        Fila 1 → encabezados agrupados por bloque
        Fila 2 → encabezados de columna individuales
        Fila 3+ → datos

    Args:
        ws          : Hoja de openpyxl activa
        df          : DataFrame con los datos
        columnas    : Columnas del DataFrame a escribir (en orden)
        encabezados : Nombres legibles para la fila de encabezado
        anchos      : Dict {letra_columna: ancho}
        bloques     : Lista de bloques para la fila agrupada
    """
    ws.sheet_view.showGridLines = False

    # — Fila 1: encabezados agrupados —
    _escribir_fila_bloques(ws, bloques)

    # — Fila 2: encabezados de columna —
    ws.row_dimensions[2].height = 36
    estilo_enc = estilo_encabezado()

    for col_idx, nombre in enumerate(encabezados, start=1):
        celda = ws.cell(row=2, column=col_idx, value=nombre)
        celda.font      = estilo_enc["font"]
        celda.fill      = estilo_enc["fill"]
        celda.alignment = estilo_enc["alignment"]
        celda.border    = estilo_enc["border"]

    # — Fila 3+: datos —
    for row_idx, (_, fila) in enumerate(df[columnas].iterrows(), start=3):
        tipo_match        = fila.get("tipo_match", "Manual")
        flag_conciliacion = fila.get("flag_conciliacion", "")
        estilo            = estilo_fila(tipo_match, flag_conciliacion=flag_conciliacion)

        for col_idx, col_nombre in enumerate(columnas, start=1):
            valor = fila[col_nombre]

            if pd.isna(valor):
                valor = None

            celda = ws.cell(row=row_idx, column=col_idx, value=valor)
            celda.font      = estilo["font"]
            celda.fill      = estilo["fill"]
            celda.alignment = estilo["alignment"]
            celda.border    = estilo["border"]

            if col_nombre in COLS_MONTO and valor is not None:
                celda.number_format = estilo_numero()["number_format"]
                celda.alignment     = estilo_numero()["alignment"]
            elif col_nombre in COLS_FECHA and valor is not None:
                celda.number_format = estilo_fecha()["number_format"]
                celda.alignment     = estilo_fecha()["alignment"]

    # — Anchos de columna —
    for letra, ancho in anchos.items():
        ws.column_dimensions[letra].width = ancho

    # — Freeze encabezados (fijar las 2 primeras filas) —
    ws.freeze_panes = "A3"


# ─── Funciones públicas ───────────────────────────────────────────────────────

def escribir_resultado(df_resultado: pd.DataFrame, saldo: dict | None = None) -> None:
    """
    Escribe el reporte completo de conciliación.

    Args:
        df_resultado: DataFrame producido por classifier.clasificar()
        saldo       : Dict de calcular_diferencia_saldo() (opcional)
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    _verificar_archivo_disponible(ARCHIVO_RESULTADO)

    wb = Workbook()
    ws = wb.active
    ws.title = "Conciliación"

    _escribir_hoja(
        ws,
        df_resultado,
        COLUMNAS_RESULTADO,
        ENCABEZADOS_RESULTADO,
        ANCHOS_RESULTADO,
        BLOQUES_RESULTADO,
    )

    ws_resumen = wb.create_sheet("Resumen")
    _escribir_resumen(ws_resumen, df_resultado, saldo=saldo)

    wb.save(ARCHIVO_RESULTADO)
    logger.info(f"Resultado guardado → {ARCHIVO_RESULTADO}")


def escribir_sin_conciliar(df_resultado: pd.DataFrame) -> None:
    """
    Escribe el reporte de partidas sin conciliar con columnas de diagnóstico.

    Args:
        df_resultado: DataFrame producido por classifier.clasificar()
    """
    from conciliation.classifier import separar_sin_conciliar

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    _verificar_archivo_disponible(ARCHIVO_SIN_CONCILIAR)

    df_sin = separar_sin_conciliar(df_resultado)

    wb = Workbook()
    ws = wb.active
    ws.title = "Sin Conciliar"

    _escribir_hoja(
        ws,
        df_sin,
        COLUMNAS_SIN_CONCILIAR,
        ENCABEZADOS_SIN_CONCILIAR,
        ANCHOS_SIN_CONCILIAR,
        BLOQUES_SIN_CONCILIAR,
    )

    wb.save(ARCHIVO_SIN_CONCILIAR)
    logger.info(f"Sin conciliar guardado → {ARCHIVO_SIN_CONCILIAR} ({len(df_sin)} partidas)")


def _escribir_resumen(ws, df: pd.DataFrame, saldo: dict | None) -> None:
    """
    Escribe la hoja de resumen ejecutivo con totales, porcentajes
    y diferencia de saldo si está disponible.

    Args:
        ws    : Hoja de openpyxl activa
        df    : DataFrame de resultado completo
        saldo : Dict de calcular_diferencia_saldo() o None
    """
    ws.sheet_view.showGridLines = False

    total     = len(df)
    exactos   = (df["tipo_match"] == "Exacto").sum()
    sugeridos = (df["tipo_match"] == "Sugerido").sum()
    manuales  = (df["tipo_match"] == "Manual").sum()
    pct_conc  = round((exactos + sugeridos) / total * 100, 1) if total > 0 else 0

    filas = [
        ("Resumen de Conciliación", ""),
        ("", ""),
        ("Total transacciones cartola", total),
        ("Match Exacto",               exactos),
        ("Match Sugerido",             sugeridos),
        ("Sin Match (Manual)",         manuales),
        ("% Conciliado",               f"{pct_conc}%"),
    ]

    if saldo:
        filas += [
            ("", ""),
            ("Diferencia de Saldo", ""),
            ("Saldo Cartola",  saldo["saldo_cartola"]),
            ("Saldo Libro",    saldo["saldo_libro"]),
            ("Diferencia",     saldo["diferencia"]),
            ("¿Cuadra?",       "Sí" if saldo["cuadra"] else "No"),
        ]

    estilo_enc  = estilo_encabezado()
    estilo_dato = estilo_fila("blanco")

    for row_idx, (etiqueta, valor) in enumerate(filas, start=1):
        celda_a = ws.cell(row=row_idx, column=1, value=etiqueta)
        celda_b = ws.cell(row=row_idx, column=2, value=valor)

        es_titulo = row_idx == 1 or etiqueta in ("Diferencia de Saldo",)

        if es_titulo and etiqueta:
            celda_a.font = estilo_enc["font"]
            celda_a.fill = estilo_enc["fill"]
            celda_b.fill = estilo_enc["fill"]
        else:
            celda_a.font = estilo_dato["font"]
            celda_b.font = estilo_dato["font"]

        if isinstance(valor, (int, float)) and etiqueta in (
            "Saldo Cartola", "Saldo Libro", "Diferencia"
        ):
            celda_b.number_format = estilo_numero()["number_format"]

    ws.column_dimensions["A"].width = 32
    ws.column_dimensions["B"].width = 18