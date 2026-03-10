"""
main.py — Orquestador del Conciliador Bancario v2.

Ejecuta el flujo completo de conciliación:
    1. Leer archivos Excel de entrada (estructura v2 con RUT)
    2. Normalizar datos (fecha_valor, glosa, rut normalizado)
    3. Hacer matching (jerarquía RUT → Monto → Fecha → Referencia)
    4. Clasificar resultados (certeza Exacto/Sugerido/Manual, antigüedad)
    5. Calcular diferencia de saldo
    6. Escribir outputs (columnas v2, flags, acción recomendada)

Uso:
    python main.py                        # consola — usa rutas de config.py
    run(path_cartola, path_libro)         # GUI — usa rutas del file picker
"""
from pathlib import Path

from utils.logger import get_logger
from utils.exceptions import ConciliadorError

from ingestion.reader import leer_cartola, leer_libro
from ingestion.normalizer import normalizar_cartola, normalizar_libro
from conciliation.matcher import hacer_matching
from conciliation.classifier import clasificar, calcular_diferencia_saldo
from reporting.writer import escribir_resultado, escribir_sin_conciliar, escribir_hallazgos


logger = get_logger(__name__)


def run(path_cartola: Path | None = None, path_libro: Path | None = None) -> dict:
    """
    Ejecuta el flujo completo de conciliación.

    Args:
        path_cartola: Ruta al archivo cartola_bancaria.xlsx.
                      Si es None, usa ARCHIVO_CARTOLA de config.py.
        path_libro:   Ruta al archivo libro_auxiliar.xlsx.
                      Si es None, usa ARCHIVO_LIBRO de config.py.

    Returns:
        dict con métricas del proceso:
            - exactos, sugeridos, manuales: int
            - saldo_cartola, saldo_libro, diferencia: float
            - cuadratura: bool

    Raises:
        ConciliadorError: Error controlado del pipeline.
        Exception:        Error inesperado.
    """
    logger.info("=" * 50)
    logger.info("  Conciliador Bancario v2 — Iniciando proceso")
    logger.info("=" * 50)

    # — Paso 1: Lectura —
    logger.info("[1/6] Leyendo archivos de entrada...")
    df_cartola_crudo = leer_cartola(path_cartola)
    df_libro_crudo   = leer_libro(path_libro)

    # — Paso 2: Normalización —
    logger.info("[2/6] Normalizando datos...")
    cartola = normalizar_cartola(df_cartola_crudo)
    libro   = normalizar_libro(df_libro_crudo)

    # — Paso 3: Matching —
    logger.info("[3/6] Ejecutando matching...")
    resultados = hacer_matching(cartola, libro)

    # — Paso 4: Clasificación —
    logger.info("[4/6] Clasificando resultados...")
    df_resultado = clasificar(cartola, libro, resultados)

    # — Paso 5: Diferencia de saldo —
    logger.info("[5/6] Calculando diferencia de saldo...")
    saldo = calcular_diferencia_saldo(cartola, libro)

    # — Paso 6: Escritura —
    logger.info("[6/6] Escribiendo archivos de salida...")
    escribir_resultado(df_resultado, saldo)
    escribir_sin_conciliar(df_resultado)
    escribir_hallazgos(df_resultado, saldo, libro)

    logger.info("=" * 50)
    logger.info("  Proceso completado exitosamente")
    logger.info("=" * 50)

    # — Métricas para la GUI —
    conteos = df_resultado["certeza"].value_counts()
    return {
        "exactos":       int(conteos.get("Exacto",   0)),
        "sugeridos":     int(conteos.get("Sugerido", 0)),
        "manuales":      int(conteos.get("Manual",   0)),
        "saldo_cartola": float(saldo["saldo_cartola"]),
        "saldo_libro":   float(saldo["saldo_libro"]),
        "diferencia":    float(saldo["diferencia"]),
        "cuadratura":    saldo["cuadra"],
    }


def main():
    """Punto de entrada para ejecución desde consola."""
    try:
        run()
    except ConciliadorError as e:
        logger.error(f"Error en el proceso de conciliación: {e}")
        raise SystemExit(1)
    except Exception as e:
        logger.error(f"Error inesperado: {e}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()