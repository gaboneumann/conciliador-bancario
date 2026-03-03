"""
reader.py — Lectura de archivos Excel de entrada.

Responsabilidad única: abrir los archivos y retornarlos como DataFrames.
No limpia ni transforma datos — eso es trabajo del normalizer.
"""
import pandas as pd
from pathlib import Path

from config.config import (
    ARCHIVO_CARTOLA,
    ARCHIVO_LIBRO,
    COLUMNAS_CARTOLA,
    COLUMNAS_LIBRO,
)
from utils.logger import get_logger
from utils.exceptions import ArchivoNoEncontradoError, ColumnaFaltanteError

logger = get_logger(__name__)


def _leer_excel(ruta: Path, columnas_requeridas: dict) -> pd.DataFrame:
    """
    Función interna que carga un Excel y valida que tenga las columnas esperadas.

    Args:
        ruta:                Ruta al archivo .xlsx
        columnas_requeridas: Diccionario de config con las columnas esperadas
                             (ej: COLUMNAS_CARTOLA)

    Returns:
        DataFrame con los datos crudos del Excel

    Raises:
        ArchivoNoEncontradoError: Si el archivo no existe
        ColumnaFaltanteError:     Si falta alguna columna requerida
    """
    if not ruta.exists():
        raise ArchivoNoEncontradoError(ruta)

    logger.info(f"Leyendo archivo: {ruta.name}")

    df = pd.read_excel(ruta, sheet_name=0)

    logger.debug(f"Columnas encontradas: {list(df.columns)}")

    for nombre_interno, nombre_excel in columnas_requeridas.items():
        if nombre_excel not in df.columns:
            raise ColumnaFaltanteError(nombre_excel, ruta.name)

    logger.info(f"{len(df)} filas cargadas desde {ruta.name}")

    return df


def leer_cartola() -> pd.DataFrame:
    """Carga la cartola bancaria desde data/input/cartola_bancaria.xlsx"""
    return _leer_excel(ARCHIVO_CARTOLA, COLUMNAS_CARTOLA)


def leer_libro() -> pd.DataFrame:
    """Carga el libro auxiliar desde data/input/libro_auxiliar.xlsx"""
    return _leer_excel(ARCHIVO_LIBRO, COLUMNAS_LIBRO)