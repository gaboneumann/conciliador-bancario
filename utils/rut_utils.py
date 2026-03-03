"""
rut_utils.py — Normalización y validación de RUT chileno.

Maneja 3 formatos de entrada:
    "19.141.427-6"  → con puntos y DV        (tiene_dv=True)
    "21493875-8"    → sin puntos, con DV      (tiene_dv=True)
    "203580347"     → solo cuerpo, sin DV     (tiene_dv=False)

Regla de negocio:
    Un RUT sin DV original nunca produce certeza Exacto,
    aunque el DV calculado coincida.
"""

import re


# ─── Función interna ──────────────────────────────────────────────────────────

def _calcular_dv(cuerpo: str) -> str:
    """
    Calcula el dígito verificador de un RUT chileno usando módulo 11 (algoritmo SII).

    Args:
        cuerpo: string numérico sin puntos ni DV. Ej: "19141427"

    Returns:
        DV como string: "0"–"9" o "K"
    """
    suma = 0
    multiplicador = 2

    for digito in reversed(cuerpo):
        suma += int(digito) * multiplicador
        multiplicador = multiplicador + 1 if multiplicador < 7 else 2

    resto = 11 - (suma % 11)

    if resto == 11:
        return "0"
    if resto == 10:
        return "K"
    return str(resto)


# ─── Función principal ────────────────────────────────────────────────────────

def normalizar_rut(rut_raw) -> dict:
    """
    Normaliza un RUT crudo proveniente del Excel.

    Args:
        rut_raw: valor crudo — puede ser str, int, float o None.

    Returns:
        dict con:
            canonical (str|None): "cuerpo-DV" sin puntos. None si inválido.
            tiene_dv  (bool):     True si el dato original incluía DV.
            dv_valido (bool):     True si el DV informado coincide con el calculado.
                                  Siempre False si tiene_dv=False.
            es_valido (bool):     True si el cuerpo es numérico y tiene 6–9 dígitos.
    """
    resultado = {
        "canonical": None,
        "tiene_dv":  False,
        "dv_valido": False,
        "es_valido": False,
    }

    # Convertir a string y limpiar
    if rut_raw is None:
        return resultado

    rut_str = str(rut_raw).strip().upper()

    if not rut_str:
        return resultado

    # Eliminar puntos de formato
    rut_str = rut_str.replace(".", "")

    # Detectar si tiene DV (formato "cuerpo-DV")
    if "-" in rut_str:
        partes = rut_str.split("-")
        if len(partes) != 2:
            return resultado

        cuerpo, dv_informado = partes[0], partes[1]
        tiene_dv = True
    else:
        cuerpo = rut_str
        dv_informado = None
        tiene_dv = False

    # Validar que el cuerpo sea numérico
    if not cuerpo.isdigit():
        return resultado

    # Validar longitud del cuerpo (6–9 dígitos)
    if not (6 <= len(cuerpo) <= 9):
        return resultado

    # Cuerpo válido
    resultado["es_valido"] = True
    resultado["tiene_dv"]  = tiene_dv

    # Calcular DV
    dv_calculado = _calcular_dv(cuerpo)

    if tiene_dv:
        # Validar DV informado contra calculado
        resultado["dv_valido"] = (dv_informado == dv_calculado)
        dv_final = dv_informado  # usamos el informado para el canonical
    else:
        # Sin DV: calculamos para normalizar, pero dv_valido queda False
        resultado["dv_valido"] = False
        dv_final = dv_calculado

    resultado["canonical"] = f"{cuerpo}-{dv_final}"

    return resultado


# ─── Comparación de RUTs ──────────────────────────────────────────────────────

def ruts_coinciden(rut_a, rut_b) -> dict:
    """
    Compara dos RUT normalizados y determina si coinciden y con qué certeza.

    Args:
        rut_a: RUT crudo del lado cartola.
        rut_b: RUT crudo del lado libro.

    Returns:
        dict con:
            coincide (bool):  True si los cuerpos coinciden.
            certeza  (str):   "exacto" | "sugerido" | "manual"
            detalle  (str):   explicación para trazabilidad.
    """
    norm_a = normalizar_rut(rut_a)
    norm_b = normalizar_rut(rut_b)

    # Alguno inválido → no coincide
    if not norm_a["es_valido"] or not norm_b["es_valido"]:
        return {
            "coincide": False,
            "certeza":  "manual",
            "detalle":  f"RUT inválido — a='{rut_a}' b='{rut_b}'",
        }

    # Extraer cuerpos para comparar (ignorar DV en la comparación)
    cuerpo_a = norm_a["canonical"].split("-")[0]
    cuerpo_b = norm_b["canonical"].split("-")[0]

    if cuerpo_a != cuerpo_b:
        return {
            "coincide": False,
            "certeza":  "manual",
            "detalle":  f"Cuerpos distintos — {norm_a['canonical']} vs {norm_b['canonical']}",
        }

    # Cuerpos coinciden — determinar certeza
    ambos_con_dv = norm_a["tiene_dv"] and norm_b["tiene_dv"]

    if ambos_con_dv:
        certeza = "exacto"
        detalle = f"RUT coincide con DV verificado — {norm_a['canonical']}"
    else:
        certeza = "sugerido"
        faltante = "cartola" if not norm_a["tiene_dv"] else "libro"
        detalle = f"RUT coincide pero falta DV en {faltante} — {norm_a['canonical']}"

    return {
        "coincide": True,
        "certeza":  certeza,
        "detalle":  detalle,
    }