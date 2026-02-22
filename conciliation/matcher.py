"""
matcher.py — Algoritmo de matching entre cartola y libro del banco.

Responsabilidad: encontrar qué transacción de la cartola corresponde
a qué transacción del libro, respetando las tolerancias definidas en rules.py

Resultado: lista de dicts con:
    idx_cartola      : índice en cartola
    idx_libro        : índice en libro (None si sin match)
    tipo_match       : "exacto", "parcial" o None
    motivo           : razón del no match (solo cuando tipo_match es None)
    idx_libro_cercano: índice del registro más cercano en libro (solo sin match)
"""
import pandas as pd
from utils.logger import get_logger
from conciliation.rules import (
    es_match_exacto,
    es_match_parcial,
    montos_coinciden,
    fechas_coinciden,
)

logger = get_logger(__name__)

# Motivos posibles de no match
MOTIVO_FECHA_FUERA_RANGO  = "Monto coincide pero fecha fuera de rango"
MOTIVO_MONTO_NO_ENCONTRADO = "Fecha coincide pero monto no encontrado"
MOTIVO_AUSENTE_EN_LIBRO    = "Transacción ausente en libro"


def _diagnosticar_sin_match(
    monto_c: float,
    fecha_c: pd.Timestamp,
    libro: pd.DataFrame,
) -> tuple[str, int | None]:
    """
    Busca en TODO el libro (incluyendo filas ya usadas) el registro
    más cercano a la transacción de la cartola y determina por qué falló.

    Busca en todo el libro porque la fila más cercana puede estar usada —
    pero igual queremos mostrarla como referencia diagnóstica.

    Args:
        monto_c: Monto de la transacción sin match
        fecha_c: Fecha de la transacción sin match
        libro:   DataFrame completo del libro

    Returns:
        Tuple (motivo, idx_libro_cercano)
        motivo           : string describiendo la razón del no match
        idx_libro_cercano: índice de la fila más cercana en el libro
    """
    idx_cercano = None

    # — Prioridad 1: ¿existe monto similar pero fecha fuera de rango? —
    for idx_l, fila_l in libro.iterrows():
        if montos_coinciden(monto_c, fila_l["monto"]):
            idx_cercano = idx_l
            return MOTIVO_FECHA_FUERA_RANGO, idx_cercano

    # — Prioridad 2: ¿existe fecha similar pero monto distinto? —
    for idx_l, fila_l in libro.iterrows():
        if fechas_coinciden(fecha_c, fila_l["fecha"]):
            idx_cercano = idx_l
            return MOTIVO_MONTO_NO_ENCONTRADO, idx_cercano

    # — Prioridad 3: no hay nada parecido —
    return MOTIVO_AUSENTE_EN_LIBRO, None


def hacer_matching(
    cartola: pd.DataFrame,
    libro: pd.DataFrame,
) -> list[dict]:
    """
    Compara cada fila de la cartola contra el libro y encuentra matches.

    Algoritmo:
        Para cada transacción de la cartola:
            1. Busca match exacto en el libro (monto + fecha + referencia)
            2. Si no encuentra, busca match parcial (monto + fecha)
            3. Si no encuentra ninguno, diagnostica por qué falló
        Una fila del libro solo puede usarse una vez para match.

    Args:
        cartola : DataFrame normalizado de la cartola personal
        libro   : DataFrame normalizado del libro del banco

    Returns:
        Lista de dicts con el resultado de cada transacción:
        [
            {
                "idx_cartola"      : 0,
                "idx_libro"        : 5,
                "tipo_match"       : "exacto",
                "motivo"           : None,
                "idx_libro_cercano": None,
            },
            {
                "idx_cartola"      : 3,
                "idx_libro"        : None,
                "tipo_match"       : None,
                "motivo"           : "Monto coincide pero fecha fuera de rango",
                "idx_libro_cercano": 12,
            },
            ...
        ]
    """
    logger.info(f"Iniciando matching: {len(cartola)} filas cartola vs {len(libro)} filas libro")

    resultados = []

    # Índices del libro que aún no han sido utilizados en ningún match
    indices_disponibles = set(libro.index)

    for idx_c, fila_c in cartola.iterrows():

        monto_c = fila_c["monto"]
        fecha_c = fila_c["fecha"]
        ref_c   = fila_c["referencia"]

        match_encontrado = None
        tipo_match       = None
        motivo           = None
        idx_cercano      = None

        # — Paso 1: buscar match exacto —
        for idx_l in list(indices_disponibles):
            fila_l = libro.loc[idx_l]
            if es_match_exacto(
                monto_c, fecha_c, ref_c,
                fila_l["monto"], fila_l["fecha"], fila_l["referencia"]
            ):
                match_encontrado = idx_l
                tipo_match       = "exacto"
                break

        # — Paso 2: si no hay exacto, buscar match parcial —
        if match_encontrado is None:
            for idx_l in list(indices_disponibles):
                fila_l = libro.loc[idx_l]
                if es_match_parcial(
                    monto_c, fecha_c, ref_c,
                    fila_l["monto"], fila_l["fecha"], fila_l["referencia"]
                ):
                    match_encontrado = idx_l
                    tipo_match       = "parcial"
                    break

        # — Paso 3: si no hay match, diagnosticar por qué —
        if match_encontrado is None:
            motivo, idx_cercano = _diagnosticar_sin_match(monto_c, fecha_c, libro)

        # — Registrar resultado —
        resultados.append({
            "idx_cartola":       idx_c,
            "idx_libro":         match_encontrado,
            "tipo_match":        tipo_match,
            "motivo":            motivo,
            "idx_libro_cercano": idx_cercano,
        })

        # — Marcar fila del libro como usada —
        if match_encontrado is not None:
            indices_disponibles.discard(match_encontrado)

    # — Resumen —
    exactos   = sum(1 for r in resultados if r["tipo_match"] == "exacto")
    parciales = sum(1 for r in resultados if r["tipo_match"] == "parcial")
    sin_match = sum(1 for r in resultados if r["tipo_match"] is None)

    logger.info(f"Matching completado → exactos: {exactos} | parciales: {parciales} | sin match: {sin_match}")

    return resultados