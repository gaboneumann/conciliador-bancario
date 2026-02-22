"""
test_normalizer.py — Tests para ingestion/normalizer.py
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime

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
    """DataFrame con los mismos nombres de columna que el Excel real."""
    return pd.DataFrame({
        "Fecha Operación":        ["2024-01-15", "2024-02-20", "2024-03-10"],
        "Descripción Operación":  ["  PAGO Luz Enel  ", "Transferéncia a Juan", "compra POS Lider"],
        "Cargo (CLP)":            [50000, 100000, None],
        "Abono (CLP)":            [None, None, 200000],
        "Referencia Interna":     ["1234567890", "ref-5678??", None],
        "Banco/Institución":      ["Banco de Chile", "BancoEstado", "BCI"],
    })


@pytest.fixture
def df_libro_crudo():
    """DataFrame con los mismos nombres de columna que el Excel real."""
    return pd.DataFrame({
        "Fecha Contable":     ["2024-01-15", "2024-02-20", "2024-03-10"],
        "Descripción":        ["  PAGO Luz Enel  ", "Transferéncia a Juan", "compra POS Lider"],
        "Monto Débito":       [50000, 100000, None],
        "Monto Crédito":      [None, None, 200000],
        "Número Referencia":  ["1234567890", "ref-5678??", None],
        "Código Transacción": ["SRV001", "TRF002", "POS003"],
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
        assert list(resultado.columns) == ["fecha", "descripcion", "monto", "referencia", "banco"]

    def test_fecha_es_datetime(self, df_cartola_crudo):
        resultado = normalizar_cartola(df_cartola_crudo)
        assert pd.api.types.is_datetime64_any_dtype(resultado["fecha"])

    def test_cargo_es_monto_negativo(self, df_cartola_crudo):
        """Un cargo de 50.000 debe quedar como -50.000."""
        resultado = normalizar_cartola(df_cartola_crudo)
        fila_cargo = resultado[resultado["monto"] == -50000]
        assert len(fila_cargo) == 1

    def test_abono_es_monto_positivo(self, df_cartola_crudo):
        """Un abono de 200.000 debe quedar como +200.000."""
        resultado = normalizar_cartola(df_cartola_crudo)
        fila_abono = resultado[resultado["monto"] == 200000]
        assert len(fila_abono) == 1

    def test_descripcion_normalizada(self, df_cartola_crudo):
        resultado = normalizar_cartola(df_cartola_crudo)
        assert "pago luz enel" in resultado["descripcion"].values
        assert "transferencia a juan" in resultado["descripcion"].values

    def test_referencia_normalizada(self, df_cartola_crudo):
        resultado = normalizar_cartola(df_cartola_crudo)
        assert "REF5678" in resultado["referencia"].values

    def test_elimina_filas_con_monto_cero(self):
        """Filas donde cargo y abono son ambos NaN deben eliminarse."""
        df = pd.DataFrame({
            "Fecha Operación":       ["2024-01-01"],
            "Descripción Operación": ["Sin monto"],
            "Cargo (CLP)":           [None],
            "Abono (CLP)":           [None],
            "Referencia Interna":    ["123"],
            "Banco/Institución":     ["BCI"],
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
        assert list(resultado.columns) == ["fecha", "descripcion", "monto", "referencia", "codigo"]

    def test_fecha_es_datetime(self, df_libro_crudo):
        resultado = normalizar_libro(df_libro_crudo)
        assert pd.api.types.is_datetime64_any_dtype(resultado["fecha"])

    def test_debito_es_monto_negativo(self, df_libro_crudo):
        resultado = normalizar_libro(df_libro_crudo)
        fila_debito = resultado[resultado["monto"] == -50000]
        assert len(fila_debito) == 1

    def test_credito_es_monto_positivo(self, df_libro_crudo):
        resultado = normalizar_libro(df_libro_crudo)
        fila_credito = resultado[resultado["monto"] == 200000]
        assert len(fila_credito) == 1

    def test_descripcion_normalizada(self, df_libro_crudo):
        resultado = normalizar_libro(df_libro_crudo)
        assert "pago luz enel" in resultado["descripcion"].values

    def test_codigo_se_preserva(self, df_libro_crudo):
        resultado = normalizar_libro(df_libro_crudo)
        assert "SRV001" in resultado["codigo"].values