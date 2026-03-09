"""
classifier.py — Clasificación y ensamblado del resultado de conciliación (v2).

Columnas de salida:
    Lado cartola:
        fecha_operacion_cartola, fecha_valor_cartola, glosa_cartola,
        rut_cartola, monto_cartola, nro_documento_cartola, banco_cartola

    Lado libro (match):
        fecha_contable_libro, glosa_libro, rut_libro, monto_libro,
        nro_referencia_libro, nro_comprobante_libro, codigo_tx_libro

    Columnas de match:
        tipo_match, certeza, regla_aplicada,
        diff_monto, diff_dias,
        flag_conciliacion, flag_iva

    Columnas de antigüedad:
        dias_antiguedad, tramo_antiguedad, accion_recomendada

    Columnas de diagnóstico (solo sin match):
        motivo, fecha_cercana, monto_cercano, glosa_cercana, diff_monto_cercano
"""
import pandas as pd
from datetime import date
from utils.logger import get_logger
from config.config import (
    CERTEZA_EXACTO,
    CERTEZA_SUGERIDO,
    CERTEZA_MANUAL,
    FLAG_PARTIDA_CONCILIACION,
    FLAG_IVA,
    ANTIGUEDAD_VIGENTE,
    ANTIGUEDAD_OBSERVACION,
)

logger = get_logger(__name__)


# ─── Funciones auxiliares ─────────────────────────────────────────────────────

def _calcular_tramo(dias: int) -> str:
    if dias < ANTIGUEDAD_VIGENTE:
        return "Vigente"
    elif dias <= ANTIGUEDAD_OBSERVACION:
        return "En Observación"
    else:
        return "Crítico"


def _calcular_accion(tipo_match: str, flag_iva: str, flag_conciliacion: str, motivo: str) -> str:
    if flag_iva:
        return "Revisar IVA — posible neto vs bruto"
    if flag_conciliacion:
        return "Partida en Conciliación — verificar cierre de mes"
    if tipo_match == CERTEZA_EXACTO:
        return "Aprobado — sin acción requerida"
    if tipo_match == CERTEZA_SUGERIDO:
        return "Revisar y aprobar match manualmente"
    mapa_motivos = {
        "Monto coincide pero fecha fuera de rango": "Revisar fecha — monto OK, desfase > 5 días",
        "Fecha coincide pero monto no encontrado":  "Revisar monto — fecha OK, sin coincidencia",
        "Posible Neto vs Bruto (×1.19)":            "Verificar IVA — posible neto vs bruto",
        "Transacción ausente en libro auxiliar":    "Ausente en libro — verificar omisión",
    }
    return mapa_motivos.get(motivo, "Revisar manualmente") if motivo else "Revisar manualmente"

# ─── Clasificador principal ───────────────────────────────────────────────────

def clasificar(
    cartola:    pd.DataFrame,
    libro:      pd.DataFrame,
    resultados: list[dict],
) -> pd.DataFrame:
    """
    Ensambla el DataFrame final de conciliación v2.

    Args:
        cartola    : DataFrame normalizado de la cartola (columnas v2)
        libro      : DataFrame normalizado del libro (columnas v2)
        resultados : Lista de dicts producida por hacer_matching() v2

    Returns:
        DataFrame con una fila por transacción de la cartola.
    """
    logger.info("Clasificando resultados del matching v2...")

    hoy  = pd.Timestamp.today().normalize()
    filas = []

    for r in resultados:
        idx_c             = r["idx_cartola"]
        idx_l             = r["idx_libro"]
        tipo_match        = r["tipo_match"] if r["tipo_match"] else "sin_match"
        certeza           = r.get("certeza", CERTEZA_MANUAL)
        motivo            = r.get("motivo")
        flag_conciliacion = r.get("flag_conciliacion", "")
        flag_iva          = r.get("flag_iva", "")
        regla_aplicada    = r.get("regla_aplicada", "")
        idx_cercano       = r.get("idx_libro_cercano")

        fila_c = cartola.loc[idx_c]

        # — Antigüedad —
        fecha_op       = pd.Timestamp(fila_c["fecha_operacion"])
        dias_antiguedad = (hoy - fecha_op).days
        tramo           = _calcular_tramo(dias_antiguedad)
        accion          = _calcular_accion(tipo_match, flag_iva, flag_conciliacion, motivo)

        # — Datos lado cartola —
        fila = {
            "fecha_operacion_cartola": fila_c["fecha_operacion"],
            "fecha_valor_cartola":     fila_c["fecha_valor"],
            "glosa_cartola":           fila_c["glosa"],
            "rut_cartola":             fila_c["rut"],
            "monto_cartola":           fila_c["monto"],
            "nro_documento_cartola":   fila_c["nro_documento"],
            "banco_cartola":           fila_c["banco"],
        }

        # — Datos lado libro (si hay match) —
        if idx_l is not None:
            fila_l = libro.loc[idx_l]
            fila.update({
                "fecha_contable_libro":  fila_l["fecha_contable"],
                "glosa_libro":           fila_l["glosa"],
                "rut_libro":             fila_l["rut"],
                "monto_libro":           fila_l["monto"],
                "nro_referencia_libro":  fila_l["nro_referencia"],
                "nro_comprobante_libro": fila_l["nro_comprobante"],
                "codigo_tx_libro":       fila_l["codigo_tx"],
                "idx_libro":             idx_l,        
                "diff_monto":            abs(fila_c["monto"] - fila_l["monto"]),
                "diff_dias":             abs((fila_c["fecha_valor"] - fila_l["fecha_contable"]).days),
                "motivo":                None,
                "fecha_cercana":         None,
                "monto_cercano":         None,
                "glosa_cercana":         None,
                "diff_monto_cercano":    None,
            })
        else:
            fila.update({
                "fecha_contable_libro":  None,
                "glosa_libro":           None,
                "rut_libro":             None,
                "monto_libro":           None,
                "nro_referencia_libro":  None,
                "nro_comprobante_libro": None,
                "codigo_tx_libro":       None,
                "idx_libro":             None, 
                "diff_monto":            None,
                "diff_dias":             None,
                "motivo":                motivo,
            })

            if idx_cercano is not None:
                fila_cercana = libro.loc[idx_cercano]
                fila.update({
                    "fecha_cercana":      fila_cercana["fecha_contable"],
                    "monto_cercano":      fila_cercana["monto"],
                    "glosa_cercana":      fila_cercana["glosa"],
                    "diff_monto_cercano": abs(fila_c["monto"] - fila_cercana["monto"]),
                })
            else:
                fila.update({
                    "fecha_cercana":      None,
                    "monto_cercano":      None,
                    "glosa_cercana":      None,
                    "diff_monto_cercano": None,
                })

        # — Columnas de match y antigüedad —
        fila.update({
            "tipo_match":        tipo_match,
            "certeza":           certeza,
            "regla_aplicada":    regla_aplicada,
            "flag_conciliacion": flag_conciliacion,
            "flag_iva":          flag_iva,
            "dias_antiguedad":   dias_antiguedad,
            "tramo_antiguedad":  tramo,
            "accion_recomendada": accion,
        })

        filas.append(fila)

    df_resultado = pd.DataFrame(filas)

    conteo = df_resultado["tipo_match"].value_counts()
    total  = len(df_resultado)
    logger.info(f"Total transacciones: {total}")
    for tipo, n in conteo.items():
        logger.info(f"  {tipo:<12}: {n:>4} ({n/total*100:.1f}%)")

    return df_resultado


def calcular_diferencia_saldo(
    cartola: pd.DataFrame,
    libro:   pd.DataFrame,
) -> dict:
    """Calcula la diferencia de saldo total entre cartola y libro."""
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
        "cuadra":        abs(diferencia) < 1,
    }


def separar_sin_conciliar(df_resultado: pd.DataFrame) -> pd.DataFrame:
    """Filtra solo las transacciones sin match para el reporte de partidas abiertas."""
    sin_conciliar = df_resultado[df_resultado["tipo_match"] == "Manual"].copy()
    logger.info(f"Partidas sin conciliar: {len(sin_conciliar)}")
    return sin_conciliar.reset_index(drop=True)