"""
Errores de nuestro dataset:

- Fechas como strings ("2024-01-15") en vez de datetime
- Descripciones con espacios extra, mayúsculas inconsistentes, acentos
- Montos con NaN, negativos o cero
- Referencias con caracteres extraños o truncadas
- Columnas con nombres distintos en cada archivo

1. Renombra columnas  → de nombres Excel a nombres internos
2. Parsea fechas      → string a datetime
3. Limpia montos      → unifica cargo/abono en un solo monto con signo
4. Limpia texto       → strip, lowercase, normaliza acentos
5. Limpia referencias → solo caracteres alfanuméricos
6. Elimina nulos      → filas donde el monto es NaN
"""


"""
normalizer.py — Limpieza y estandarización de DataFrames crudos.

Responsabilidad: transformar los datos tal como vienen del Excel
en un formato predecible y consistente para el motor de conciliación.

Esquema de salida garantizado para ambos archivos:
    - fecha        : datetime64
    - descripcion  : str (lowercase, sin espacios extra, sin acentos)
    - monto        : float (negativo=egreso, positivo=ingreso)
    - referencia   : str (alfanumérico, uppercase)
"""
import re
import unicodedata
import pandas as pd

from config.config import COLUMNAS_CARTOLA, COLUMNAS_LIBRO
from utils.logger import get_logger
from utils.exceptions import NormalizacionError

logger = get_logger(__name__)


# ─── Funciones auxiliares ─────────────────────────────────────────────────────

def _normalizar_texto(texto: str) -> str:
    """
    Estandariza un string:
      1. Elimina espacios al inicio y al final
      2. Colapsa espacios internos múltiples en uno solo
      3. Convierte a minúsculas
      4. Elimina acentos (á→a, é→e, ñ→n, etc.)

    Ejemplo:
        "  PAGO Luz  Enel  " → "pago luz enel"
        "Transferéncia"      → "transferencia"
    """
    if not isinstance(texto, str):
        return ""
    # Eliminar acentos usando normalización Unicode
    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    texto = texto.strip().lower()
    texto = re.sub(r"\s+", " ", texto)
    return texto


def _normalizar_referencia(ref) -> str:
    """
    Estandariza una referencia interna:
      - Solo caracteres alfanuméricos
      - Uppercase
      - Vacío si es nulo

    Ejemplo:
        "1234X??"  → "1234X"
        "ref-5678" → "REF5678"
    """
    if pd.isna(ref) or str(ref).strip() == "":
        return ""
    ref = str(ref).strip().upper()
    return re.sub(r"[^A-Z0-9]", "", ref)


def _parsear_fecha(serie: pd.Series, nombre_archivo: str) -> pd.Series:
    """
    Convierte una Serie de fechas (string o mixed) a datetime.
    Lanza NormalizacionError si no puede parsear ninguna fecha.
    """
    try:
        return pd.to_datetime(serie, dayfirst=False, errors="coerce")
    except Exception as e:
        raise NormalizacionError(
            f"No se pudo parsear la columna de fechas: {e}",
            columna="fecha"
        )


# Normalizadores principales

def normalizar_cartola(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normaliza el DataFrame crudo de la cartola personal.

    Pasos:
        1. Renombra columnas Excel → nombres internos
        2. Parsea fechas
        3. Unifica cargo/abono en un monto con signo
        4. Limpia descripcion y referencia
        5. Elimina filas sin monto válido

    Returns:
        DataFrame con columnas: fecha, descripcion, monto, referencia, banco
    """
    logger.info("Normalizando cartola personal...")
    df = df.copy()

    # — 1. Renombrar columnas —
    inverso = {v: k for k, v in COLUMNAS_CARTOLA.items()}
    df = df.rename(columns=inverso)

    # — 2. Parsear fechas —
    df["fecha"] = _parsear_fecha(df["fecha"], "cartola")

    # — 3. Unificar cargo y abono en monto con signo —
    # cargo  → negativo (sale dinero)
    # abono  → positivo (entra dinero)
    cargo = pd.to_numeric(df["cargo"], errors="coerce").fillna(0)
    abono = pd.to_numeric(df["abono"], errors="coerce").fillna(0)
    df["monto"] = abono - cargo

    # — 4. Limpiar texto —
    df["descripcion"] = df["descripcion"].apply(_normalizar_texto)
    df["referencia"]  = df["referencia"].apply(_normalizar_referencia)

    # — 5. Eliminar filas sin monto válido —
    n_antes = len(df)
    df = df[df["monto"] != 0].copy()
    n_eliminadas = n_antes - len(df)
    if n_eliminadas > 0:
        logger.warning(f"Cartola: {n_eliminadas} filas eliminadas por monto cero o nulo")

    logger.info(f"Cartola normalizada: {len(df)} filas válidas")

    return df[["fecha", "descripcion", "monto", "referencia", "banco"]].reset_index(drop=True)


def normalizar_libro(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normaliza el DataFrame crudo del libro del banco.

    Pasos:
        1. Renombra columnas Excel → nombres internos
        2. Parsea fechas
        3. Unifica debito/credito en un monto con signo
        4. Limpia descripcion y referencia
        5. Elimina filas sin monto válido

    Returns:
        DataFrame con columnas: fecha, descripcion, monto, referencia, codigo
    """
    logger.info("Normalizando libro del banco...")
    df = df.copy()

    # — 1. Renombrar columnas —
    inverso = {v: k for k, v in COLUMNAS_LIBRO.items()}
    df = df.rename(columns=inverso)

    # — 2. Parsear fechas —
    df["fecha"] = _parsear_fecha(df["fecha"], "libro")

    # — 3. Unificar debito y credito en monto con signo —
    # debito  → negativo (sale dinero)
    # credito → positivo (entra dinero)
    debito  = pd.to_numeric(df["debito"],  errors="coerce").fillna(0)
    credito = pd.to_numeric(df["credito"], errors="coerce").fillna(0)
    df["monto"] = credito - debito

    # — 4. Limpiar texto —
    df["descripcion"] = df["descripcion"].apply(_normalizar_texto)
    df["referencia"]  = df["referencia"].apply(_normalizar_referencia)

    # — 5. Eliminar filas sin monto válido —
    n_antes = len(df)
    df = df[df["monto"] != 0].copy()
    n_eliminadas = n_antes - len(df)
    if n_eliminadas > 0:
        logger.warning(f"Libro: {n_eliminadas} filas eliminadas por monto cero o nulo")

    logger.info(f"Libro normalizado: {len(df)} filas válidas")

    return df[["fecha", "descripcion", "monto", "referencia", "codigo"]].reset_index(drop=True)