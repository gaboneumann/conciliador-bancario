"""
test_classifier.py — Tests para conciliation/classifier.py (v2)
"""
import pytest
import pandas as pd
from conciliation.classifier import (
    clasificar,
    separar_sin_conciliar,
    calcular_diferencia_saldo,
)


# ─── Fixtures base ────────────────────────────────────────────────────────────

@pytest.fixture
def cartola():
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
def libro():
    return pd.DataFrame({
        "fecha_contable":  pd.to_datetime(["2024-01-15", "2024-02-21"]),
        "glosa":           ["pago luz enel", "transferencia juan"],
        "rut":             ["19141427-6", "21493875-8"],
        "monto":           [-100_000.0, -50_200.0],
        "nro_referencia":  ["1234567890", "XXXX567890"],
        "nro_comprobante": ["COMP001", "COMP002"],
        "codigo_tx":       ["SRV001", "TRF002"],
    })


@pytest.fixture
def resultados_mixtos():
    return [
        {
            "idx_cartola": 0, "idx_libro": 0,
            "tipo_match": "Exacto", "certeza": "Exacto",
            "motivo": None, "flag_conciliacion": "", "flag_iva": "",
            "regla_aplicada": "RUT + Monto + Fecha + Referencia",
            "idx_libro_cercano": None,
        },
        {
            "idx_cartola": 1, "idx_libro": 1,
            "tipo_match": "Sugerido", "certeza": "Sugerido",
            "motivo": None, "flag_conciliacion": "", "flag_iva": "",
            "regla_aplicada": "RUT + Monto + Fecha",
            "idx_libro_cercano": None,
        },
        {
            "idx_cartola": 2, "idx_libro": None,
            "tipo_match": "Manual", "certeza": "Manual",
            "motivo": "Monto coincide pero fecha fuera de rango",
            "flag_conciliacion": "", "flag_iva": "",
            "regla_aplicada": "",
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
        for col in ["fecha_operacion_cartola", "monto_cartola", "glosa_cartola",
                    "rut_cartola", "nro_documento_cartola", "banco_cartola"]:
            assert col in df_resultado.columns

    def test_columnas_libro_presentes(self, df_resultado):
        for col in ["fecha_contable_libro", "monto_libro", "glosa_libro",
                    "rut_libro", "nro_referencia_libro", "codigo_tx_libro"]:
            assert col in df_resultado.columns

    def test_columnas_calculadas_presentes(self, df_resultado):
        for col in ["tipo_match", "certeza", "diff_monto", "diff_dias",
                    "flag_conciliacion", "flag_iva", "regla_aplicada"]:
            assert col in df_resultado.columns

    def test_columnas_antiguedad_presentes(self, df_resultado):
        for col in ["dias_antiguedad", "tramo_antiguedad", "accion_recomendada"]:
            assert col in df_resultado.columns

    def test_columnas_diagnostico_presentes(self, df_resultado):
        for col in ["motivo", "fecha_cercana", "monto_cercano",
                    "glosa_cercana", "diff_monto_cercano"]:
            assert col in df_resultado.columns


# ─── Valores tipo_match ───────────────────────────────────────────────────────

class TestTipoMatch:

    def test_exacto_se_clasifica_correctamente(self, df_resultado):
        assert df_resultado.loc[0, "tipo_match"] == "Exacto"

    def test_sugerido_se_clasifica_correctamente(self, df_resultado):
        assert df_resultado.loc[1, "tipo_match"] == "Sugerido"

    def test_manual_se_clasifica_correctamente(self, df_resultado):
        assert df_resultado.loc[2, "tipo_match"] == "Manual"


# ─── Columnas calculadas ──────────────────────────────────────────────────────

class TestColumnasCalculadas:

    def test_diff_monto_cero_en_match_exacto(self, df_resultado):
        assert df_resultado.loc[0, "diff_monto"] == 0.0

    def test_diff_monto_calculada_en_match_sugerido(self, df_resultado):
        assert df_resultado.loc[1, "diff_monto"] == 200.0

    def test_diff_dias_cero_en_match_exacto(self, df_resultado):
        assert df_resultado.loc[0, "diff_dias"] == 1  # fecha_valor vs fecha_contable

    def test_diff_monto_vacio_en_manual(self, df_resultado):
        assert pd.isna(df_resultado.loc[2, "diff_monto"])

    def test_diff_dias_vacio_en_manual(self, df_resultado):
        assert pd.isna(df_resultado.loc[2, "diff_dias"])


# ─── Diagnóstico ─────────────────────────────────────────────────────────────

class TestDiagnostico:

    def test_motivo_presente_en_manual(self, df_resultado):
        assert df_resultado.loc[2, "motivo"] == "Monto coincide pero fecha fuera de rango"

    def test_motivo_none_en_exacto(self, df_resultado):
        assert pd.isna(df_resultado.loc[0, "motivo"])

    def test_monto_cercano_presente_en_manual(self, df_resultado):
        assert df_resultado.loc[2, "monto_cercano"] == -100_000.0

    def test_fecha_cercana_presente_en_manual(self, df_resultado):
        assert pd.notna(df_resultado.loc[2, "fecha_cercana"])

    def test_diff_monto_cercano_calculada(self, df_resultado):
        assert df_resultado.loc[2, "diff_monto_cercano"] == 300_000.0

    def test_datos_cercanos_none_en_exacto(self, df_resultado):
        assert pd.isna(df_resultado.loc[0, "monto_cercano"])


# ─── Antigüedad ───────────────────────────────────────────────────────────────

class TestAntiguedad:

    def test_tramo_vigente(self, libro, resultados_mixtos):
        cartola = pd.DataFrame({
            "fecha_operacion": [pd.Timestamp.today()],
            "fecha_valor":     [pd.Timestamp.today()],
            "glosa":           ["pago"],
            "rut":             ["19141427-6"],
            "monto":           [-100_000.0],
            "nro_documento":   ["1234567890"],
            "banco":           ["BCI"],
        })
        df = clasificar(cartola, libro, [resultados_mixtos[0]])
        assert df.loc[0, "tramo_antiguedad"] == "Vigente"

    def test_tramo_critico(self, libro, resultados_mixtos):
        cartola = pd.DataFrame({
            "fecha_operacion": [pd.Timestamp.today() - pd.Timedelta(days=100)],
            "fecha_valor":     [pd.Timestamp.today() - pd.Timedelta(days=100)],
            "glosa":           ["pago"],
            "rut":             ["19141427-6"],
            "monto":           [-100_000.0],
            "nro_documento":   ["1234567890"],
            "banco":           ["BCI"],
        })
        df = clasificar(cartola, libro, [resultados_mixtos[0]])
        assert df.loc[0, "tramo_antiguedad"] == "Crítico"


# ─── Acción recomendada ───────────────────────────────────────────────────────

class TestAccionRecomendada:

    def test_accion_exacto(self, df_resultado):
        assert df_resultado.loc[0, "accion_recomendada"] == "Aprobado — sin acción requerida"

    def test_accion_sugerido(self, df_resultado):
        assert df_resultado.loc[1, "accion_recomendada"] == "Revisar y aprobar match manualmente"

    def test_accion_iva(self, cartola, libro):
        resultados = [{
            "idx_cartola": 0, "idx_libro": None,
            "tipo_match": "Manual", "certeza": "Manual",
            "motivo": "Posible IVA",
            "flag_conciliacion": "",
            "flag_iva": "Posible Neto vs Bruto (×1.19)",
            "regla_aplicada": "",
            "idx_libro_cercano": None,
        }]
        df = clasificar(cartola, libro, resultados)
        assert df.loc[0, "accion_recomendada"] == "Revisar IVA — posible neto vs bruto"


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

    def test_cuadra_false_cuando_hay_diferencia(self, cartola, libro):
        resultado = calcular_diferencia_saldo(cartola, libro)
        assert resultado["cuadra"] == False

    def test_cuadra_true_cuando_montos_iguales(self):
        df = pd.DataFrame({"monto": [-100_000.0, 200_000.0]})
        resultado = calcular_diferencia_saldo(df, df)
        assert resultado["cuadra"] == True


# ─── separar_sin_conciliar ────────────────────────────────────────────────────

class TestSepararSinConciliar:

    def test_retorna_dataframe(self, df_resultado):
        assert isinstance(separar_sin_conciliar(df_resultado), pd.DataFrame)

    def test_solo_contiene_manual(self, df_resultado):
        resultado = separar_sin_conciliar(df_resultado)
        assert all(resultado["tipo_match"] == "Manual")

    def test_cantidad_correcta(self, df_resultado):
        assert len(separar_sin_conciliar(df_resultado)) == 1

    def test_index_reseteado(self, df_resultado):
        resultado = separar_sin_conciliar(df_resultado)
        assert list(resultado.index) == list(range(len(resultado)))