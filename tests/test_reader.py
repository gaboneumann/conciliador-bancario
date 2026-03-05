"""
test_reader.py — Tests para ingestion/reader.py (v2)
"""
import pytest
import pandas as pd
from pathlib import Path
from unittest.mock import patch

from ingestion.reader import leer_cartola, leer_libro, _leer_excel
from utils.exceptions import ArchivoNoEncontradoError, ColumnaFaltanteError
from config.config import COLUMNAS_CARTOLA, COLUMNAS_LIBRO


# ─── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def cartola_excel(tmp_path) -> Path:
    """Crea un Excel de cartola válido en una carpeta temporal."""
    ruta = tmp_path / "cartola_bancaria.xlsx"
    df = pd.DataFrame({
        "Fecha Operación":      ["2024-01-01", "2024-01-02"],
        "Fecha Valor":          ["2024-01-02", "2024-01-03"],
        "Glosa":                ["Transferencia a Juan", "Pago Luz Enel"],
        "RUT Origen/Destino":   ["19.141.427-6", "21493875-8"],
        "Cargos (CLP)":         [100000, 50000],
        "Abonos (CLP)":         [None, None],
        "Saldo Disponible":     [900000, 850000],
        "Nº Documento":         ["1234567890", "0987654321"],
        "Banco/Institución":    ["Banco de Chile", "BancoEstado"],
    })
    df.to_excel(ruta, index=False)
    return ruta


@pytest.fixture
def libro_excel(tmp_path) -> Path:
    """Crea un Excel de libro auxiliar válido en una carpeta temporal."""
    ruta = tmp_path / "libro_auxiliar.xlsx"
    df = pd.DataFrame({
        "Fecha Contable":       ["2024-01-01", "2024-01-02"],
        "Glosa Contable":       ["Transferencia a Juan", "Pago Luz Enel"],
        "RUT Auxiliar":         ["19.141.427-6", "21493875-8"],
        "Debe (CLP)":           [100000, 50000],
        "Haber (CLP)":          [None, None],
        "Saldo":                [900000, 850000],
        "Nº Referencia":        ["1234567890", "0987654321"],
        "Nº Comprobante":       ["COMP001", "COMP002"],
        "Código Transacción":   ["TRF001", "SRV002"],
    })
    df.to_excel(ruta, index=False)
    return ruta


@pytest.fixture
def excel_sin_columnas(tmp_path) -> Path:
    """Crea un Excel con columnas incorrectas para testear el error."""
    ruta = tmp_path / "malo.xlsx"
    df = pd.DataFrame({"Columna Rara": [1, 2], "Otra Columna": [3, 4]})
    df.to_excel(ruta, index=False)
    return ruta


# ─── Lectura exitosa ──────────────────────────────────────────────────────────

class TestLecturaExitosa:

    def test_retorna_dataframe(self, cartola_excel):
        df = _leer_excel(cartola_excel, COLUMNAS_CARTOLA)
        assert isinstance(df, pd.DataFrame)

    def test_cantidad_de_filas_correcta(self, cartola_excel):
        df = _leer_excel(cartola_excel, COLUMNAS_CARTOLA)
        assert len(df) == 2

    def test_columnas_del_excel_presentes(self, cartola_excel):
        df = _leer_excel(cartola_excel, COLUMNAS_CARTOLA)
        for nombre_excel in COLUMNAS_CARTOLA.values():
            assert nombre_excel in df.columns

    def test_leer_libro_retorna_dataframe(self, libro_excel):
        with patch("ingestion.reader.ARCHIVO_LIBRO", libro_excel):
            df = leer_libro()
        assert isinstance(df, pd.DataFrame)

    def test_leer_cartola_retorna_dataframe(self, cartola_excel):
        with patch("ingestion.reader.ARCHIVO_CARTOLA", cartola_excel):
            df = leer_cartola()
        assert isinstance(df, pd.DataFrame)


# ─── Errores esperados ────────────────────────────────────────────────────────

class TestErrores:

    def test_archivo_inexistente_lanza_error(self, tmp_path):
        ruta_falsa = tmp_path / "no_existe.xlsx"
        with pytest.raises(ArchivoNoEncontradoError):
            _leer_excel(ruta_falsa, COLUMNAS_CARTOLA)

    def test_error_incluye_la_ruta(self, tmp_path):
        ruta_falsa = tmp_path / "no_existe.xlsx"
        with pytest.raises(ArchivoNoEncontradoError) as exc_info:
            _leer_excel(ruta_falsa, COLUMNAS_CARTOLA)
        assert "no_existe.xlsx" in str(exc_info.value)

    def test_columna_faltante_lanza_error(self, excel_sin_columnas):
        with pytest.raises(ColumnaFaltanteError):
            _leer_excel(excel_sin_columnas, COLUMNAS_CARTOLA)

    def test_error_columna_menciona_nombre_columna(self, excel_sin_columnas):
        with pytest.raises(ColumnaFaltanteError) as exc_info:
            _leer_excel(excel_sin_columnas, COLUMNAS_CARTOLA)
        assert "Fecha Operación" in str(exc_info.value)