"""
logger.py — Configuración central de logging.

Crea un logger que escribe simultáneamente en:
  - Consola     → para ver el progreso en tiempo real
  - Archivo     → para guardar historial de ejecuciones
"""

import logging
from config.config import ARCHIVO_LOG

# Formato de cada línea del log
FORMATO = "%(asctime)s | %(levelname)-8s | %(message)s"
FORMATO_FECHA = "%Y-%m-%d %H:%M:%S"

def get_logger(nombre: str) -> logging.Logger:
    """
    Retorna un logger configurado con dos destinos: consola y archivo.

    Uso:
        from utils.logger import get_logger
        logger = get_logger(__name__)
        logger.info("Proceso iniciado")
        logger.warning("Valor nulo encontrado")
        logger.error("No se pudo leer el archivo")
    """
    logger = logging.getLogger(nombre)

    # Evita agregar handlers duplicados si la función se llama más de una vez
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter(FORMATO, datefmt=FORMATO_FECHA)

    # — Handler 1: Consola —
    handler_consola = logging.StreamHandler()
    handler_consola.setLevel(logging.INFO)   # muestra INFO, WARNING, ERROR
    handler_consola.setFormatter(formatter)

    # — Handler 2: Archivo —
    ARCHIVO_LOG.parent.mkdir(parents=True, exist_ok=True)
    handler_archivo = logging.FileHandler(ARCHIVO_LOG, encoding="utf-8")
    handler_archivo.setLevel(logging.DEBUG)  # guarda TODO, incluyendo DEBUG
    handler_archivo.setFormatter(formatter)

    logger.addHandler(handler_consola)
    logger.addHandler(handler_archivo)

    return logger