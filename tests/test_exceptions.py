"""
test_exceptions.py — Tests para utils/exceptions.py
"""
import pytest
from utils.exceptions import (
    ConciliadorError,
    IngestionError,
    ArchivoNoEncontradoError,
    ColumnaFaltanteError,
    NormalizacionError,
    ConciliacionError,
)


# Jerarquía de herencia

class TestJerarquia:

    def test_ingestion_es_conciliador_error(self):
        """IngestionError debe ser capturable como ConciliadorError."""
        assert issubclass(IngestionError, ConciliadorError)

    def test_archivo_no_encontrado_es_ingestion_error(self):
        assert issubclass(ArchivoNoEncontradoError, IngestionError)

    def test_columna_faltante_es_ingestion_error(self):
        assert issubclass(ColumnaFaltanteError, IngestionError)

    def test_normalizacion_es_conciliador_error(self):
        assert issubclass(NormalizacionError, ConciliadorError)

    def test_conciliacion_es_conciliador_error(self):
        assert issubclass(ConciliacionError, ConciliadorError)

    def test_todas_heredan_de_exception(self):
        """Todas deben ser excepciones válidas de Python."""
        for clase in [ConciliadorError, IngestionError, ArchivoNoEncontradoError,
                      ColumnaFaltanteError, NormalizacionError, ConciliacionError]:
            assert issubclass(clase, Exception)


# Mensajes de erro
class TestMensajes:

    def test_archivo_no_encontrado_incluye_ruta(self):
        """El mensaje debe mencionar la ruta del archivo."""
        ruta = "data/input/cartola_personal.xlsx"
        error = ArchivoNoEncontradoError(ruta)
        assert ruta in str(error)

    def test_columna_faltante_incluye_nombre_columna(self):
        """El mensaje debe mencionar el nombre de la columna."""
        error = ColumnaFaltanteError("Fecha Operación", "cartola.xlsx")
        assert "Fecha Operación" in str(error)

    def test_columna_faltante_incluye_nombre_archivo(self):
        """El mensaje debe mencionar el nombre del archivo."""
        error = ColumnaFaltanteError("Fecha Operación", "cartola.xlsx")
        assert "cartola.xlsx" in str(error)

    def test_normalizacion_incluye_mensaje(self):
        """El mensaje base debe aparecer en el error."""
        error = NormalizacionError("valor no numérico")
        assert "valor no numérico" in str(error)

    def test_normalizacion_incluye_columna_si_se_pasa(self):
        """Si se pasa columna, debe aparecer en el mensaje."""
        error = NormalizacionError("valor no numérico", columna="Monto Débito")
        assert "Monto Débito" in str(error)

    def test_normalizacion_sin_columna_no_falla(self):
        """NormalizacionError debe funcionar sin pasar columna."""
        error = NormalizacionError("dato inválido")
        assert "dato inválido" in str(error)


# Atributo

class TestAtributos:

    def test_archivo_no_encontrado_guarda_ruta(self):
        """La ruta debe quedar accesible como atributo."""
        ruta = "data/input/libro_banco.xlsx"
        error = ArchivoNoEncontradoError(ruta)
        assert error.ruta == ruta

    def test_columna_faltante_guarda_columna(self):
        """La columna debe quedar accesible como atributo."""
        error = ColumnaFaltanteError("Monto Crédito", "libro.xlsx")
        assert error.columna == "Monto Crédito"

    def test_columna_faltante_guarda_archivo(self):
        """El archivo debe quedar accesible como atributo."""
        error = ColumnaFaltanteError("Monto Crédito", "libro.xlsx")
        assert error.archivo == "libro.xlsx"

    def test_normalizacion_guarda_columna(self):
        """La columna debe quedar accesible como atributo."""
        error = NormalizacionError("error", columna="Fecha")
        assert error.columna == "Fecha"

    def test_normalizacion_columna_none_si_no_se_pasa(self):
        """Si no se pasa columna, el atributo debe ser None."""
        error = NormalizacionError("error")
        assert error.columna is None


# Comportamiento como excepciones

class TestComportamiento:

    def test_se_puede_lanzar_y_capturar_por_clase_base(self):
        """Una excepción hija debe ser capturable por ConciliadorError."""
        with pytest.raises(ConciliadorError):
            raise ArchivoNoEncontradoError("archivo.xlsx")

    def test_se_puede_lanzar_y_capturar_por_clase_propia(self):
        """Debe ser capturable por su propia clase."""
        with pytest.raises(ArchivoNoEncontradoError):
            raise ArchivoNoEncontradoError("archivo.xlsx")

    def test_columna_faltante_capturable_como_ingestion_error(self):
        with pytest.raises(IngestionError):
            raise ColumnaFaltanteError("Fecha", "cartola.xlsx")