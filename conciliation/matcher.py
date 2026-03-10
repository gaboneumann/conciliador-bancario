"""
matcher.py — Algoritmo de matching entre cartola y libro auxiliar (v2.2).

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

CAMBIOS v2.2:
─────────────────────────────────────────────────────────────────────────────
OPT 1 · hacer_matching() — índice por RUT
    Antes : O(n²) — por cada fila cartola itera todo el libro
    Ahora : O(n)  — pre-construye dict {cuerpo_rut → [indices]}
            por cada fila cartola busca solo en su bucket de RUT
    Impacto: ~992.000 iteraciones → ~10–50 por fila

OPT 2 · _diagnosticar_sin_match() — mismo índice por RUT
    Antes : 4 loops completos sobre todo el libro
    Ahora : bucket por RUT para pasos 1–3
            fallback al libro completo solo para pasos 4–5 (sin RUT)
    Impacto: diagnóstico proporcional al tamaño del bucket, no del libro

OPT 3 · _construir_indice_rut() — función auxiliar
    Pre-procesa el libro una sola vez antes del loop principal.
    Normaliza cada RUT y agrupa índices por cuerpo.
    RUTs inválidos van al bucket "SIN_RUT".
─────────────────────────────────────────────────────────────────────────────
"""
import pandas as pd
from collections import defaultdict
from utils.logger import get_logger
from utils.rut_utils import ruts_coinciden, normalizar_rut
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

_SIN_RUT = "SIN_RUT"


# ─── Índice por RUT ───────────────────────────────────────────────────────────

def _construir_indice_rut(libro: pd.DataFrame) -> dict[str, list[int]]:
    """
    Pre-procesa el libro una sola vez y agrupa índices por cuerpo de RUT.

    Returns:
        dict {cuerpo_rut: [idx1, idx2, ...]}
        RUTs inválidos van al bucket _SIN_RUT.
    """
    indice = defaultdict(list)

    for idx, fila in libro.iterrows():
        norm = normalizar_rut(fila["rut"])
        if norm["es_valido"]:
            cuerpo = norm["canonical"].split("-")[0]
        else:
            cuerpo = _SIN_RUT
        indice[cuerpo].append(idx)

    return indice


def _cuerpo_rut(rut_raw) -> str:
    """
    Extrae el cuerpo normalizado de un RUT crudo.
    Retorna _SIN_RUT si el RUT es inválido.
    """
    norm = normalizar_rut(rut_raw)
    if not norm["es_valido"]:
        return _SIN_RUT
    return norm["canonical"].split("-")[0]


# ─── Diagnóstico ──────────────────────────────────────────────────────────────

def _diagnosticar_sin_match(
    monto_c: float,
    fecha_c: pd.Timestamp,
    rut_c: str,
    libro: pd.DataFrame,
    indice_rut: dict[str, list[int]],
) -> tuple[str, int | None, str]:
    """
    Busca en el libro la causa más probable del no match.

    Prioridad de diagnóstico:
        1. RUT + Monto coinciden pero fecha fuera de rango
        2. RUT + Posible IVA (ratio ×1.19)
        3. RUT + Fecha coinciden pero monto no encontrado
        4. Monto coincide sin RUT (fallback libro completo)
        5. Fecha coincide sin RUT (fallback libro completo)
        6. Ausente en libro

    Returns:
        Tuple (motivo, idx_cercano, flag_iva)
    """
    flag_iva = ""
    cuerpo_c = _cuerpo_rut(rut_c)

    # Pasos 1–3: buscar solo en el bucket del RUT
    bucket = indice_rut.get(cuerpo_c, [])

    for idx_l in bucket:
        fila_l = libro.loc[idx_l]
        if montos_coinciden(monto_c, fila_l["monto"]):
            return MOTIVO_FECHA_FUERA_RANGO, idx_l, flag_iva
        elif detectar_iva(monto_c, fila_l["monto"]):
            return MOTIVO_POSIBLE_IVA, idx_l, FLAG_IVA

    for idx_l in bucket:
        fila_l = libro.loc[idx_l]
        if fechas_coinciden(fecha_c, fila_l["fecha_contable"]):
            return MOTIVO_MONTO_NO_ENCONTRADO, idx_l, flag_iva

    # Pasos 4–5: fallback al libro completo (sin filtro de RUT)
    for idx_l, fila_l in libro.iterrows():
        if montos_coinciden(monto_c, fila_l["monto"]):
            return MOTIVO_FECHA_FUERA_RANGO, idx_l, flag_iva

    for idx_l, fila_l in libro.iterrows():
        if fechas_coinciden(fecha_c, fila_l["fecha_contable"]):
            return MOTIVO_MONTO_NO_ENCONTRADO, idx_l, flag_iva

    return MOTIVO_AUSENTE_EN_LIBRO, None, flag_iva


# ─── Evaluación de candidato ──────────────────────────────────────────────────

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

    # — Paso 2: Monto —
    monto_c = fila_c["monto"]
    monto_l = fila_l["monto"]

    if montos_coinciden(monto_c, monto_l):
        diff_monto = abs(monto_c - monto_l)
        if diff_monto > 0:
            certeza_monto = CERTEZA_SUGERIDO
    elif detectar_iva(monto_c, monto_l):
        certeza_monto = CERTEZA_SUGERIDO
        flag_iva      = FLAG_IVA
    else:
        return None

    # — Paso 3: Fecha Valor vs Fecha Contable —
    fecha_valor    = fila_c["fecha_valor"]
    fecha_contable = fila_l["fecha_contable"]

    dentro_rango   = fechas_coinciden(fecha_valor, fecha_contable)
    mismo_mes_flag = mismo_mes(fecha_valor, fecha_contable)

    flag_conciliacion = ""
    certeza_fecha     = CERTEZA_EXACTO

    if not mismo_mes_flag:
        flag_conciliacion = FLAG_PARTIDA_CONCILIACION
        certeza_fecha     = CERTEZA_SUGERIDO
    elif not dentro_rango:
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
        "certeza":           certeza_final,
        "flag_conciliacion": flag_conciliacion,
        "flag_iva":          flag_iva,
        "regla_aplicada":    regla_aplicada,
    }


# ─── Loop principal ───────────────────────────────────────────────────────────

def hacer_matching(
    cartola: pd.DataFrame,
    libro: pd.DataFrame,
    progreso_callback=None,
) -> list[dict]:
    """
    Compara cada fila de la cartola contra el libro usando la jerarquía v2.

    Args:
        cartola:            DataFrame normalizado de la cartola bancaria.
        libro:              DataFrame normalizado del libro auxiliar.
        progreso_callback:  Función opcional fn(actual, total) para reportar
                            avance. La GUI la usa para actualizar la barra
                            de progreso. Si es None, se ignora.

    Returns:
        Lista de dicts con resultado de cada transacción.
    """
    logger.info(f"Iniciando matching v2.2: {len(cartola)} filas cartola vs {len(libro)} filas libro")

    # OPT: pre-construir índice por RUT una sola vez
    indice_rut          = _construir_indice_rut(libro)
    resultados          = []
    indices_disponibles = set(libro.index)
    total               = len(cartola)

    for i, (idx_c, fila_c) in enumerate(cartola.iterrows()):

        # Callback de progreso para la GUI
        if progreso_callback:
            progreso_callback(i + 1, total)

        match_encontrado  = None
        certeza           = CERTEZA_MANUAL
        flag_conciliacion = ""
        flag_iva          = ""
        regla_aplicada    = ""
        motivo            = None
        idx_cercano       = None

        # OPT: buscar solo en el bucket del RUT de esta fila
        cuerpo_c = _cuerpo_rut(fila_c["rut"])
        bucket   = [
            idx_l for idx_l in indice_rut.get(cuerpo_c, [])
            if idx_l in indices_disponibles
        ]

        # Fallback: si el RUT es inválido, buscar en todo el libro disponible
        if cuerpo_c == _SIN_RUT:
            bucket = list(indices_disponibles)

        for idx_l in bucket:
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
            indices_disponibles.discard(match_encontrado)
        else:
            tipo_match = CERTEZA_MANUAL
            motivo, idx_cercano, flag_iva = _diagnosticar_sin_match(
                fila_c["monto"],
                fila_c["fecha_valor"],
                fila_c["rut"],
                libro,
                indice_rut,
            )

        resultados.append({
            "idx_cartola":       idx_c,
            "idx_libro":         match_encontrado,
            "tipo_match":        tipo_match,
            "certeza":           certeza if match_encontrado is not None else CERTEZA_MANUAL,
            "motivo":            motivo,
            "flag_conciliacion": flag_conciliacion,
            "flag_iva":          flag_iva,
            "regla_aplicada":    regla_aplicada,
            "idx_libro_cercano": idx_cercano,
        })

    exactos   = sum(1 for r in resultados if r["tipo_match"] == CERTEZA_EXACTO)
    sugeridos = sum(1 for r in resultados if r["tipo_match"] == CERTEZA_SUGERIDO)
    manuales  = sum(1 for r in resultados if r["tipo_match"] == CERTEZA_MANUAL)

    logger.info(f"Matching completado → exactos: {exactos} | sugeridos: {sugeridos} | manuales: {manuales}")

    return resultados