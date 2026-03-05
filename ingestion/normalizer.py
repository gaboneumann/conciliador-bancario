"""
normalizer.py — Limpieza y estandarización de DataFrames crudos (v2).

Esquema de salida garantizado:

    Cartola:
        fecha_operacion, fecha_valor, glosa, rut, monto, nro_documento, banco

    Libro:
        fecha_contable, glosa, rut, monto, nro_referencia, nro_comprobante, codigo_tx
"""
import re
import unicodedata
import pandas as pd

from config.config import COLUMNAS_CARTOLA, COLUMNAS_LIBRO
from utils.logger import get_logger
from utils.exceptions import NormalizacionError
from utils.rut_utils import normalizar_rut

logger = get_logger(__name__)


# ─── Funciones auxiliares ─────────────────────────────────────────────────────

def _normalizar_texto(texto: str) -> str:
    """
    Estandariza un string:
      1. Elimina espacios al inicio y al final
      2. Colapsa espacios internos múltiples en uno solo
      3. Convierte a minúsculas
      4. Elimina acentos (á→a, é→e, ñ→n, etc.)
    """
    if not isinstance(texto, str):
        return ""
    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    texto = texto.strip().lower()
    texto = re.sub(r"\s+", " ", texto)
    return texto


def _normalizar_referencia(ref) -> str:
    """
    Estandariza una referencia: solo alfanumérico, uppercase.
    Retorna vacío si es nulo.
    """
    if pd.isna(ref) or str(ref).strip() == "":
        return ""
    ref = str(ref).strip().upper()
    return re.sub(r"[^A-Z0-9]", "", ref)


def _parsear_fecha(serie: pd.Series, nombre_columna: str) -> pd.Series:
    """Convierte una Serie de fechas a datetime64."""
    try:
        return pd.to_datetime(serie, dayfirst=False, errors="coerce")
    except Exception as e:
        raise NormalizacionError(
            f"No se pudo parsear la columna de fechas: {e}",
            columna=nombre_columna
        )


def _normalizar_rut_serie(serie: pd.Series) -> pd.Series:
    """
    Aplica normalizar_rut() a cada elemento de la Serie.
    Retorna el canonical si es válido, None si no.
    """
    def _extraer_canonical(valor):
        resultado = normalizar_rut(valor)
        return resultado["canonical"] if resultado["es_valido"] else None

    return serie.apply(_extraer_canonical)


# ─── Normalizadores principales ───────────────────────────────────────────────

def normalizar_cartola(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normaliza el DataFrame crudo de la cartola bancaria.

    Pasos:
        1. Renombra columnas Excel → nombres internos
        2. Parsea fecha_operacion y fecha_valor
        3. Normaliza RUT
        4. Unifica cargo/abono en monto con signo
        5. Limpia glosa y nro_documento
        6. Elimina filas sin monto válido

    Returns:
        DataFrame con columnas:
        fecha_operacion, fecha_valor, glosa, rut, monto, nro_documento, banco
    """
    logger.info("Normalizando cartola bancaria...")
    df = df.copy()

    # — 1. Renombrar columnas —
    inverso = {v: k for k, v in COLUMNAS_CARTOLA.items()}
    df = df.rename(columns=inverso)

    # — 2. Parsear fechas —
    df["fecha_operacion"] = _parsear_fecha(df["fecha_operacion"], "fecha_operacion")
    df["fecha_valor"]     = _parsear_fecha(df["fecha_valor"],     "fecha_valor")

    # — 3. Normalizar RUT —
    df["rut"] = _normalizar_rut_serie(df["rut"])

    # — 4. Unificar cargo/abono en monto con signo —
    cargo = pd.to_numeric(df["cargo"], errors="coerce").fillna(0)
    abono = pd.to_numeric(df["abono"], errors="coerce").fillna(0)
    df["monto"] = abono - cargo

    # — 5. Limpiar texto —
    df["glosa"]        = df["glosa"].apply(_normalizar_texto)
    df["nro_documento"] = df["nro_documento"].apply(_normalizar_referencia)

    # — 6. Eliminar filas sin monto válido —
    n_antes = len(df)
    df = df[df["monto"] != 0].copy()
    n_eliminadas = n_antes - len(df)
    if n_eliminadas > 0:
        logger.warning(f"Cartola: {n_eliminadas} filas eliminadas por monto cero o nulo")

    logger.info(f"Cartola normalizada: {len(df)} filas válidas")

    columnas_salida = ["fecha_operacion", "fecha_valor", "glosa", "rut", "monto", "nro_documento", "banco"]
    return df[columnas_salida].reset_index(drop=True)


def normalizar_libro(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normaliza el DataFrame crudo del libro auxiliar.

    Pasos:
        1. Renombra columnas Excel → nombres internos
        2. Parsea fecha_contable
        3. Normaliza RUT
        4. Unifica debe/haber en monto con signo
        5. Limpia glosa y nro_referencia
        6. Elimina filas sin monto válido

    Returns:
        DataFrame con columnas:
        fecha_contable, glosa, rut, monto, nro_referencia, nro_comprobante, codigo_tx
    """
    logger.info("Normalizando libro auxiliar...")
    df = df.copy()

    # — 1. Renombrar columnas —
    inverso = {v: k for k, v in COLUMNAS_LIBRO.items()}
    df = df.rename(columns=inverso)

    # — 2. Parsear fecha —
    df["fecha_contable"] = _parsear_fecha(df["fecha_contable"], "fecha_contable")

    # — 3. Normalizar RUT —
    df["rut"] = _normalizar_rut_serie(df["rut"])

    # — 4. Unificar debe/haber en monto con signo —
    debe  = pd.to_numeric(df["debe"],  errors="coerce").fillna(0)
    haber = pd.to_numeric(df["haber"], errors="coerce").fillna(0)
    df["monto"] = haber - debe

    # — 5. Limpiar texto —
    df["glosa"]         = df["glosa"].apply(_normalizar_texto)
    df["nro_referencia"] = df["nro_referencia"].apply(_normalizar_referencia)

    # — 6. Eliminar filas sin monto válido —
    n_antes = len(df)
    df = df[df["monto"] != 0].copy()
    n_eliminadas = n_antes - len(df)
    if n_eliminadas > 0:
        logger.warning(f"Libro: {n_eliminadas} filas eliminadas por monto cero o nulo")

    logger.info(f"Libro normalizado: {len(df)} filas válidas")

    columnas_salida = ["fecha_contable", "glosa", "rut", "monto", "nro_referencia", "nro_comprobante", "codigo_tx"]
    return df[columnas_salida].reset_index(drop=True)