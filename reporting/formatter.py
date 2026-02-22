"""
formatter.py — Estilos y colores para los Excel de salida.

Responsabilidad única: definir y retornar objetos de estilo de openpyxl.
No escribe archivos ni manipula datos.

Colores de filas por tipo de match:
    exacto    → verde claro   #C6EFCE
    parcial   → amarillo claro #FFEB9C
    sin_match → rojo claro    #FFC7CE

Colores de encabezados agrupados:
    Cartola Personal → azul oscuro   #1F4E79
    Libro del Banco  → verde oscuro  #1A5632
    Resultado        → gris oscuro   #404040
    Diagnóstico      → rojo oscuro   #7B2C2C
"""
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

# ─── Colores de filas ─────────────────────────────────────────────────────────

COLORES = {
    "exacto":     "C6EFCE",   # verde claro
    "parcial":    "FFEB9C",   # amarillo claro
    "sin_match":  "FFC7CE",   # rojo claro
    "encabezado": "1F4E79",   # azul oscuro (encabezado simple)
    "blanco":     "FFFFFF",
    "gris_claro": "F2F2F2",
}

# ─── Colores de bloques (encabezados agrupados) ───────────────────────────────

COLORES_BLOQUE = {
    "cartola":     "1F4E79",  # azul oscuro
    "libro":       "1A5632",  # verde oscuro
    "resultado":   "404040",  # gris oscuro
    "diagnostico": "7B2C2C",  # rojo oscuro
}

# ─── Fuente ───────────────────────────────────────────────────────────────────

FUENTE = "Arial"
TAMANO = 10


# ─── Constructores de estilo ──────────────────────────────────────────────────

def estilo_encabezado() -> dict:
    """Estilo para la fila de encabezados de columna (fila 2)."""
    return {
        "font": Font(
            name=FUENTE,
            size=TAMANO,
            bold=True,
            color="FFFFFF",
        ),
        "fill": PatternFill(
            fill_type="solid",
            start_color=COLORES["encabezado"],
        ),
        "alignment": Alignment(
            horizontal="center",
            vertical="center",
            wrap_text=True,
        ),
        "border": _borde_fino(),
    }


def estilo_encabezado_bloque(bloque: str) -> dict:
    """
    Estilo para la fila superior de encabezados agrupados (fila 1).

    Cada bloque tiene su propio color para separar visualmente
    los datos de cartola, libro, resultado y diagnóstico.

    Args:
        bloque: "cartola", "libro", "resultado" o "diagnostico"

    Returns:
        Dict con font, fill, alignment y border
    """
    color = COLORES_BLOQUE.get(bloque, COLORES_BLOQUE["resultado"])

    return {
        "font": Font(
            name=FUENTE,
            size=TAMANO + 1,   # un punto más grande para destacar
            bold=True,
            color="FFFFFF",
        ),
        "fill": PatternFill(
            fill_type="solid",
            start_color=color,
        ),
        "alignment": Alignment(
            horizontal="center",
            vertical="center",
        ),
        "border": _borde_medio(),
    }


def estilo_fila(tipo_match: str) -> dict:
    """
    Estilo para una fila de datos según su tipo de match.

    Args:
        tipo_match: "exacto", "parcial", "sin_match" o cualquier string

    Returns:
        Dict con font, fill, alignment y border listos para aplicar
    """
    color = COLORES.get(tipo_match, COLORES["blanco"])

    return {
        "font": Font(name=FUENTE, size=TAMANO),
        "fill": PatternFill(fill_type="solid", start_color=color),
        "alignment": Alignment(vertical="center"),
        "border": _borde_fino(),
    }


def estilo_numero() -> dict:
    """Estilo adicional para celdas con montos."""
    return {
        "number_format": '#,##0_-;[Red](#,##0)',
        "alignment": Alignment(horizontal="right", vertical="center"),
    }


def estilo_fecha() -> dict:
    """Estilo adicional para celdas con fechas."""
    return {
        "number_format": "YYYY-MM-DD",
        "alignment": Alignment(horizontal="center", vertical="center"),
    }


# ─── Anchos de columna ────────────────────────────────────────────────────────
# resultado: 5 cartola + 5 libro + 3 resultado = 13 columnas
# sin_conciliar: 5 cartola + 5 diagnóstico = 10 columnas

ANCHOS_RESULTADO = {
    "A": 14,   # fecha_cartola
    "B": 16,   # monto_cartola
    "C": 35,   # descripcion_cartola
    "D": 16,   # referencia_cartola
    "E": 20,   # banco_cartola
    "F": 14,   # fecha_libro
    "G": 16,   # monto_libro
    "H": 35,   # descripcion_libro
    "I": 16,   # referencia_libro
    "J": 14,   # codigo_libro
    "K": 14,   # tipo_match
    "L": 14,   # diff_monto
    "M": 12,   # diff_dias
}

ANCHOS_SIN_CONCILIAR = {
    "A": 14,   # fecha_cartola
    "B": 16,   # monto_cartola
    "C": 35,   # descripcion_cartola
    "D": 16,   # referencia_cartola
    "E": 20,   # banco_cartola
    "F": 35,   # motivo
    "G": 14,   # fecha_cercana
    "H": 16,   # monto_cercano
    "I": 35,   # descripcion_cercana
    "J": 16,   # diff_monto_cercano
}

# ─── Definición de bloques para encabezados agrupados ─────────────────────────
# Cada bloque define: nombre visible, color y rango de columnas (1-based)

BLOQUES_RESULTADO = [
    {"nombre": "Cartola Personal", "bloque": "cartola",   "col_inicio": 1, "col_fin": 5},
    {"nombre": "Libro del Banco",  "bloque": "libro",     "col_inicio": 6, "col_fin": 10},
    {"nombre": "Resultado",        "bloque": "resultado", "col_inicio": 11, "col_fin": 13},
]

BLOQUES_SIN_CONCILIAR = [
    {"nombre": "Cartola Personal",    "bloque": "cartola",     "col_inicio": 1, "col_fin": 5},
    {"nombre": "Diagnóstico",         "bloque": "diagnostico", "col_inicio": 6, "col_fin": 10},
]


# ─── Utilidades internas ──────────────────────────────────────────────────────

def _borde_fino() -> Border:
    lado = Side(style="thin", color="BFBFBF")
    return Border(left=lado, right=lado, top=lado, bottom=lado)


def _borde_medio() -> Border:
    """Borde más grueso para separar bloques visualmente."""
    lado_grueso = Side(style="medium", color="FFFFFF")
    lado_fino   = Side(style="thin",   color="BFBFBF")
    return Border(
        left=lado_grueso,
        right=lado_grueso,
        top=lado_fino,
        bottom=lado_fino,
    )