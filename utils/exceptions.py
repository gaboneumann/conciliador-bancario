"""
exceptions.py — Excepciones personalizadas del Conciliador Bancario.

Jerarquía:
    ConciliadorError                    ← base de todas
    ├── IngestionError                  ← problemas al leer archivos
    │   ├── ArchivoNoEncontradoError
    │   └── ColumnaFaltanteError
    ├── NormalizacionError              ← problemas al limpiar datos
    └── ConciliacionError               ← problemas durante el matching
"""


class ConciliadorError(Exception):
    """
    Clase base de todas las excepciones del proyecto.
    Permite capturar cualquier error propio con un solo except:

        try:
            ...
        except ConciliadorError as e:
            logger.error(e)
    """
    pass


# Ingestion 

class IngestionError(ConciliadorError):
    """Error genérico al leer o cargar archivos de entrada."""
    pass


class ArchivoNoEncontradoError(IngestionError):
    """El archivo Excel no existe en la ruta esperada."""

    def __init__(self, ruta):
        self.ruta = ruta
        super().__init__(f"No se encontró el archivo: {ruta}")


class ColumnaFaltanteError(IngestionError):
    """El Excel no contiene una columna que el sistema espera."""

    def __init__(self, columna, archivo):
        self.columna = columna
        self.archivo = archivo
        super().__init__(
            f"Columna requerida '{columna}' no encontrada en '{archivo}'"
        )


# Normalización 

class NormalizacionError(ConciliadorError):
    """Error al limpiar o estandarizar los datos cargados."""

    def __init__(self, mensaje, columna=None):
        self.columna = columna
        detalle = f" (columna: '{columna}')" if columna else ""
        super().__init__(f"Error de normalización{detalle}: {mensaje}")


#  Conciliación 

class ConciliacionError(ConciliadorError):
    """Error durante el proceso de matching o clasificación."""
    pass