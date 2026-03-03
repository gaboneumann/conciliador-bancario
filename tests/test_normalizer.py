"""
test_normalizer.py — Tests para ingestion/normalizer.py (v2)
"""
import pytest
import pandas as pd
import numpy as np

from ingestion.normalizer import (
    normalizar_cartola,
    normalizar_libro,
    _normalizar_texto,
    _normalizar_referencia,
)
from utils.exceptions import NormalizacionError


# ─── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def df_cartola_crudo():
    """DataFrame con los mismos nombres de columna que el Excel real v2."""
    return pd.DataFrame({
        "Fecha Operación":      ["2024-01-15", "2024-02-20", "2024-03-10"],
        "Fecha Valor":          ["2024-01-16", "2024-02-21", "2024-03-11"],
        "Glosa":                ["  PAGO Luz Enel  ", "Transferéncia a Juan", "compra POS Lider"],
        "RUT Origen/Destino":   ["19.141.427-6", "21493875-8", "203580347"],
        "Cargos (CLP)":         [50000, 100000, None],
        "Abonos (CLP)":         [None, None, 200000],
        "Saldo Disponible":     [900000, 800000, 1000000],
        "Nº Documento":         ["1234567890", "ref-5678??", None],
        "Banco/Institución":    ["Banco de Chile", "BancoEstado", "BCI"],
    })


@pytest.fixture
def df_libro_crudo():
    """DataFrame con los mismos nombres de columna que el Excel real v2."""
    return pd.DataFrame({
        "Fecha Contable":       ["2024-01-15", "2024-02-20", "2024-03-10"],
        "Glosa Contable":       ["  PAGO Luz Enel  ", "Transferéncia a Juan", "compra POS Lider"],
        "RUT Auxiliar":         ["19.141.427-6", "21493875-8", "203580347"],
        "Debe (CLP)":           [50000, 100000, None],
        "Haber (CLP)":          [None, None, 200000],
        "Saldo":                [900000, 800000, 1000000],
        "Nº Referencia":        ["1234567890", "ref-5678??", None],
        "Nº Comprobante":       ["COMP001", "COMP002", "COMP003"],
        "Código Transacción":   ["SRV001", "TRF002", "POS003"],
    })


# ─── Tests _normalizar_texto ──────────────────────────────────────────────────

class TestNormalizarTexto:

    def test_elimina_espacios_extremos(self):
        assert _normalizar_texto("  hola  ") == "hola"

    def test_colapsa_espacios_internos(self):
        assert _normalizar_texto("pago  luz   enel") == "pago luz enel"

    def test_convierte_a_minusculas(self):
        assert _normalizar_texto("TRANSFERENCIA") == "transferencia"

    def test_elimina_acentos(self):
        assert _normalizar_texto("Transferéncia") == "transferencia"
        assert _normalizar_texto("Pago Ñoño") == "pago nono"

    def test_valor_no_string_retorna_vacio(self):
        assert _normalizar_texto(None) == ""
        assert _normalizar_texto(123)  == ""

    def test_string_vacio_retorna_vacio(self):
        assert _normalizar_texto("") == ""


# ─── Tests _normalizar_referencia ─────────────────────────────────────────────

class TestNormalizarReferencia:

    def test_convierte_a_uppercase(self):
        assert _normalizar_referencia("abc123") == "ABC123"

    def test_elimina_caracteres_especiales(self):
        assert _normalizar_referencia("ref-5678??") == "REF5678"

    def test_nulo_retorna_vacio(self):
        assert _normalizar_referencia(None) == ""
        assert _normalizar_referencia(np.nan) == ""

    def test_string_vacio_retorna_vacio(self):
        assert _normalizar_referencia("") == ""

    def test_solo_alfanumerico_no_cambia(self):
        assert _normalizar_referencia("1234567890") == "1234567890"


# ─── Tests normalizar_cartola ─────────────────────────────────────────────────

class TestNormalizarCartola:

    def test_retorna_dataframe(self, df_cartola_crudo):
        resultado = normalizar_cartola(df_cartola_crudo)
        assert isinstance(resultado, pd.DataFrame)

    def test_columnas_de_salida_correctas(self, df_cartola_crudo):
        resultado = normalizar_cartola(df_cartola_crudo)
        columnas_esperadas = [
            "fecha_operacion", "fecha_valor", "glosa", "rut",
            "monto", "nro_documento", "banco"
        ]
        assert list(resultado.columns) == columnas_esperadas

    def test_fecha_operacion_es_datetime(self, df_cartola_crudo):
        resultado = normalizar_cartola(df_cartola_crudo)
        assert pd.api.types.is_datetime64_any_dtype(resultado["fecha_operacion"])

    def test_fecha_valor_es_datetime(self, df_cartola_crudo):
        resultado = normalizar_cartola(df_cartola_crudo)
        assert pd.api.types.is_datetime64_any_dtype(resultado["fecha_valor"])

    def test_cargo_es_monto_negativo(self, df_cartola_crudo):
        resultado = normalizar_cartola(df_cartola_crudo)
        fila_cargo = resultado[resultado["monto"] == -50000]
        assert len(fila_cargo) == 1

    def test_abono_es_monto_positivo(self, df_cartola_crudo):
        resultado = normalizar_cartola(df_cartola_crudo)
        fila_abono = resultado[resultado["monto"] == 200000]
        assert len(fila_abono) == 1

    def test_glosa_normalizada(self, df_cartola_crudo):
        resultado = normalizar_cartola(df_cartola_crudo)
        assert "pago luz enel" in resultado["glosa"].values
        assert "transferencia a juan" in resultado["glosa"].values

    def test_nro_documento_normalizado(self, df_cartola_crudo):
        resultado = normalizar_cartola(df_cartola_crudo)
        assert "REF5678" in resultado["nro_documento"].values

    def test_rut_canonical_presente(self, df_cartola_crudo):
        """El RUT debe quedar en formato canonical después de normalizar."""
        resultado = normalizar_cartola(df_cartola_crudo)
        assert "19141427-6" in resultado["rut"].values

    def test_rut_sin_dv_se_normaliza(self, df_cartola_crudo):
        """RUT sin DV debe calcular y agregar el DV."""
        resultado = normalizar_cartola(df_cartola_crudo)
        assert "203580347-8" in resultado["rut"].values

    def test_elimina_filas_con_monto_cero(self):
        df = pd.DataFrame({
            "Fecha Operación":      ["2024-01-01"],
            "Fecha Valor":          ["2024-01-01"],
            "Glosa":                ["Sin monto"],
            "RUT Origen/Destino":   ["19.141.427-6"],
            "Cargos (CLP)":         [None],
            "Abonos (CLP)":         [None],
            "Saldo Disponible":     [0],
            "Nº Documento":         ["123"],
            "Banco/Institución":    ["BCI"],
        })
        resultado = normalizar_cartola(df)
        assert len(resultado) == 0


# ─── Tests normalizar_libro ───────────────────────────────────────────────────

class TestNormalizarLibro:

    def test_retorna_dataframe(self, df_libro_crudo):
        resultado = normalizar_libro(df_libro_crudo)
        assert isinstance(resultado, pd.DataFrame)

    def test_columnas_de_salida_correctas(self, df_libro_crudo):
        resultado = normalizar_libro(df_libro_crudo)
        columnas_esperadas = [
            "fecha_contable", "glosa", "rut",
            "monto", "nro_referencia", "nro_comprobante", "codigo_tx"
        ]
        assert list(resultado.columns) == columnas_esperadas

    def test_fecha_contable_es_datetime(self, df_libro_crudo):
        resultado = normalizar_libro(df_libro_crudo)
        assert pd.api.types.is_datetime64_any_dtype(resultado["fecha_contable"])

    def test_debe_es_monto_negativo(self, df_libro_crudo):
        resultado = normalizar_libro(df_libro_crudo)
        fila_debe = resultado[resultado["monto"] == -50000]
        assert len(fila_debe) == 1

    def test_haber_es_monto_positivo(self, df_libro_crudo):
        resultado = normalizar_libro(df_libro_crudo)
        fila_haber = resultado[resultado["monto"] == 200000]
        assert len(fila_haber) == 1

    def test_glosa_normalizada(self, df_libro_crudo):
        resultado = normalizar_libro(df_libro_crudo)
        assert "pago luz enel" in resultado["glosa"].values

    def test_rut_canonical_presente(self, df_libro_crudo):
        resultado = normalizar_libro(df_libro_crudo)
        assert "19141427-6" in resultado["rut"].values

    def test_rut_sin_dv_se_normaliza(self, df_libro_crudo):
        resultado = normalizar_libro(df_libro_crudo)
        assert "203580347-8" in resultado["rut"].values

    def test_nro_comprobante_se_preserva(self, df_libro_crudo):
        resultado = normalizar_libro(df_libro_crudo)
        assert "COMP001" in resultado["nro_comprobante"].values

    def test_codigo_tx_se_preserva(self, df_libro_crudo):
        resultado = normalizar_libro(df_libro_crudo)
        assert "SRV001" in resultado["codigo_tx"].values