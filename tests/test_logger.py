"""
Lo que debemos verificar:

1. El logger se crea correctamente
2. Escribe en el archivo de log
3. No duplica handlers si se llama dos veces
"""

"""
test_logger.py — Tests para utils/logger.py
"""
import logging
import pytest
from pathlib import Path
from utils.logger import get_logger
from config.config import ARCHIVO_LOG


# ─── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def limpiar_logger():
    """
    Limpia el logger antes de cada test para evitar contaminación entre tests.
    Sin esto, los handlers se acumulan entre tests y los resultados son impredecibles.
    """
    logger = logging.getLogger("test_logger")
    logger.handlers.clear()
    yield
    logger.handlers.clear()


@pytest.fixture
def logger():
    return get_logger("test_logger")


# ─── Creación del logger ──────────────────────────────────────────────────────

class TestCreacionLogger:

    def test_retorna_instancia_de_logger(self, logger):
        """get_logger debe retornar un objeto Logger de Python."""
        assert isinstance(logger, logging.Logger)

    def test_logger_tiene_dos_handlers(self, logger):
        """Debe tener exactamente 2 handlers: consola y archivo."""
        assert len(logger.handlers) == 2

    def test_logger_tiene_handler_de_consola(self, logger):
        """Uno de los handlers debe ser StreamHandler (consola)."""
        tipos = [type(h) for h in logger.handlers]
        assert logging.StreamHandler in tipos

    def test_logger_tiene_handler_de_archivo(self, logger):
        """Uno de los handlers debe ser FileHandler (archivo)."""
        tipos = [type(h) for h in logger.handlers]
        assert logging.FileHandler in tipos

    def test_nivel_del_logger_es_debug(self, logger):
        """El logger debe capturar desde DEBUG hacia arriba."""
        assert logger.level == logging.DEBUG


# ─── Niveles de cada handler ──────────────────────────────────────────────────

class TestNivelesHandlers:

    def test_handler_consola_nivel_info(self, logger):
        """La consola solo debe mostrar INFO y superior."""
        stream_handlers = [h for h in logger.handlers
                           if type(h) is logging.StreamHandler]
        assert stream_handlers[0].level == logging.INFO

    def test_handler_archivo_nivel_debug(self, logger):
        """El archivo debe guardar todo desde DEBUG."""
        file_handlers = [h for h in logger.handlers
                         if isinstance(h, logging.FileHandler)]
        assert file_handlers[0].level == logging.DEBUG


# ─── Escritura en archivo ─────────────────────────────────────────────────────

class TestEscrituraArchivo:

    def test_crea_archivo_de_log(self, logger):
        """El archivo de log debe existir tras usar el logger."""
        logger.info("mensaje de prueba")
        assert ARCHIVO_LOG.exists()

    def test_escribe_mensaje_en_archivo(self, logger, tmp_path):
        """El mensaje enviado debe aparecer en el archivo de log."""
        logger.info("mensaje único de verificación 12345")
        contenido = ARCHIVO_LOG.read_text(encoding="utf-8")
        assert "mensaje único de verificación 12345" in contenido

    def test_escribe_nivel_debug_en_archivo(self, logger):
        """Los mensajes DEBUG deben quedar guardados en el archivo."""
        logger.debug("debug de verificación 99999")
        contenido = ARCHIVO_LOG.read_text(encoding="utf-8")
        assert "debug de verificación 99999" in contenido


# ─── Sin duplicación de handlers ─────────────────────────────────────────────

class TestSinDuplicacion:

    def test_llamar_dos_veces_no_duplica_handlers(self):
        """Llamar get_logger dos veces con el mismo nombre no debe duplicar handlers."""
        logger1 = get_logger("logger_duplicado")
        logger2 = get_logger("logger_duplicado")
        assert len(logger2.handlers) == 2