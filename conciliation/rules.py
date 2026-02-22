"""
rules.py — Reglas de negocio para la conciliación bancaria.

Define qué significa que dos transacciones "hacen match"
bajo criterios de tolerancia configurables.

Todas las funciones retornan bool y son puras:
  - No modifican datos
  - No tienen efectos secundarios
  - El mismo input siempre produce el mismo output
"""
import pandas as pd
from config.config import (
    TOLERANCIA_MONTO_PCT,
    TOLERANCIA_DIAS,
    TOLERANCIA_REFERENCIA,
)


def montos_coinciden(monto_a: float, monto_b: float) -> bool:
    """
    Verifica si dos montos coinciden dentro del ±2% configurado.

    Ejemplo con TOLERANCIA_MONTO_PCT = 0.02:
        100.000 vs 101.500  → True  (diferencia 1.5%)
        100.000 vs 103.000  → False (diferencia 3.0%)
        100.000 vs 100.000  → True  (diferencia 0.0%)

    Args:
        monto_a: Monto de la cartola
        monto_b: Monto del libro

    Returns:
        True si la diferencia porcentual es <= TOLERANCIA_MONTO_PCT
    """
    if pd.isna(monto_a) or pd.isna(monto_b):
        return False
    if monto_a == 0 and monto_b == 0:
        return True
    if monto_a == 0 or monto_b == 0:
        return False

    diferencia_pct = abs(monto_a - monto_b) / abs(monto_a)
    return diferencia_pct <= TOLERANCIA_MONTO_PCT


def fechas_coinciden(fecha_a: pd.Timestamp, fecha_b: pd.Timestamp) -> bool:
    """
    Verifica si dos fechas coinciden dentro del ±3 días configurado.

    Ejemplo con TOLERANCIA_DIAS = 3:
        15-ene vs 17-ene → True  (2 días de diferencia)
        15-ene vs 19-ene → False (4 días de diferencia)
        15-ene vs 15-ene → True  (0 días de diferencia)

    Args:
        fecha_a: Fecha de la cartola
        fecha_b: Fecha del libro

    Returns:
        True si la diferencia en días es <= TOLERANCIA_DIAS
    """
    if pd.isna(fecha_a) or pd.isna(fecha_b):
        return False

    diferencia_dias = abs((fecha_a - fecha_b).days)
    return diferencia_dias <= TOLERANCIA_DIAS


def referencias_coinciden(ref_a: str, ref_b: str) -> bool:
    """
    Verifica si dos referencias coinciden por sus primeros N caracteres.

    Usa coincidencia parcial porque los errores del dataset incluyen
    referencias truncadas o con caracteres faltantes al final.

    Ejemplo con TOLERANCIA_REFERENCIA = 4:
        "1234567890" vs "1234567890" → True  (match exacto)
        "1234567890" vs "1234X"      → True  (primeros 4 iguales)
        "1234567890" vs "9999"       → False (primeros 4 distintos)
        ""           vs "1234"       → False (referencia vacía)

    Args:
        ref_a: Referencia de la cartola (ya normalizada a uppercase)
        ref_b: Referencia del libro (ya normalizada a uppercase)

    Returns:
        True si los primeros TOLERANCIA_REFERENCIA caracteres son iguales
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

    Útil para detectar transacciones que son probablemente la misma
    pero con referencia incorrecta o faltante.
    """
    return (
        montos_coinciden(monto_a, monto_b) and
        fechas_coinciden(fecha_a, fecha_b) and
        not referencias_coinciden(ref_a, ref_b)
    )