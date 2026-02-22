"""
classifier.py — Clasificación y ensamblado del resultado de conciliación.

Responsabilidad: tomar los resultados del matcher y construir un
DataFrame final con toda la información necesaria para el reporte.

Columnas del DataFrame de salida:
    Lado cartola:
        fecha_cartola, monto_cartola, descripcion_cartola,
        referencia_cartola, banco_cartola

    Lado libro (match):
        fecha_libro, monto_libro, descripcion_libro,
        referencia_libro, codigo_libro

    Columnas calculadas (todos los matches):
        tipo_match  : "exacto", "parcial" o "sin_match"
        diff_monto  : diferencia absoluta en CLP
        diff_dias   : diferencia en días entre fechas

    Columnas diagnóstico (solo sin_match):
        motivo               : razón del no match
        fecha_cercana        : fecha del registro más cercano en libro
        monto_cercano        : monto del registro más cercano en libro
        descripcion_cercana  : descripción del registro más cercano en libro
        diff_monto_cercano   : diferencia vs el registro más cercano
"""
import pandas as pd
from utils.logger import get_logger

logger = get_logger(__name__)


def clasificar(
    cartola:    pd.DataFrame,
    libro:      pd.DataFrame,
    resultados: list[dict],
) -> pd.DataFrame:
    """
    Ensambla el DataFrame final de conciliación.

    Args:
        cartola    : DataFrame normalizado de la cartola
        libro      : DataFrame normalizado del libro
        resultados : Lista de dicts producida por hacer_matching()
                     Cada dict incluye: idx_cartola, idx_libro, tipo_match,
                     motivo, idx_libro_cercano

    Returns:
        DataFrame con una fila por transacción de la cartola,
        enriquecida con su match del libro y columnas calculadas.
    """
    logger.info("Clasificando resultados del matching...")

    filas = []

    for r in resultados:
        idx_c       = r["idx_cartola"]
        idx_l       = r["idx_libro"]
        tipo_match  = r["tipo_match"] if r["tipo_match"] else "sin_match"
        motivo      = r.get("motivo")
        idx_cercano = r.get("idx_libro_cercano")

        fila_c = cartola.loc[idx_c]

        # — Datos del lado cartola —
        fila = {
            "fecha_cartola":       fila_c["fecha"],
            "monto_cartola":       fila_c["monto"],
            "descripcion_cartola": fila_c["descripcion"],
            "referencia_cartola":  fila_c["referencia"],
            "banco_cartola":       fila_c["banco"],
        }

        # — Datos del lado libro (si hay match exacto o parcial) —
        if idx_l is not None:
            fila_l = libro.loc[idx_l]
            fila.update({
                "fecha_libro":       fila_l["fecha"],
                "monto_libro":       fila_l["monto"],
                "descripcion_libro": fila_l["descripcion"],
                "referencia_libro":  fila_l["referencia"],
                "codigo_libro":      fila_l["codigo"],
                "diff_monto":        abs(fila_c["monto"] - fila_l["monto"]),
                "diff_dias":         abs((fila_c["fecha"] - fila_l["fecha"]).days),
                "motivo":            None,
                "fecha_cercana":     None,
                "monto_cercano":     None,
                "descripcion_cercana": None,
                "diff_monto_cercano":  None,
            })

        # — Sin match: datos vacíos + diagnóstico —
        else:
            fila.update({
                "fecha_libro":       None,
                "monto_libro":       None,
                "descripcion_libro": None,
                "referencia_libro":  None,
                "codigo_libro":      None,
                "diff_monto":        None,
                "diff_dias":         None,
                "motivo":            motivo,
            })

            # — Datos del registro más cercano (si existe) —
            if idx_cercano is not None:
                fila_cercana = libro.loc[idx_cercano]
                fila.update({
                    "fecha_cercana":      fila_cercana["fecha"],
                    "monto_cercano":      fila_cercana["monto"],
                    "descripcion_cercana": fila_cercana["descripcion"],
                    "diff_monto_cercano": abs(fila_c["monto"] - fila_cercana["monto"]),
                })
            else:
                fila.update({
                    "fecha_cercana":      None,
                    "monto_cercano":      None,
                    "descripcion_cercana": None,
                    "diff_monto_cercano":  None,
                })

        fila["tipo_match"] = tipo_match
        filas.append(fila)

    df_resultado = pd.DataFrame(filas)

    # — Resumen en log —
    conteo = df_resultado["tipo_match"].value_counts()
    total  = len(df_resultado)
    logger.info(f"Total transacciones : {total}")
    for tipo, n in conteo.items():
        pct = n / total * 100
        logger.info(f"  {tipo:<12}: {n:>4} ({pct:.1f}%)")

    return df_resultado


def calcular_diferencia_saldo(
    cartola: pd.DataFrame,
    libro:   pd.DataFrame,
) -> dict:
    """
    Calcula la diferencia de saldo total entre cartola y libro.

    Compara la suma de todos los montos de cada archivo.
    Si la conciliación fuera perfecta, esta diferencia sería cero.

    Args:
        cartola: DataFrame normalizado de la cartola
        libro:   DataFrame normalizado del libro

    Returns:
        Dict con:
            saldo_cartola   : suma total de montos en la cartola
            saldo_libro     : suma total de montos en el libro
            diferencia      : saldo_cartola - saldo_libro
            cuadra          : True si la diferencia es exactamente 0
    """
    saldo_cartola = cartola["monto"].sum()
    saldo_libro   = libro["monto"].sum()
    diferencia    = saldo_cartola - saldo_libro

    logger.info(f"Saldo cartola : {saldo_cartola:,.0f}")
    logger.info(f"Saldo libro   : {saldo_libro:,.0f}")
    logger.info(f"Diferencia    : {diferencia:,.0f}")

    return {
        "saldo_cartola": round(saldo_cartola, 2),
        "saldo_libro":   round(saldo_libro,   2),
        "diferencia":    round(diferencia,    2),
        "cuadra":        abs(diferencia) < 1,   # tolerancia de $1 por redondeos
    }


def separar_sin_conciliar(df_resultado: pd.DataFrame) -> pd.DataFrame:
    """
    Filtra solo las transacciones sin match para el reporte de partidas abiertas.

    Args:
        df_resultado: DataFrame completo producido por clasificar()

    Returns:
        DataFrame con solo las filas de tipo_match == "sin_match",
        incluyendo columnas de diagnóstico.
    """
    sin_conciliar = df_resultado[df_resultado["tipo_match"] == "sin_match"].copy()
    logger.info(f"Partidas sin conciliar: {len(sin_conciliar)}")
    return sin_conciliar.reset_index(drop=True)