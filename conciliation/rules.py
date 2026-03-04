"""
rules.py — Reglas de negocio para la conciliación bancaria (v2).

Todas las funciones son puras:
  - No modifican datos
  - No tienen efectos secundarios
  - El mismo input siempre produce el mismo output
"""
import pandas as pd
from config.config import (
    TOLERANCIA_MONTO_PCT,
    TOLERANCIA_MONTO_ABS_MAX,
    TOLERANCIA_DIAS,
    TOLERANCIA_REFERENCIA,
    FACTOR_IVA,
    TOLERANCIA_IVA,
)


def montos_coinciden(monto_a: float, monto_b: float) -> bool:
    """
    Verifica si dos montos coinciden dentro de:
        min(±2% del monto, $5.000 CLP)

    El cap absoluto evita que diferencias de millones pasen
    el filtro por estar bajo el 2% relativo.

    Ejemplo:
        100.000 vs 101.500  → True  (1.5% < 2%, $1.500 < $5.000)
        500.000 vs 505.001  → False ($5.001 > cap de $5.000)
      1.000.000 vs 1.004.999 → True  ($4.999 < cap)
      1.000.000 vs 1.005.001 → False ($5.001 > cap)
    """
    if pd.isna(monto_a) or pd.isna(monto_b):
        return False
    if monto_a == 0 and monto_b == 0:
        return True
    if monto_a == 0 or monto_b == 0:
        return False

    tolerancia = min(abs(monto_a) * TOLERANCIA_MONTO_PCT, TOLERANCIA_MONTO_ABS_MAX)
    return abs(monto_a - monto_b) <= tolerancia


def fechas_coinciden(fecha_a: pd.Timestamp, fecha_b: pd.Timestamp) -> bool:
    """
    Verifica si dos fechas coinciden dentro del ±3 días configurado.

    Args:
        fecha_a: Fecha Valor de la cartola
        fecha_b: Fecha Contable del libro

    Returns:
        True si la diferencia en días es <= TOLERANCIA_DIAS
    """
    if pd.isna(fecha_a) or pd.isna(fecha_b):
        return False

    diferencia_dias = abs((fecha_a - fecha_b).days)
    return diferencia_dias <= TOLERANCIA_DIAS


def mismo_mes(fecha_a: pd.Timestamp, fecha_b: pd.Timestamp) -> bool:
    """
    Verifica si dos fechas pertenecen al mismo año y mes contable.

    Usada para detectar desfase de mes y activar el flag
    Partida en Conciliación.

    Returns:
        True si año y mes son iguales en ambas fechas.
    """
    fa = pd.Timestamp(fecha_a)
    fb = pd.Timestamp(fecha_b)
    return fa.year == fb.year and fa.month == fb.month


def detectar_iva(monto_a: float, monto_b: float) -> bool:
    """
    Detecta si la diferencia entre dos montos corresponde al ratio IVA (×1.19).

    Útil para diagnosticar partidas sin match donde uno registra
    neto y el otro bruto de IVA.

    Returns:
        True si el ratio entre montos es aproximadamente 1.19 (±1%)
    """
    if not monto_a or not monto_b:
        return False

    ratio = abs(monto_a) / abs(monto_b)
    return (
        abs(ratio - FACTOR_IVA) <= TOLERANCIA_IVA or
        abs(1 / ratio - FACTOR_IVA) <= TOLERANCIA_IVA
    )


def referencias_coinciden(ref_a: str, ref_b: str) -> bool:
    """
    Verifica si dos referencias coinciden por sus primeros N caracteres.

    En v2 la tolerancia sube de 4 a 6 caracteres (TOLERANCIA_REFERENCIA).
    Solo actúa como desempate — nunca descarta un candidato.

    Returns:
        True si los primeros TOLERANCIA_REFERENCIA caracteres son iguales.
    """
    if not ref_a or not ref_b:
        return False

    return ref_a[:TOLERANCIA_REFERENCIA] == ref_b[:TOLERANCIA_REFERENCIA]


def es_match_exacto(monto_a: float, fecha_a: pd.Timestamp, ref_a: str,
                    monto_b: float, fecha_b: pd.Timestamp, ref_b: str) -> bool:
    """
    Verifica si dos transacciones hacen match exacto en los tres criterios.
    Los tres deben cumplirse simultáneamente.
    """
    return (
        montos_coinciden(monto_a, monto_b) and
        fechas_coinciden(fecha_a, fecha_b) and
        referencias_coinciden(ref_a, ref_b)
    )


def es_match_parcial(monto_a: float, fecha_a: pd.Timestamp, ref_a: str,
                     monto_b: float, fecha_b: pd.Timestamp, ref_b: str) -> bool:
    """
    Verifica si dos transacciones hacen match parcial:
    monto y fecha coinciden, pero la referencia no.
    """
    return (
        montos_coinciden(monto_a, monto_b) and
        fechas_coinciden(fecha_a, fecha_b) and
        not referencias_coinciden(ref_a, ref_b)
    )