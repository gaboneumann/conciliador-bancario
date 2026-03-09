"""
config.py — Configuración central del Conciliador Bancario v2.

Toda tolerancia, ruta y constante vive aquí.
Para ajustar el comportamiento del conciliador, solo edita este archivo.

Responsabilidades:
1. Rutas        → dónde están los archivos de entrada y salida
2. Columnas     → cómo se llaman las columnas en cada Excel (v2)
3. Tolerancias  → qué tan flexible es el matching
4. Flags        → etiquetas de certeza y antigüedad
"""

from pathlib import Path

# ─── Rutas ────────────────────────────────────────────────────────────────────
BASE_DIR   = Path(__file__).resolve().parent.parent
DATA_DIR   = BASE_DIR / "data"
INPUT_DIR  = DATA_DIR / "input"
OUTPUT_DIR = DATA_DIR / "output"
LOGS_DIR   = DATA_DIR / "logs"

ARCHIVO_CARTOLA       = INPUT_DIR  / "cartola_bancaria.xlsx"
ARCHIVO_LIBRO         = INPUT_DIR  / "libro_auxiliar.xlsx"
ARCHIVO_RESULTADO     = OUTPUT_DIR / "conciliacion_resultado.xlsx"
ARCHIVO_SIN_CONCILIAR = OUTPUT_DIR / "partidas_sin_conciliar.xlsx"
ARCHIVO_HALLAZGOS = OUTPUT_DIR / "hallazgos_criticos_auditoria.xlsx"
ARCHIVO_LOG           = LOGS_DIR   / "conciliacion.log"

# ─── Mapeo de columnas ────────────────────────────────────────────────────────
# Traduce los nombres reales del Excel a nombres internos del código.
# Si el Excel cambia un encabezado, solo se actualiza aquí.

COLUMNAS_CARTOLA = {
    "fecha_operacion": "Fecha Operación",
    "fecha_valor":     "Fecha Valor",
    "glosa":           "Glosa",
    "rut":             "RUT Origen/Destino",
    "cargo":           "Cargos (CLP)",
    "abono":           "Abonos (CLP)",
    "saldo":           "Saldo Disponible",
    "nro_documento":   "Nº Documento",
    "banco":           "Banco/Institución",
}

COLUMNAS_LIBRO = {
    "fecha_contable":   "Fecha Contable",
    "glosa":            "Glosa Contable",
    "rut":              "RUT Auxiliar",
    "debe":             "Debe (CLP)",
    "haber":            "Haber (CLP)",
    "saldo":            "Saldo",
    "nro_referencia":   "Nº Referencia",
    "nro_comprobante":  "Nº Comprobante",
    "codigo_tx":        "Código Transacción",
}

# ─── Tolerancias de matching ──────────────────────────────────────────────────
TOLERANCIA_MONTO_PCT      = 0.02    # ±2% de diferencia relativa en monto
TOLERANCIA_MONTO_ABS_MAX  = 5_000   # cap absoluto en CLP — evita que millones pasen por estar bajo el 2%
TOLERANCIA_DIAS           = 5       # ±5 días entre fecha_valor (cartola) y fecha_contable (libro)
TOLERANCIA_REFERENCIA     = 6       # primeros 6 caracteres de Nº Documento vs Nº Referencia
FACTOR_IVA                = 1.19    # ratio esperado para detección neto vs bruto
TOLERANCIA_IVA            = 0.01    # ±1% sobre el ratio 1.19

# ─── Niveles de certeza ───────────────────────────────────────────────────────
CERTEZA_EXACTO    = "Exacto"
CERTEZA_SUGERIDO  = "Sugerido"
CERTEZA_MANUAL    = "Manual"

# ─── Flags especiales ─────────────────────────────────────────────────────────
FLAG_PARTIDA_CONCILIACION = "Partida en Conciliación"
FLAG_IVA                  = "Posible Neto vs Bruto (×1.19)"

# ─── Antigüedad de partidas ───────────────────────────────────────────────────
ANTIGUEDAD_VIGENTE       = 30   # días — menos de esto: Vigente
ANTIGUEDAD_OBSERVACION   = 90   # días — entre 30 y esto: En Observación
                                 # más de 90: Crítico