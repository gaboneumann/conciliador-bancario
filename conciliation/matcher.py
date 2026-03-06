"""
matcher.py — Algoritmo de matching entre cartola y libro auxiliar (v2.1).

Jerarquía de matching definida por contador:
    1. RUT      → coincidencia exacta (llave maestra — descarte inmediato si falla)
    2. Monto    → diferencia ≤ min(2%, $5.000 CLP)  |  o ratio ×1.19 (IVA)
    3. Fecha    → fecha_valor vs fecha_contable ±5 días (ampliado desde ±3)
    4. Nº Doc   → primeros 6 caracteres (solo desempate)

Certeza resultante:
    Exacto   → RUT con DV + Monto exacto + Fecha mismo mes ±3 días + Referencia
    Sugerido → cualquiera de:
               · RUT sin DV
               · Desfase de mes (Partida en Conciliación)
               · Fecha fuera de ±3 días pero dentro de ±5 días
               · Monto con diferencia > $0 pero ≤ $5.000 (materialidad)
               · Monto con ratio ×1.19 (posible neto vs bruto IVA)
    Manual   → sin match automático

CAMBIOS v2.1:
─────────────────────────────────────────────────────────────────────────────
FIX 1 · _evaluar_candidato() — IVA genera Sugerido
    Antes : montos_coinciden() False → return None → Manual
    Ahora : montos_coinciden() False → detectar_iva() → si True →
            certeza Sugerido + flag_iva, continuar con fecha
    Impacto: ~31 filas IVA pasan de Manual → Sugerido

FIX 2 · _evaluar_candidato() — Materialidad genera Sugerido
    Antes : montos_coinciden() True → certeza Exacto (sin distinción de diff)
    Ahora : montos_coinciden() True + diff > 0 → certeza_monto = Sugerido
            montos_coinciden() True + diff == 0 → certeza_monto = Exacto
    Impacto: diferencias de $1–$4.999 se clasifican como Sugerido, no Exacto

FIX 3 · config.py — TOLERANCIA_DIAS 3 → 5
    El matcher ya manejaba fechas fuera de rango como Sugerido,
    pero solo las "veía" dentro de la ventana de búsqueda de ±3 días.
    Con ±5 días, candidatos a 4-5 días de distancia entran al loop.
    Cambio en config.py: TOLERANCIA_DIAS = 5
    Este archivo NO cambia la lógica de fecha — solo se beneficia del config.
─────────────────────────────────────────────────────────────────────────────
"""
import pandas as pd
from utils.logger import get_logger
from utils.rut_utils import ruts_coinciden
from conciliation.rules import (
    montos_coinciden,
    fechas_coinciden,
    mismo_mes,
    detectar_iva,
    referencias_coinciden,
)
from config.config import (
    CERTEZA_EXACTO,
    CERTEZA_SUGERIDO,
    CERTEZA_MANUAL,
    FLAG_PARTIDA_CONCILIACION,
    FLAG_IVA,
    TOLERANCIA_MONTO_ABS_MAX,
)

logger = get_logger(__name__)

# ─── Motivos de sin match ─────────────────────────────────────────────────────
MOTIVO_FECHA_FUERA_RANGO   = "Monto coincide pero fecha fuera de rango"
MOTIVO_MONTO_NO_ENCONTRADO = "Fecha coincide pero monto no encontrado"
MOTIVO_POSIBLE_IVA         = "Posible Neto vs Bruto (×1.19)"
MOTIVO_AUSENTE_EN_LIBRO    = "Transacción ausente en libro auxiliar"


def _diagnosticar_sin_match(
    monto_c: float,
    fecha_c: pd.Timestamp,
    rut_c: str,
    libro: pd.DataFrame,
) -> tuple[str, int | None, str]:
    """
    Busca en todo el libro la causa más probable del no match.

    Prioridad de diagnóstico:
        1. RUT + Monto coinciden pero fecha fuera de rango
        2. RUT + Posible IVA (ratio ×1.19)
        3. RUT + Fecha coinciden pero monto no encontrado
        4. Monto coincide sin RUT
        5. Fecha coincide sin RUT
        6. Ausente en libro

    Returns:
        Tuple (motivo, idx_cercano, flag_iva)
    """
    flag_iva = ""

    for idx_l, fila_l in libro.iterrows():
        rut_match = ruts_coinciden(rut_c, fila_l["rut"])

        if rut_match["coincide"]:
            if montos_coinciden(monto_c, fila_l["monto"]):
                return MOTIVO_FECHA_FUERA_RANGO, idx_l, flag_iva
            elif detectar_iva(monto_c, fila_l["monto"]):
                flag_iva = FLAG_IVA
                return MOTIVO_POSIBLE_IVA, idx_l, flag_iva

    for idx_l, fila_l in libro.iterrows():
        rut_match = ruts_coinciden(rut_c, fila_l["rut"])

        if rut_match["coincide"]:
            if fechas_coinciden(fecha_c, fila_l["fecha_contable"]):
                return MOTIVO_MONTO_NO_ENCONTRADO, idx_l, flag_iva

    for idx_l, fila_l in libro.iterrows():
        if montos_coinciden(monto_c, fila_l["monto"]):
            return MOTIVO_FECHA_FUERA_RANGO, idx_l, flag_iva

    for idx_l, fila_l in libro.iterrows():
        if fechas_coinciden(fecha_c, fila_l["fecha_contable"]):
            return MOTIVO_MONTO_NO_ENCONTRADO, idx_l, flag_iva

    return MOTIVO_AUSENTE_EN_LIBRO, None, flag_iva


def _evaluar_candidato(
    fila_c: pd.Series,
    fila_l: pd.Series,
) -> dict | None:
    """
    Evalúa un candidato del libro contra una fila de cartola
    siguiendo la jerarquía RUT → Monto → Fecha → Referencia.

    Returns:
        dict con certeza, flag_conciliacion, flag_iva y regla_aplicada
        None si el candidato no pasa la jerarquía
    """
    flag_iva      = ""
    certeza_monto = CERTEZA_EXACTO

    # — Paso 1: RUT (llave maestra) —
    rut_result = ruts_coinciden(fila_c["rut"], fila_l["rut"])
    if not rut_result["coincide"]:
        return None

    certeza_rut = rut_result["certeza"]

    # — Paso 2: Monto —────────────────────────────────────────────────────────
    # FIX 1: si monto no coincide por tolerancia normal, verificar ratio IVA.
    # FIX 2: si monto coincide con diff > 0, marcar certeza_monto = Sugerido.
    monto_c = fila_c["monto"]
    monto_l = fila_l["monto"]

    if montos_coinciden(monto_c, monto_l):
        # FIX 2: distinguir diff=0 (Exacto) de diff>0 (materialidad → Sugerido)
        diff_monto = abs(monto_c - monto_l)
        if diff_monto > 0:
            certeza_monto = CERTEZA_SUGERIDO   # diferencia pequeña pero real
        # si diff == 0 → certeza_monto queda CERTEZA_EXACTO

    elif detectar_iva(monto_c, monto_l):
        # FIX 1: ratio ×1.19 detectado → match válido con certeza Sugerido
        certeza_monto = CERTEZA_SUGERIDO
        flag_iva      = FLAG_IVA

    else:
        # Monto no pasa ninguna regla → descartar candidato
        return None

    # — Paso 3: Fecha Valor vs Fecha Contable —
    # TOLERANCIA_DIAS en config.py controla la ventana de búsqueda.
    # FIX 3 (en config.py): ampliar de 3 → 5 días.
    # Este bloque NO cambia — solo se beneficia del nuevo valor de config.
    fecha_valor    = fila_c["fecha_valor"]
    fecha_contable = fila_l["fecha_contable"]

    dentro_rango      = fechas_coinciden(fecha_valor, fecha_contable)
    mismo_mes_flag    = mismo_mes(fecha_valor, fecha_contable)

    flag_conciliacion = ""
    certeza_fecha     = CERTEZA_EXACTO

    if not mismo_mes_flag:
        flag_conciliacion = FLAG_PARTIDA_CONCILIACION
        certeza_fecha     = CERTEZA_SUGERIDO
    elif not dentro_rango:
        # Fecha fuera de ±3 días pero dentro de la ventana ampliada (±5 días)
        certeza_fecha = CERTEZA_SUGERIDO

    # — Paso 4: Referencia (solo desempate) —
    ref_coincide = referencias_coinciden(
        fila_c["nro_documento"],
        fila_l["nro_referencia"],
    )

    # — Certeza final: la más baja entre RUT, Monto y Fecha —
    niveles = [certeza_rut, certeza_monto, certeza_fecha]
    if any(n == CERTEZA_SUGERIDO or n == "sugerido" for n in niveles):
        certeza_final = CERTEZA_SUGERIDO
    else:
        certeza_final = CERTEZA_EXACTO

    # — Regla aplicada —
    partes = ["RUT", "Monto", "Fecha"]
    if ref_coincide:
        partes.append("Referencia")
    if flag_iva:
        partes.append("IVA ×1.19")
    regla_aplicada = " + ".join(partes)

    return {
        "certeza":            certeza_final,
        "flag_conciliacion":  flag_conciliacion,
        "flag_iva":           flag_iva,
        "regla_aplicada":     regla_aplicada,
    }


def hacer_matching(
    cartola: pd.DataFrame,
    libro: pd.DataFrame,
) -> list[dict]:
    """
    Compara cada fila de la cartola contra el libro usando la jerarquía v2.

    Returns:
        Lista de dicts con resultado de cada transacción.
    """
    logger.info(f"Iniciando matching v2: {len(cartola)} filas cartola vs {len(libro)} filas libro")

    resultados          = []
    indices_disponibles = set(libro.index)

    for idx_c, fila_c in cartola.iterrows():

        match_encontrado  = None
        certeza           = CERTEZA_MANUAL
        flag_conciliacion = ""
        flag_iva          = ""
        regla_aplicada    = ""
        motivo            = None
        idx_cercano       = None

        for idx_l in list(indices_disponibles):
            fila_l     = libro.loc[idx_l]
            evaluacion = _evaluar_candidato(fila_c, fila_l)

            if evaluacion is not None:
                match_encontrado  = idx_l
                certeza           = evaluacion["certeza"]
                flag_conciliacion = evaluacion["flag_conciliacion"]
                flag_iva          = evaluacion["flag_iva"]
                regla_aplicada    = evaluacion["regla_aplicada"]
                break

        if match_encontrado is not None:
            tipo_match = certeza
        else:
            tipo_match = CERTEZA_MANUAL
            motivo, idx_cercano, flag_iva = _diagnosticar_sin_match(
                fila_c["monto"],
                fila_c["fecha_valor"],
                fila_c["rut"],
                libro,
            )

        resultados.append({
            "idx_cartola":        idx_c,
            "idx_libro":          match_encontrado,
            "tipo_match":         tipo_match,
            "certeza":            certeza if match_encontrado is not None else CERTEZA_MANUAL,
            "motivo":             motivo,
            "flag_conciliacion":  flag_conciliacion,
            "flag_iva":           flag_iva,
            "regla_aplicada":     regla_aplicada,
            "idx_libro_cercano":  idx_cercano,
        })

        if match_encontrado is not None:
            indices_disponibles.discard(match_encontrado)

    exactos   = sum(1 for r in resultados if r["tipo_match"] == CERTEZA_EXACTO)
    sugeridos = sum(1 for r in resultados if r["tipo_match"] == CERTEZA_SUGERIDO)
    manuales  = sum(1 for r in resultados if r["tipo_match"] == CERTEZA_MANUAL)

    logger.info(f"Matching completado → exactos: {exactos} | sugeridos: {sugeridos} | manuales: {manuales}")

    return resultados