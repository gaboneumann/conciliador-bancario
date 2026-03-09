"""
✔️ LISTO

Lo que debemos verificar:

1. Las rutas se resuelven correctamente
2. Los diccionarios de columnas tienen las claves esperadas
3. Las tolerancias son valores válidos
"""

"""
test_config.py — Tests para config/config.py
"""
import pytest
from pathlib import Path
from config.config import (
    BASE_DIR,
    INPUT_DIR,
    OUTPUT_DIR,
    LOGS_DIR,
    ARCHIVO_CARTOLA,
    ARCHIVO_LIBRO,
    ARCHIVO_RESULTADO,
    ARCHIVO_SIN_CONCILIAR,
    ARCHIVO_LOG,
    COLUMNAS_CARTOLA,
    COLUMNAS_LIBRO,
    TOLERANCIA_MONTO_PCT,
    TOLERANCIA_DIAS,
    TOLERANCIA_REFERENCIA,
)


# ─── Rutas ────────────────────────────────────────────────────────────────────

class TestRutas:

    def test_base_dir_es_directorio_del_proyecto(self):
        """BASE_DIR debe apuntar a la raíz del proyecto."""
        assert BASE_DIR.name == "conciliador_bancario"

    def test_rutas_son_absolutas(self):
        """Todas las rutas deben ser absolutas, no relativas."""
        for ruta in [BASE_DIR, INPUT_DIR, OUTPUT_DIR, LOGS_DIR]:
            assert ruta.is_absolute(), f"{ruta} no es absoluta"

    def test_rutas_de_datos_dentro_de_base_dir(self):
        """input/, output/ y logs/ deben estar dentro de data/."""
        assert str(INPUT_DIR).startswith(str(BASE_DIR))
        assert str(OUTPUT_DIR).startswith(str(BASE_DIR))
        assert str(LOGS_DIR).startswith(str(BASE_DIR))

    def test_archivos_de_entrada_en_input_dir(self):
        """Los archivos de entrada deben apuntar a la carpeta input/."""
        assert ARCHIVO_CARTOLA.parent == INPUT_DIR
        assert ARCHIVO_LIBRO.parent   == INPUT_DIR

    def test_archivos_de_salida_en_output_dir(self):
        """Los archivos de salida deben apuntar a la carpeta output/."""
        assert ARCHIVO_RESULTADO.parent     == OUTPUT_DIR
        assert ARCHIVO_SIN_CONCILIAR.parent == OUTPUT_DIR

    def test_archivo_log_en_logs_dir(self):
        """El archivo de log debe apuntar a la carpeta logs/."""
        assert ARCHIVO_LOG.parent == LOGS_DIR

    def test_extension_archivos_entrada(self):
        """Los archivos de entrada deben ser .xlsx"""
        assert ARCHIVO_CARTOLA.suffix == ".xlsx"
        assert ARCHIVO_LIBRO.suffix   == ".xlsx"

    def test_extension_archivos_salida(self):
        """Los archivos de salida deben ser .xlsx"""
        assert ARCHIVO_RESULTADO.suffix     == ".xlsx"
        assert ARCHIVO_SIN_CONCILIAR.suffix == ".xlsx"


# ─── Columnas ─────────────────────────────────────────────────────────────────

class TestColumnas:

    def test_cartola_tiene_claves_requeridas(self):
        claves_requeridas = {"fecha_operacion", "fecha_valor", "glosa", "rut", "cargo", "abono", "banco"}
        assert claves_requeridas.issubset(COLUMNAS_CARTOLA.keys())

    def test_libro_tiene_claves_requeridas(self):
        claves_requeridas = {"fecha_contable", "glosa", "rut", "debe", "haber", "nro_referencia", "nro_comprobante", "codigo_tx"}
        assert claves_requeridas.issubset(COLUMNAS_LIBRO.keys())   

    def test_valores_columnas_son_strings(self):
        """Los valores del mapeo deben ser strings no vacíos."""
        for clave, valor in COLUMNAS_CARTOLA.items():
            assert isinstance(valor, str) and valor.strip(), \
                f"COLUMNAS_CARTOLA['{clave}'] debe ser un string no vacío"

        for clave, valor in COLUMNAS_LIBRO.items():
            assert isinstance(valor, str) and valor.strip(), \
                f"COLUMNAS_LIBRO['{clave}'] debe ser un string no vacío"


# ─── Tolerancias ──────────────────────────────────────────────────────────────

class TestTolerancias:

    def test_tolerancia_monto_es_porcentaje_valido(self):
        """Debe ser un float entre 0 y 1."""
        assert isinstance(TOLERANCIA_MONTO_PCT, float)
        assert 0 < TOLERANCIA_MONTO_PCT < 1, \
            "La tolerancia de monto debe estar entre 0% y 100%"

    def test_tolerancia_dias_es_entero_positivo(self):
        """Debe ser un entero positivo."""
        assert isinstance(TOLERANCIA_DIAS, int)
        assert TOLERANCIA_DIAS > 0

    def test_tolerancia_referencia_es_entero_positivo(self):
        """Debe ser un entero positivo."""
        assert isinstance(TOLERANCIA_REFERENCIA, int)
        assert TOLERANCIA_REFERENCIA > 0
 
    def test_tolerancia_monto_es_dos_por_ciento(self):
        """Verificamos que el valor configurado es exactamente 2%."""
        assert TOLERANCIA_MONTO_PCT == 0.02

    def test_tolerancia_dias_es_cinco(self):
        """Verificamos que el valor configurado es exactamente 5 días."""
        assert TOLERANCIA_DIAS == 5