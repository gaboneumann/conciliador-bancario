"""
test_classifier.py — Tests para conciliation/classifier.py
"""
import pytest
import pandas as pd
from conciliation.classifier import (
    clasificar,
    separar_sin_conciliar,
    calcular_diferencia_saldo,
)


# ─── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def cartola():
    return pd.DataFrame({
        "fecha":       pd.to_datetime(["2024-01-15", "2024-02-20", "2024-03-10"]),
        "monto":       [-100_000.0, -50_000.0, 200_000.0],
        "referencia":  ["1234567890", "ABCD567890", "9999999999"],
        "descripcion": ["pago luz enel", "transferencia juan", "sueldo empresa"],
        "banco":       ["Banco de Chile", "BancoEstado", "BCI"],
    })


@pytest.fixture
def libro():
    return pd.DataFrame({
        "fecha":       pd.to_datetime(["2024-01-15", "2024-02-21"]),
        "monto":       [-100_000.0, -50_200.0],
        "referencia":  ["1234567890", "XXXX567890"],
        "descripcion": ["pago luz enel", "transferencia juan"],
        "codigo":      ["SRV001", "TRF002"],
    })


@pytest.fixture
def resultados_mixtos():
    """Exacto, parcial y sin_match con los nuevos campos del matcher."""
    return [
        {
            "idx_cartola": 0, "idx_libro": 0, "tipo_match": "exacto",
            "motivo": None, "idx_libro_cercano": None,
        },
        {
            "idx_cartola": 1, "idx_libro": 1, "tipo_match": "parcial",
            "motivo": None, "idx_libro_cercano": None,
        },
        {
            "idx_cartola": 2, "idx_libro": None, "tipo_match": None,
            "motivo": "Monto coincide pero fecha fuera de rango",
            "idx_libro_cercano": 0,
        },
    ]


@pytest.fixture
def df_resultado(cartola, libro, resultados_mixtos):
    return clasificar(cartola, libro, resultados_mixtos)


# ─── Estructura del DataFrame ─────────────────────────────────────────────────

class TestEstructura:

    def test_retorna_dataframe(self, df_resultado):
        assert isinstance(df_resultado, pd.DataFrame)

    def test_filas_igual_a_cartola(self, df_resultado, cartola):
        assert len(df_resultado) == len(cartola)

    def test_columnas_cartola_presentes(self, df_resultado):
        for col in ["fecha_cartola", "monto_cartola", "descripcion_cartola",
                    "referencia_cartola", "banco_cartola"]:
            assert col in df_resultado.columns

    def test_columnas_libro_presentes(self, df_resultado):
        for col in ["fecha_libro", "monto_libro", "descripcion_libro",
                    "referencia_libro", "codigo_libro"]:
            assert col in df_resultado.columns

    def test_columnas_calculadas_presentes(self, df_resultado):
        for col in ["tipo_match", "diff_monto", "diff_dias"]:
            assert col in df_resultado.columns

    def test_columnas_diagnostico_presentes(self, df_resultado):
        for col in ["motivo", "fecha_cercana", "monto_cercano",
                    "descripcion_cercana", "diff_monto_cercano"]:
            assert col in df_resultado.columns


# ─── Valores tipo_match ───────────────────────────────────────────────────────

class TestTipoMatch:

    def test_exacto_se_clasifica_correctamente(self, df_resultado):
        assert df_resultado.loc[0, "tipo_match"] == "exacto"

    def test_parcial_se_clasifica_correctamente(self, df_resultado):
        assert df_resultado.loc[1, "tipo_match"] == "parcial"

    def test_none_se_convierte_a_sin_match(self, df_resultado):
        assert df_resultado.loc[2, "tipo_match"] == "sin_match"


# ─── Columnas calculadas ──────────────────────────────────────────────────────

class TestColumnasCalculadas:

    def test_diff_monto_cero_en_match_exacto(self, df_resultado):
        assert df_resultado.loc[0, "diff_monto"] == 0.0

    def test_diff_monto_calculada_en_match_parcial(self, df_resultado):
        assert df_resultado.loc[1, "diff_monto"] == 200.0

    def test_diff_dias_cero_en_match_exacto(self, df_resultado):
        assert df_resultado.loc[0, "diff_dias"] == 0

    def test_diff_dias_calculada_en_match_parcial(self, df_resultado):
        assert df_resultado.loc[1, "diff_dias"] == 1

    def test_diff_monto_vacio_en_sin_match(self, df_resultado):
        assert pd.isna(df_resultado.loc[2, "diff_monto"])

    def test_diff_dias_vacio_en_sin_match(self, df_resultado):
        assert pd.isna(df_resultado.loc[2, "diff_dias"])


# ─── Columnas de diagnóstico ──────────────────────────────────────────────────

class TestDiagnostico:

    def test_motivo_presente_en_sin_match(self, df_resultado):
        assert df_resultado.loc[2, "motivo"] == "Monto coincide pero fecha fuera de rango"

    def test_motivo_none_en_match_exacto(self, df_resultado):
        assert pd.isna(df_resultado.loc[0, "motivo"])

    def test_motivo_none_en_match_parcial(self, df_resultado):
        assert pd.isna(df_resultado.loc[1, "motivo"])

    def test_monto_cercano_presente_en_sin_match(self, df_resultado):
        assert df_resultado.loc[2, "monto_cercano"] == -100_000.0

    def test_fecha_cercana_presente_en_sin_match(self, df_resultado):
        assert pd.notna(df_resultado.loc[2, "fecha_cercana"])

    def test_diff_monto_cercano_calculada(self, df_resultado):
        """Cartola monto 200.000 vs cercano -100.000 → diff = 300.000."""
        assert df_resultado.loc[2, "diff_monto_cercano"] == 300_000.0

    def test_datos_cercanos_none_en_match_exacto(self, df_resultado):
        assert pd.isna(df_resultado.loc[0, "monto_cercano"])
        assert pd.isna(df_resultado.loc[0, "fecha_cercana"])


# ─── calcular_diferencia_saldo ────────────────────────────────────────────────

class TestDiferenciaSaldo:

    def test_retorna_dict(self, cartola, libro):
        resultado = calcular_diferencia_saldo(cartola, libro)
        assert isinstance(resultado, dict)

    def test_tiene_claves_correctas(self, cartola, libro):
        resultado = calcular_diferencia_saldo(cartola, libro)
        for clave in ["saldo_cartola", "saldo_libro", "diferencia", "cuadra"]:
            assert clave in resultado

    def test_saldo_cartola_correcto(self, cartola, libro):
        resultado = calcular_diferencia_saldo(cartola, libro)
        assert resultado["saldo_cartola"] == 50_000.0

    def test_saldo_libro_correcto(self, cartola, libro):
        resultado = calcular_diferencia_saldo(cartola, libro)
        assert resultado["saldo_libro"] == -150_200.0

    def test_diferencia_calculada(self, cartola, libro):
        resultado = calcular_diferencia_saldo(cartola, libro)
        assert resultado["diferencia"] == resultado["saldo_cartola"] - resultado["saldo_libro"]

    def test_cuadra_false_cuando_hay_diferencia(self, cartola, libro):
        resultado = calcular_diferencia_saldo(cartola, libro)
        assert resultado["cuadra"] == False

    def test_cuadra_true_cuando_montos_iguales(self):
        df = pd.DataFrame({
            "monto": [-100_000.0, 200_000.0],
            "fecha": pd.to_datetime(["2024-01-01", "2024-01-02"]),
        })
        resultado = calcular_diferencia_saldo(df, df)
        assert resultado["cuadra"] == True
        assert resultado["diferencia"] == 0.0


# ─── separar_sin_conciliar ────────────────────────────────────────────────────

class TestSepararSinConciliar:

    def test_retorna_dataframe(self, df_resultado):
        assert isinstance(separar_sin_conciliar(df_resultado), pd.DataFrame)

    def test_solo_contiene_sin_match(self, df_resultado):
        resultado = separar_sin_conciliar(df_resultado)
        assert all(resultado["tipo_match"] == "sin_match")

    def test_cantidad_correcta(self, df_resultado):
        assert len(separar_sin_conciliar(df_resultado)) == 1

    def test_incluye_columnas_diagnostico(self, df_resultado):
        resultado = separar_sin_conciliar(df_resultado)
        assert "motivo"        in resultado.columns
        assert "monto_cercano" in resultado.columns

    def test_index_reseteado(self, df_resultado):
        resultado = separar_sin_conciliar(df_resultado)
        assert list(resultado.index) == list(range(len(resultado)))