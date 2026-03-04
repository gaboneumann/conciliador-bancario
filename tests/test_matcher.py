"""
test_matcher.py — Tests para conciliation/matcher.py (v2)
"""
import pytest
import pandas as pd
from conciliation.matcher import (
    hacer_matching,
    _diagnosticar_sin_match,
    MOTIVO_FECHA_FUERA_RANGO,
    MOTIVO_MONTO_NO_ENCONTRADO,
    MOTIVO_AUSENTE_EN_LIBRO,
    MOTIVO_POSIBLE_IVA,
)


# ─── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def cartola_simple():
    return pd.DataFrame({
        "fecha_operacion": pd.to_datetime(["2024-01-15", "2024-02-20", "2024-03-10"]),
        "fecha_valor":     pd.to_datetime(["2024-01-16", "2024-02-21", "2024-03-11"]),
        "glosa":           ["pago luz enel", "transferencia juan", "sueldo empresa"],
        "rut":             ["19141427-6", "21493875-8", "203580347-8"],
        "monto":           [-100_000.0, -50_000.0, 200_000.0],
        "nro_documento":   ["1234567890", "ABCD567890", "9999999999"],
        "banco":           ["Banco de Chile", "BancoEstado", "BCI"],
    })


@pytest.fixture
def libro_match_exacto():
    return pd.DataFrame({
        "fecha_contable":  pd.to_datetime(["2024-01-15", "2024-02-20", "2024-03-10"]),
        "glosa":           ["pago luz enel", "transferencia juan", "sueldo empresa"],
        "rut":             ["19141427-6", "21493875-8", "203580347-8"],
        "monto":           [-100_000.0, -50_000.0, 200_000.0],
        "nro_referencia":  ["1234567890", "ABCD567890", "9999999999"],
        "nro_comprobante": ["COMP001", "COMP002", "COMP003"],
        "codigo_tx":       ["SRV001", "TRF002", "ACR003"],
    })


@pytest.fixture
def libro_match_parcial():
    """Mismo RUT y monto, fecha dentro de rango, referencia distinta."""
    return pd.DataFrame({
        "fecha_contable":  pd.to_datetime(["2024-01-16", "2024-02-21", "2024-03-11"]),
        "glosa":           ["pago luz enel", "transferencia juan", "sueldo empresa"],
        "rut":             ["19141427-6", "21493875-8", "203580347-8"],
        "monto":           [-101_000.0, -50_200.0, 201_000.0],
        "nro_referencia":  ["XXXX567890", "XXXX567890", "XXXX999999"],
        "nro_comprobante": ["COMP001", "COMP002", "COMP003"],
        "codigo_tx":       ["SRV001", "TRF002", "ACR003"],
    })


@pytest.fixture
def libro_sin_match():
    return pd.DataFrame({
        "fecha_contable":  pd.to_datetime(["2024-06-01", "2024-07-01", "2024-08-01"]),
        "glosa":           ["otro pago", "otra transferencia", "otro ingreso"],
        "rut":             ["11111111-1", "22222222-2", "33333333-3"],
        "monto":           [-999_000.0, -888_000.0, 777_000.0],
        "nro_referencia":  ["0000000000", "1111111111", "2222222222"],
        "nro_comprobante": ["COMP001", "COMP002", "COMP003"],
        "codigo_tx":       ["OTR001", "OTR002", "OTR003"],
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
        claves_esperadas = {
            "idx_cartola", "idx_libro", "tipo_match", "certeza",
            "motivo", "flag_conciliacion", "flag_iva", "regla_aplicada",
            "idx_libro_cercano",
        }
        for r in resultado:
            assert claves_esperadas.issubset(r.keys())


# ─── Match exacto ─────────────────────────────────────────────────────────────

class TestMatchExacto:

    def test_detecta_matches_exactos(self, cartola_simple, libro_match_exacto):
        resultado = hacer_matching(cartola_simple, libro_match_exacto)
        assert all(r["tipo_match"] == "Exacto" for r in resultado)

    def test_certeza_exacto(self, cartola_simple, libro_match_exacto):
        resultado = hacer_matching(cartola_simple, libro_match_exacto)
        assert all(r["certeza"] == "Exacto" for r in resultado)

    def test_motivo_none_en_match_exacto(self, cartola_simple, libro_match_exacto):
        resultado = hacer_matching(cartola_simple, libro_match_exacto)
        assert all(r["motivo"] is None for r in resultado)

    def test_flag_conciliacion_vacio_en_mismo_mes(self, cartola_simple, libro_match_exacto):
        resultado = hacer_matching(cartola_simple, libro_match_exacto)
        assert all(r["flag_conciliacion"] == "" for r in resultado)


# ─── Match sugerido por RUT sin DV ───────────────────────────────────────────

class TestMatchSugerido:

    def test_rut_sin_dv_baja_certeza_a_sugerido(self, cartola_simple):
        """RUT en cartola sin DV → certeza Sugerido aunque todo coincida."""
        cartola = cartola_simple.copy()
        cartola.loc[0, "rut"] = "19141427"  # sin DV

        libro = pd.DataFrame({
            "fecha_contable":  pd.to_datetime(["2024-01-15"]),
            "glosa":           ["pago luz enel"],
            "rut":             ["19141427-6"],
            "monto":           [-100_000.0],
            "nro_referencia":  ["1234567890"],
            "nro_comprobante": ["COMP001"],
            "codigo_tx":       ["SRV001"],
        })
        resultado = hacer_matching(cartola.iloc[[0]], libro)
        assert resultado[0]["certeza"] == "Sugerido"

    def test_rut_distinto_descarta_candidato(self, cartola_simple):
        """RUT distinto → sin match aunque monto y fecha coincidan."""
        libro = pd.DataFrame({
            "fecha_contable":  pd.to_datetime(["2024-01-15"]),
            "glosa":           ["pago luz enel"],
            "rut":             ["11111111-1"],  # RUT distinto
            "monto":           [-100_000.0],
            "nro_referencia":  ["1234567890"],
            "nro_comprobante": ["COMP001"],
            "codigo_tx":       ["SRV001"],
        })
        resultado = hacer_matching(cartola_simple.iloc[[0]], libro)
        assert resultado[0]["tipo_match"] == "Manual"


# ─── Flag Partida en Conciliación ────────────────────────────────────────────

class TestFlagConciliacion:

    def test_desfase_de_mes_activa_flag(self, cartola_simple):
        """fecha_valor en enero, fecha_contable en febrero → flag activo."""
        libro = pd.DataFrame({
            "fecha_contable":  pd.to_datetime(["2024-02-01"]),  # mes distinto
            "glosa":           ["pago luz enel"],
            "rut":             ["19141427-6"],
            "monto":           [-100_000.0],
            "nro_referencia":  ["1234567890"],
            "nro_comprobante": ["COMP001"],
            "codigo_tx":       ["SRV001"],
        })
        # Ajustar fecha_valor para que esté dentro de ±3 días de feb-01
        cartola = cartola_simple.copy()
        cartola.loc[0, "fecha_valor"] = pd.Timestamp("2024-01-30")

        resultado = hacer_matching(cartola.iloc[[0]], libro)
        assert resultado[0]["flag_conciliacion"] == "Partida en Conciliación"
        assert resultado[0]["certeza"] == "Sugerido"


# ─── Flag IVA ─────────────────────────────────────────────────────────────────

class TestFlagIva:

    def test_diagnostico_iva_en_sin_match(self):
        """Ratio ×1.19 entre montos activa flag_iva en diagnóstico."""
        cartola = pd.DataFrame({
            "fecha_operacion": pd.to_datetime(["2024-01-15"]),
            "fecha_valor":     pd.to_datetime(["2024-01-16"]),
            "glosa":           ["servicio"],
            "rut":             ["19141427-6"],
            "monto":           [-119_000.0],
            "nro_documento":   ["1234567890"],
            "banco":           ["BCI"],
        })
        libro = pd.DataFrame({
            "fecha_contable":  pd.to_datetime(["2024-01-15"]),
            "glosa":           ["servicio"],
            "rut":             ["19141427-6"],
            "monto":           [-100_000.0],  # ratio 1.19
            "nro_referencia":  ["9999999999"],
            "nro_comprobante": ["COMP001"],
            "codigo_tx":       ["SRV001"],
        })
        resultado = hacer_matching(cartola, libro)
        assert resultado[0]["flag_iva"] == "Posible Neto vs Bruto (×1.19)"


# ─── Sin reutilización ────────────────────────────────────────────────────────

class TestSinReutilizacion:

    def test_fila_libro_no_se_reutiliza(self):
        cartola = pd.DataFrame({
            "fecha_operacion": pd.to_datetime(["2024-01-15", "2024-01-15"]),
            "fecha_valor":     pd.to_datetime(["2024-01-15", "2024-01-15"]),
            "glosa":           ["pago luz", "pago luz"],
            "rut":             ["19141427-6", "19141427-6"],
            "monto":           [-100_000.0, -100_000.0],
            "nro_documento":   ["1234567890", "1234567890"],
            "banco":           ["BCI", "BCI"],
        })
        libro = pd.DataFrame({
            "fecha_contable":  pd.to_datetime(["2024-01-15"]),
            "glosa":           ["pago luz"],
            "rut":             ["19141427-6"],
            "monto":           [-100_000.0],
            "nro_referencia":  ["1234567890"],
            "nro_comprobante": ["COMP001"],
            "codigo_tx":       ["SRV001"],
        })
        resultado = hacer_matching(cartola, libro)
        tipos = [r["tipo_match"] for r in resultado]
        assert tipos.count("Exacto") == 1
        assert tipos.count("Manual") == 1

    def test_indices_libro_son_unicos(self, cartola_simple, libro_match_exacto):
        resultado = hacer_matching(cartola_simple, libro_match_exacto)
        indices = [r["idx_libro"] for r in resultado if r["idx_libro"] is not None]
        assert len(indices) == len(set(indices))


# ─── _diagnosticar_sin_match ──────────────────────────────────────────────────

class TestDiagnosticar:

    @pytest.fixture
    def libro_base(self):
        return pd.DataFrame({
            "fecha_contable":  pd.to_datetime(["2024-01-15"]),
            "glosa":           ["pago luz"],
            "rut":             ["19141427-6"],
            "monto":           [-100_000.0],
            "nro_referencia":  ["1234567890"],
            "nro_comprobante": ["COMP001"],
            "codigo_tx":       ["SRV001"],
        })

    def test_monto_coincide_fecha_no(self, libro_base):
        motivo, idx, flag_iva = _diagnosticar_sin_match(
            -100_000.0,
            pd.Timestamp("2024-06-01"),
            "19141427-6",
            libro_base,
        )
        assert motivo == MOTIVO_FECHA_FUERA_RANGO
        assert idx == 0
        assert flag_iva == ""

    def test_fecha_coincide_monto_no(self, libro_base):
        motivo, idx, flag_iva = _diagnosticar_sin_match(
            -999_000.0,
            pd.Timestamp("2024-01-15"),
            "19141427-6",
            libro_base,
        )
        assert motivo == MOTIVO_MONTO_NO_ENCONTRADO
        assert idx == 0

    def test_nada_coincide(self):
        libro = pd.DataFrame({
            "fecha_contable":  pd.to_datetime(["2024-06-01"]),
            "glosa":           ["otro"],
            "rut":             ["11111111-1"],
            "monto":           [-999_000.0],
            "nro_referencia":  ["0000000000"],
            "nro_comprobante": ["COMP001"],
            "codigo_tx":       ["OTR001"],
        })
        motivo, idx, flag_iva = _diagnosticar_sin_match(
            -100_000.0,
            pd.Timestamp("2024-01-15"),
            "19141427-6",
            libro,
        )
        assert motivo == MOTIVO_AUSENTE_EN_LIBRO
        assert idx is None

    def test_detecta_posible_iva(self, libro_base):
        """Ratio ×1.19 entre montos → MOTIVO_POSIBLE_IVA y flag activo."""
        motivo, idx, flag_iva = _diagnosticar_sin_match(
            -119_000.0,
            pd.Timestamp("2024-06-01"),
            "19141427-6",
            libro_base,
        )
        assert motivo == MOTIVO_POSIBLE_IVA
        assert flag_iva == "Posible Neto vs Bruto (×1.19)"