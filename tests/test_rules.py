"""
test_rules.py — Tests para conciliation/rules.py (v2)
"""
import pytest
import pandas as pd
import numpy as np
from conciliation.rules import (
    montos_coinciden,
    fechas_coinciden,
    referencias_coinciden,
    es_match_exacto,
    es_match_parcial,
    mismo_mes,
    detectar_iva,
)


# ─── montos_coinciden ─────────────────────────────────────────────────────────

class TestMontosCoinciden:

    def test_montos_identicos(self):
        assert montos_coinciden(100_000, 100_000) is True

    def test_diferencia_dentro_tolerancia(self):
        assert montos_coinciden(100_000, 101_500) is True

    def test_diferencia_exactamente_en_limite(self):
        assert montos_coinciden(100_000, 102_000) is True

    def test_diferencia_fuera_de_tolerancia(self):
        assert montos_coinciden(100_000, 103_000) is False

    def test_ambos_cero(self):
        assert montos_coinciden(0, 0) is True

    def test_uno_cero_otro_no(self):
        assert montos_coinciden(0, 100_000) is False

    def test_montos_negativos_dentro_tolerancia(self):
        assert montos_coinciden(-100_000, -101_500) is True

    def test_montos_negativos_fuera_tolerancia(self):
        assert montos_coinciden(-100_000, -103_000) is False

    def test_nan_retorna_false(self):
        assert montos_coinciden(np.nan, 100_000) is False
        assert montos_coinciden(100_000, np.nan) is False
        assert montos_coinciden(np.nan, np.nan)  is False

    # ── Cap de materialidad $5.000 CLP (v2) ──────────────────────────────────

    def test_diferencia_bajo_cap_pasa(self):
        """$4.999 de diferencia con monto grande debe pasar."""
        assert montos_coinciden(1_000_000, 1_004_999) is True

    def test_diferencia_exactamente_cap_pasa(self):
        """$5.000 exactos en el límite con monto grande debe pasar."""
        assert montos_coinciden(1_000_000, 1_005_000) is True

    def test_diferencia_sobre_cap_falla(self):
        """$5.001 de diferencia debe fallar aunque esté bajo el 2% relativo."""
        assert montos_coinciden(500_000, 505_001) is False

    def test_cap_aplica_en_montos_grandes(self):
        """En montos grandes el cap de $5.000 es más restrictivo que el 2%."""
        # 2% de 1.000.000 = 20.000 — pero el cap es 5.000
        assert montos_coinciden(1_000_000, 1_005_001) is False
        assert montos_coinciden(1_000_000, 1_004_999) is True


# ─── fechas_coinciden ─────────────────────────────────────────────────────────

class TestFechasCoinciden:

    def test_fechas_identicas(self):
        fecha = pd.Timestamp("2024-01-15")
        assert fechas_coinciden(fecha, fecha) is True

    def test_diferencia_dentro_tolerancia(self):
        a = pd.Timestamp("2024-01-15")
        b = pd.Timestamp("2024-01-17")
        assert fechas_coinciden(a, b) is True

    def test_diferencia_exactamente_en_limite(self):
        a = pd.Timestamp("2024-01-15")
        b = pd.Timestamp("2024-01-18")
        assert fechas_coinciden(a, b) is True

    def test_diferencia_fuera_de_tolerancia(self):
        a = pd.Timestamp("2024-01-15")
        b = pd.Timestamp("2024-01-21")  # 6 días → fuera de rango
        assert fechas_coinciden(a, b) is False

    def test_fecha_anterior_y_posterior(self):
        a = pd.Timestamp("2024-01-15")
        b = pd.Timestamp("2024-01-12")
        assert fechas_coinciden(a, b) is True

    def test_nan_retorna_false(self):
        fecha = pd.Timestamp("2024-01-15")
        assert fechas_coinciden(pd.NaT, fecha) is False
        assert fechas_coinciden(fecha, pd.NaT) is False


# ─── referencias_coinciden ────────────────────────────────────────────────────

class TestReferenciasCoinciden:

    def test_referencias_identicas(self):
        assert referencias_coinciden("1234567890", "1234567890") is True

    def test_primeros_caracteres_iguales(self):
        """Con tolerancia de 6, los primeros 6 iguales deben pasar."""
        assert referencias_coinciden("1234567890", "123456XXXX") is True

    def test_primeros_caracteres_distintos(self):
        assert referencias_coinciden("1234567890", "9999567890") is False

    def test_referencia_vacia_retorna_false(self):
        assert referencias_coinciden("", "1234567890") is False
        assert referencias_coinciden("1234567890", "") is False
        assert referencias_coinciden("", "") is False

    def test_referencia_mas_corta_que_tolerancia(self):
        assert referencias_coinciden("12", "12") is True
        assert referencias_coinciden("12", "99") is False


# ─── es_match_exacto ──────────────────────────────────────────────────────────

class TestMatchExacto:

    def test_los_tres_criterios_cumplen(self):
        assert es_match_exacto(
            100_000, pd.Timestamp("2024-01-15"), "1234567890",
            101_500, pd.Timestamp("2024-01-16"), "123456XXXX",
        ) is True

    def test_falla_si_monto_no_coincide(self):
        assert es_match_exacto(
            100_000, pd.Timestamp("2024-01-15"), "1234567890",
            110_000, pd.Timestamp("2024-01-15"), "1234567890",
        ) is False

    def test_falla_si_fecha_no_coincide(self):
        assert es_match_exacto(
            100_000, pd.Timestamp("2024-01-15"), "1234567890",
            100_000, pd.Timestamp("2024-01-25"), "1234567890",
        ) is False

    def test_falla_si_referencia_no_coincide(self):
        assert es_match_exacto(
            100_000, pd.Timestamp("2024-01-15"), "1234567890",
            100_000, pd.Timestamp("2024-01-15"), "9999567890",
        ) is False


# ─── es_match_parcial ─────────────────────────────────────────────────────────

class TestMatchParcial:

    def test_monto_y_fecha_coinciden_referencia_no(self):
        assert es_match_parcial(
            100_000, pd.Timestamp("2024-01-15"), "1234567890",
            100_000, pd.Timestamp("2024-01-15"), "9999567890",
        ) is True

    def test_no_es_parcial_si_los_tres_coinciden(self):
        assert es_match_parcial(
            100_000, pd.Timestamp("2024-01-15"), "1234567890",
            100_000, pd.Timestamp("2024-01-15"), "1234567890",
        ) is False

    def test_no_es_parcial_si_monto_no_coincide(self):
        assert es_match_parcial(
            100_000, pd.Timestamp("2024-01-15"), "1234567890",
            110_000, pd.Timestamp("2024-01-15"), "9999567890",
        ) is False


# ─── mismo_mes (v2) ───────────────────────────────────────────────────────────

class TestMismoMes:

    def test_mismo_mes_mismo_anio(self):
        a = pd.Timestamp("2024-01-15")
        b = pd.Timestamp("2024-01-28")
        assert mismo_mes(a, b) is True

    def test_meses_distintos_mismo_anio(self):
        a = pd.Timestamp("2024-01-31")
        b = pd.Timestamp("2024-02-01")
        assert mismo_mes(a, b) is False

    def test_mismo_mes_anio_distinto(self):
        a = pd.Timestamp("2024-01-15")
        b = pd.Timestamp("2025-01-15")
        assert mismo_mes(a, b) is False

    def test_fechas_identicas(self):
        a = pd.Timestamp("2024-06-15")
        assert mismo_mes(a, a) is True


# ─── detectar_iva (v2) ────────────────────────────────────────────────────────

class TestDetectarIva:

    def test_ratio_exacto_1_19(self):
        """119.000 / 100.000 = 1.19 exacto."""
        assert detectar_iva(119_000, 100_000) is True

    def test_ratio_inverso(self):
        """100.000 / 119.000 ≈ 0.840 → inverso es 1.19."""
        assert detectar_iva(100_000, 119_000) is True

    def test_ratio_dentro_tolerancia(self):
        """1.195 está dentro del ±1% sobre 1.19."""
        assert detectar_iva(119_500, 100_000) is True

    def test_ratio_fuera_de_tolerancia(self):
        """1.25 está fuera del ±1% sobre 1.19."""
        assert detectar_iva(125_000, 100_000) is False

    def test_montos_iguales_no_es_iva(self):
        assert detectar_iva(100_000, 100_000) is False

    def test_cero_retorna_false(self):
        assert detectar_iva(0, 100_000) is False
        assert detectar_iva(100_000, 0) is False