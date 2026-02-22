"""
test_rules.py — Tests para conciliation/rules.py
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
)


# ─── montos_coinciden ─────────────────────────────────────────────────────────

class TestMontosCoinciden:

    def test_montos_identicos(self):
        assert montos_coinciden(100_000, 100_000) is True

    def test_diferencia_dentro_tolerancia(self):
        """1.5% de diferencia debe pasar con tolerancia de 2%."""
        assert montos_coinciden(100_000, 101_500) is True

    def test_diferencia_exactamente_en_limite(self):
        """2.0% exacto debe pasar (límite incluido)."""
        assert montos_coinciden(100_000, 102_000) is True

    def test_diferencia_fuera_de_tolerancia(self):
        """3% de diferencia debe fallar."""
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


# ─── fechas_coinciden ─────────────────────────────────────────────────────────

class TestFechasCoinciden:

    def test_fechas_identicas(self):
        fecha = pd.Timestamp("2024-01-15")
        assert fechas_coinciden(fecha, fecha) is True

    def test_diferencia_dentro_tolerancia(self):
        """2 días de diferencia debe pasar con tolerancia de 3."""
        a = pd.Timestamp("2024-01-15")
        b = pd.Timestamp("2024-01-17")
        assert fechas_coinciden(a, b) is True

    def test_diferencia_exactamente_en_limite(self):
        """3 días exactos debe pasar (límite incluido)."""
        a = pd.Timestamp("2024-01-15")
        b = pd.Timestamp("2024-01-18")
        assert fechas_coinciden(a, b) is True

    def test_diferencia_fuera_de_tolerancia(self):
        """4 días de diferencia debe fallar."""
        a = pd.Timestamp("2024-01-15")
        b = pd.Timestamp("2024-01-19")
        assert fechas_coinciden(a, b) is False

    def test_fecha_anterior_y_posterior(self):
        """La tolerancia aplica en ambas direcciones."""
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
        """Con tolerancia de 4, los primeros 4 iguales deben pasar."""
        assert referencias_coinciden("1234567890", "1234XXXXX") is True

    def test_primeros_caracteres_distintos(self):
        assert referencias_coinciden("1234567890", "9999567890") is False

    def test_referencia_vacia_retorna_false(self):
        assert referencias_coinciden("", "1234567890") is False
        assert referencias_coinciden("1234567890", "") is False
        assert referencias_coinciden("", "") is False

    def test_referencia_mas_corta_que_tolerancia(self):
        """Si la referencia tiene menos de 4 caracteres, compara lo que hay."""
        assert referencias_coinciden("12", "12") is True
        assert referencias_coinciden("12", "99") is False


# ─── es_match_exacto ──────────────────────────────────────────────────────────

class TestMatchExacto:

    def test_los_tres_criterios_cumplen(self):
        assert es_match_exacto(
            100_000, pd.Timestamp("2024-01-15"), "1234567890",
            101_500, pd.Timestamp("2024-01-16"), "1234XXXXXX",
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
        """Si los tres coinciden es match exacto, no parcial."""
        assert es_match_parcial(
            100_000, pd.Timestamp("2024-01-15"), "1234567890",
            100_000, pd.Timestamp("2024-01-15"), "1234567890",
        ) is False

    def test_no_es_parcial_si_monto_no_coincide(self):
        assert es_match_parcial(
            100_000, pd.Timestamp("2024-01-15"), "1234567890",
            110_000, pd.Timestamp("2024-01-15"), "9999567890",
        ) is False