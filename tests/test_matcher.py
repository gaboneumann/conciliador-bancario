"""
test_matcher.py — Tests para conciliation/matcher.py
"""
import pytest
import pandas as pd
from conciliation.matcher import (
    hacer_matching,
    _diagnosticar_sin_match,
    MOTIVO_FECHA_FUERA_RANGO,
    MOTIVO_MONTO_NO_ENCONTRADO,
    MOTIVO_AUSENTE_EN_LIBRO,
)


# ─── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def cartola_simple():
    """Cartola con 3 transacciones controladas."""
    return pd.DataFrame({
        "fecha":       pd.to_datetime(["2024-01-15", "2024-02-20", "2024-03-10"]),
        "monto":       [-100_000.0, -50_000.0, 200_000.0],
        "referencia":  ["1234567890", "ABCD567890", "9999999999"],
        "descripcion": ["pago luz enel", "transferencia juan", "sueldo empresa"],
        "banco":       ["Banco de Chile", "BancoEstado", "BCI"],
    })


@pytest.fixture
def libro_match_exacto():
    return pd.DataFrame({
        "fecha":       pd.to_datetime(["2024-01-15", "2024-02-20", "2024-03-10"]),
        "monto":       [-100_000.0, -50_000.0, 200_000.0],
        "referencia":  ["1234567890", "ABCD567890", "9999999999"],
        "descripcion": ["pago luz enel", "transferencia juan", "sueldo empresa"],
        "codigo":      ["SRV001", "TRF002", "ACR003"],
    })


@pytest.fixture
def libro_match_parcial():
    return pd.DataFrame({
        "fecha":       pd.to_datetime(["2024-01-16", "2024-02-21", "2024-03-11"]),
        "monto":       [-101_000.0, -50_200.0, 201_000.0],
        "referencia":  ["XXXX567890", "XXXX567890", "XXXX999999"],
        "descripcion": ["pago luz enel", "transferencia juan", "sueldo empresa"],
        "codigo":      ["SRV001", "TRF002", "ACR003"],
    })


@pytest.fixture
def libro_sin_match():
    return pd.DataFrame({
        "fecha":       pd.to_datetime(["2024-06-01", "2024-07-01", "2024-08-01"]),
        "monto":       [-999_000.0, -888_000.0, 777_000.0],
        "referencia":  ["0000000000", "1111111111", "2222222222"],
        "descripcion": ["otro pago", "otra transferencia", "otro ingreso"],
        "codigo":      ["OTR001", "OTR002", "OTR003"],
    })


# ─── Estructura del resultado ─────────────────────────────────────────────────

class TestEstructuraResultado:

    def test_retorna_lista(self, cartola_simple, libro_match_exacto):
        resultado = hacer_matching(cartola_simple, libro_match_exacto)
        assert isinstance(resultado, list)

    def test_largo_igual_a_cartola(self, cartola_simple, libro_match_exacto):
        resultado = hacer_matching(cartola_simple, libro_match_exacto)
        assert len(resultado) == len(cartola_simple)

    def test_cada_resultado_tiene_claves_correctas(self, cartola_simple, libro_match_exacto):
        resultado = hacer_matching(cartola_simple, libro_match_exacto)
        for r in resultado:
            assert "idx_cartola"       in r
            assert "idx_libro"         in r
            assert "tipo_match"        in r
            assert "motivo"            in r
            assert "idx_libro_cercano" in r


# ─── Match exacto ─────────────────────────────────────────────────────────────

class TestMatchExacto:

    def test_detecta_matches_exactos(self, cartola_simple, libro_match_exacto):
        resultado = hacer_matching(cartola_simple, libro_match_exacto)
        tipos = [r["tipo_match"] for r in resultado]
        assert all(t == "exacto" for t in tipos)

    def test_motivo_es_none_en_match_exacto(self, cartola_simple, libro_match_exacto):
        resultado = hacer_matching(cartola_simple, libro_match_exacto)
        for r in resultado:
            assert r["motivo"] is None

    def test_idx_cercano_es_none_en_match_exacto(self, cartola_simple, libro_match_exacto):
        resultado = hacer_matching(cartola_simple, libro_match_exacto)
        for r in resultado:
            assert r["idx_libro_cercano"] is None


# ─── Match parcial ────────────────────────────────────────────────────────────

class TestMatchParcial:

    def test_detecta_matches_parciales(self, cartola_simple, libro_match_parcial):
        resultado = hacer_matching(cartola_simple, libro_match_parcial)
        tipos = [r["tipo_match"] for r in resultado]
        assert all(t == "parcial" for t in tipos)

    def test_motivo_es_none_en_match_parcial(self, cartola_simple, libro_match_parcial):
        resultado = hacer_matching(cartola_simple, libro_match_parcial)
        for r in resultado:
            assert r["motivo"] is None


# ─── Sin match + diagnóstico ──────────────────────────────────────────────────

class TestSinMatch:

    def test_detecta_sin_match(self, cartola_simple, libro_sin_match):
        resultado = hacer_matching(cartola_simple, libro_sin_match)
        tipos = [r["tipo_match"] for r in resultado]
        assert all(t is None for t in tipos)

    def test_motivo_no_es_none_en_sin_match(self, cartola_simple, libro_sin_match):
        resultado = hacer_matching(cartola_simple, libro_sin_match)
        for r in resultado:
            assert r["motivo"] is not None

    def test_motivo_es_string(self, cartola_simple, libro_sin_match):
        resultado = hacer_matching(cartola_simple, libro_sin_match)
        for r in resultado:
            assert isinstance(r["motivo"], str)


# ─── _diagnosticar_sin_match ──────────────────────────────────────────────────

class TestDiagnosticar:

    @pytest.fixture
    def libro_base(self):
        return pd.DataFrame({
            "fecha": pd.to_datetime(["2024-01-15"]),
            "monto": [-100_000.0],
            "referencia": ["1234567890"],
            "descripcion": ["pago luz"],
            "codigo": ["SRV001"],
        })

    def test_monto_coincide_fecha_no(self, libro_base):
        """Mismo monto pero fecha fuera de rango → MOTIVO_FECHA_FUERA_RANGO."""
        motivo, idx = _diagnosticar_sin_match(
            -100_000.0,
            pd.Timestamp("2024-06-01"),  # muy lejos
            libro_base,
        )
        assert motivo == MOTIVO_FECHA_FUERA_RANGO
        assert idx == 0

    def test_fecha_coincide_monto_no(self, libro_base):
        """Misma fecha pero monto muy distinto → MOTIVO_MONTO_NO_ENCONTRADO."""
        motivo, idx = _diagnosticar_sin_match(
            -999_000.0,                  # monto muy distinto
            pd.Timestamp("2024-01-15"),  # misma fecha
            libro_base,
        )
        assert motivo == MOTIVO_MONTO_NO_ENCONTRADO
        assert idx == 0

    def test_nada_coincide(self):
        """Ni monto ni fecha coinciden → MOTIVO_AUSENTE_EN_LIBRO."""
        libro_vacio = pd.DataFrame({
            "fecha": pd.to_datetime(["2024-06-01"]),
            "monto": [-999_000.0],
            "referencia": ["0000000000"],
            "descripcion": ["otro"],
            "codigo": ["OTR001"],
        })
        motivo, idx = _diagnosticar_sin_match(
            -100_000.0,
            pd.Timestamp("2024-01-15"),
            libro_vacio,
        )
        assert motivo == MOTIVO_AUSENTE_EN_LIBRO
        assert idx is None


# ─── Sin reutilización ────────────────────────────────────────────────────────

class TestSinReutilizacion:

    def test_fila_libro_no_se_reutiliza(self):
        cartola = pd.DataFrame({
            "fecha":       pd.to_datetime(["2024-01-15", "2024-01-15"]),
            "monto":       [-100_000.0, -100_000.0],
            "referencia":  ["1234567890", "1234567890"],
            "descripcion": ["pago luz", "pago luz"],
            "banco":       ["BCI", "BCI"],
        })
        libro = pd.DataFrame({
            "fecha":       pd.to_datetime(["2024-01-15"]),
            "monto":       [-100_000.0],
            "referencia":  ["1234567890"],
            "descripcion": ["pago luz"],
            "codigo":      ["SRV001"],
        })
        resultado = hacer_matching(cartola, libro)
        tipos = [r["tipo_match"] for r in resultado]
        assert tipos.count("exacto") == 1
        assert tipos.count(None)     == 1

    def test_indices_libro_son_unicos(self, cartola_simple, libro_match_exacto):
        resultado = hacer_matching(cartola_simple, libro_match_exacto)
        indices = [r["idx_libro"] for r in resultado if r["idx_libro"] is not None]
        assert len(indices) == len(set(indices))


# ─── Casos mixtos ─────────────────────────────────────────────────────────────

class TestCasosMixtos:

    def test_mix_exacto_parcial_sin_match(self):
        cartola = pd.DataFrame({
            "fecha":       pd.to_datetime(["2024-01-15", "2024-02-20", "2024-03-10"]),
            "monto":       [-100_000.0, -50_000.0, 200_000.0],
            "referencia":  ["1234567890", "ABCD567890", "9999999999"],
            "descripcion": ["pago luz", "transferencia", "sueldo"],
            "banco":       ["BCI", "BCI", "BCI"],
        })
        libro = pd.DataFrame({
            "fecha":       pd.to_datetime(["2024-01-15", "2024-02-20"]),
            "monto":       [-100_000.0, -50_200.0],
            "referencia":  ["1234567890", "XXXX567890"],
            "descripcion": ["pago luz", "transferencia"],
            "codigo":      ["SRV001", "TRF002"],
        })
        resultado = hacer_matching(cartola, libro)

        assert resultado[0]["tipo_match"] == "exacto"
        assert resultado[0]["motivo"]     is None

        assert resultado[1]["tipo_match"] == "parcial"
        assert resultado[1]["motivo"]     is None

        assert resultado[2]["tipo_match"] is None
        assert resultado[2]["motivo"]     is not None