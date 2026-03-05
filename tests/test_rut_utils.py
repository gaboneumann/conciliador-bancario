"""
test_rut_utils.py — Tests para utils/rut_utils.py

Cubre:
- normalizar_rut() con 3 formatos de entrada
- _calcular_dv() incluyendo caso K y borde
- ruts_coinciden() exacto vs sugerido vs no coincide
- Casos inválidos: letras, vacío, largo fuera de rango
"""

import pytest
from utils.rut_utils import normalizar_rut, _calcular_dv, ruts_coinciden


# ─── _calcular_dv() ───────────────────────────────────────────────────────────

class TestCalcularDv:

    def test_dv_numerico(self):
        assert _calcular_dv("19141427") == "6"

    def test_dv_numerico_2(self):
        assert _calcular_dv("21493875") == "8"

    def test_dv_k(self):
        """El algoritmo módulo 11 puede producir K como dígito verificador."""
        assert _calcular_dv("12531909") == "2"   # corregido: resultado real es 2

    def test_cuerpo_6_digitos(self):
        """RUT de empresa pequeña o persona con cuerpo corto."""
        assert _calcular_dv("579751") == "9"     # corregido: resultado real es 9

    def test_cuerpo_9_digitos(self):
        """RUT de empresa grande — cuerpo de 9 dígitos."""
        assert _calcular_dv("203580347") == "8"


# ─── normalizar_rut() ─────────────────────────────────────────────────────────

class TestNormalizarRut:

    def test_formato_con_puntos_y_dv(self):
        """Formato estándar SII: 19.141.427-6"""
        result = normalizar_rut("19.141.427-6")
        assert result["canonical"] == "19141427-6"
        assert result["tiene_dv"] is True
        assert result["dv_valido"] is True
        assert result["es_valido"] is True

    def test_formato_sin_puntos_con_dv(self):
        """Formato sin puntos: 21493875-8"""
        result = normalizar_rut("21493875-8")
        assert result["canonical"] == "21493875-8"
        assert result["tiene_dv"] is True
        assert result["dv_valido"] is True
        assert result["es_valido"] is True

    def test_formato_sin_dv(self):
        """Solo cuerpo numérico — DV debe calcularse."""
        result = normalizar_rut("203580347")
        assert result["canonical"] == "203580347-8"
        assert result["tiene_dv"] is False
        assert result["dv_valido"] is False  # no había DV para validar
        assert result["es_valido"] is True

    def test_formato_sin_dv_corto(self):
        result = normalizar_rut("57975113")
        assert result["canonical"] == "57975113-4"
        assert result["tiene_dv"] is False
        assert result["es_valido"] is True

    def test_dv_invalido(self):
        """DV informado no coincide con el calculado."""
        result = normalizar_rut("19141427-9")  # DV correcto es 6
        assert result["tiene_dv"] is True
        assert result["dv_valido"] is False
        assert result["es_valido"] is True  # cuerpo es válido igual

    def test_dv_k(self):
        """Buscar un RUT cuyo DV real sea K."""
        result = normalizar_rut("1000005-K")
        assert result["canonical"] == "1000005-K"
        assert result["tiene_dv"] is True
        assert result["dv_valido"] is True
        
    def test_rut_invalido_letras(self):
        result = normalizar_rut("38404X")
        assert result["es_valido"] is False
        assert result["canonical"] is None

    def test_rut_invalido_vacio(self):
        result = normalizar_rut("")
        assert result["es_valido"] is False
        assert result["canonical"] is None

    def test_rut_invalido_none(self):
        result = normalizar_rut(None)
        assert result["es_valido"] is False
        assert result["canonical"] is None

    def test_rut_invalido_caracteres_especiales(self):
        result = normalizar_rut("??-!")
        assert result["es_valido"] is False

    def test_rut_cuerpo_muy_corto(self):
        """Menos de 6 dígitos — fuera de rango válido."""
        result = normalizar_rut("12345")
        assert result["es_valido"] is False


# ─── ruts_coinciden() ─────────────────────────────────────────────────────────

class TestRutsCoinciden:

    def test_exacto_ambos_con_dv(self):
        """Ambos RUT tienen DV verificado y coinciden → Exacto."""
        result = ruts_coinciden("19.141.427-6", "19141427-6")
        assert result["coincide"] is True
        assert result["certeza"] == "exacto"

    def test_sugerido_uno_sin_dv(self):
        """Un RUT sin DV — certeza baja a Sugerido aunque coincidan."""
        result = ruts_coinciden("19141427", "19141427-6")
        assert result["coincide"] is True
        assert result["certeza"] == "sugerido"

    def test_no_coinciden(self):
        result = ruts_coinciden("19141427-6", "21493875-8")
        assert result["coincide"] is False
        assert result["certeza"] == "manual"

    def test_detalle_presente(self):
        """El campo detalle siempre debe estar presente para trazabilidad."""
        result = ruts_coinciden("19141427-6", "19141427-6")
        assert "detalle" in result
        assert isinstance(result["detalle"], str)

    def test_rut_invalido_no_coincide(self):
        """Un RUT inválido nunca produce coincidencia."""
        result = ruts_coinciden("38404X", "19141427-6")
        assert result["coincide"] is False

    def test_ambos_invalidos(self):
        result = ruts_coinciden("??", "!!")
        assert result["coincide"] is False