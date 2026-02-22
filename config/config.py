"""
Configuración central del Conciliador Bancario.

Toda tolerancia, ruta y constante vive aquí.
Para ajustar el comportamiento del conciliador, solo edita este archivo.
"""

"""
Responsabilidades:

1. Rutas        → dónde están los archivos de entrada y salida
2. Columnas     → cómo se llaman las columnas en cada Excel
3. Tolerancias  → qué tan flexible es el matching

"""

from pathlib import Path

#  Rutas 
BASE_DIR   = Path(__file__).resolve().parent.parent
DATA_DIR   = BASE_DIR / "data"
INPUT_DIR  = DATA_DIR / "input"
OUTPUT_DIR = DATA_DIR / "output"
LOGS_DIR   = DATA_DIR / "logs"

# Archivo de entrada
ARCHIVO_CARTOLA = INPUT_DIR / "cartola_personal.xlsx"
ARCHIVO_LIBRO   = INPUT_DIR / "libro_banco.xlsx"

# Archivos de salida
ARCHIVO_RESULTADO     = OUTPUT_DIR / "conciliacion_resultado.xlsx"
ARCHIVO_SIN_CONCILIAR = OUTPUT_DIR / "partidas_sin_conciliar.xlsx"
ARCHIVO_LOG           = LOGS_DIR   / "conciliacion.log"

# Mapeo de columnas 
# Traduce los nombres reales del Excel a nombres internos del código.
# Si el Excel cambia un encabezado, solo se actualiza aquí.
COLUMNAS_CARTOLA = {
    "fecha":       "Fecha Operación",
    "descripcion": "Descripción Operación",
    "cargo":       "Cargo (CLP)",
    "abono":       "Abono (CLP)",
    "referencia":  "Referencia Interna",
    "banco":       "Banco/Institución",
}

COLUMNAS_LIBRO = {
    "fecha":       "Fecha Contable",
    "descripcion": "Descripción",
    "debito":      "Monto Débito",
    "credito":     "Monto Crédito",
    "referencia":  "Número Referencia",
    "codigo":      "Código Transacción",
}

# ─── Tolerancias de matching ──────────────────────────────────────────────────
# Definen qué tan flexible es el algoritmo al comparar dos transacciones.
TOLERANCIA_MONTO_PCT  = 0.02   # ±2%  → 100.000 hace match con 98.000–102.000
TOLERANCIA_DIAS       = 3      # ±3 días entre fecha cartola y fecha libro
TOLERANCIA_REFERENCIA = 4      # mínimo de caracteres iniciales que deben coincidir


print('BASE_DIR :', BASE_DIR)
print('INPUT_DIR:', INPUT_DIR)
print('OUTPUT_DIR:', OUTPUT_DIR)
print()
print('Columnas cartola:', list(COLUMNAS_CARTOLA.keys()))
print('Columnas libro  :', list(COLUMNAS_LIBRO.keys()))
print()
print('Tolerancia monto:', TOLERANCIA_MONTO_PCT)
print('Tolerancia días :', TOLERANCIA_DIAS)
print('Tolerancia ref  :', TOLERANCIA_REFERENCIA)
