"""
test_main.py — Tests para main.py
"""
import pytest
import pandas as pd
from unittest.mock import patch
from main import main
from utils.exceptions import ArchivoNoEncontradoError


# ─── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def df_cartola():
    return pd.DataFrame({
        "fecha":       pd.to_datetime(["2024-01-15"]),
        "monto":       [-100_000.0],
        "descripcion": ["pago luz enel"],
        "referencia":  ["1234567890"],
        "banco":       ["Banco de Chile"],
    })


@pytest.fixture
def df_libro():
    return pd.DataFrame({
        "fecha":       pd.to_datetime(["2024-01-15"]),
        "monto":       [-100_000.0],
        "descripcion": ["pago luz enel"],
        "referencia":  ["1234567890"],
        "codigo":      ["SRV001"],
    })


@pytest.fixture
def df_resultado():
    return pd.DataFrame({
        "fecha_cartola":       pd.to_datetime(["2024-01-15"]),
        "monto_cartola":       [-100_000.0],
        "descripcion_cartola": ["pago luz enel"],
        "referencia_cartola":  ["1234567890"],
        "banco_cartola":       ["Banco de Chile"],
        "fecha_libro":         pd.to_datetime(["2024-01-15"]),
        "monto_libro":         [-100_000.0],
        "descripcion_libro":   ["pago luz enel"],
        "referencia_libro":    ["1234567890"],
        "codigo_libro":        ["SRV001"],
        "tipo_match":          ["exacto"],
        "certeza":             ["Exacto"],   # ← agregado
        "diff_monto":          [0.0],
        "diff_dias":           [0],
        "motivo":              [None],
        "fecha_cercana":       [None],
        "monto_cercano":       [None],
        "descripcion_cercana": [None],
        "diff_monto_cercano":  [None],
    })


@pytest.fixture
def saldo_mock():
    return {
        "saldo_cartola": -100_000.0,
        "saldo_libro":   -100_000.0,
        "diferencia":    0.0,
        "cuadra":        True,
    }


# ─── Flujo exitoso ────────────────────────────────────────────────────────────

class TestFlujoExitoso:

    def test_main_ejecuta_sin_errores(
        self, df_cartola, df_libro, df_resultado, saldo_mock
    ):
        resultados_mock = [
            {"idx_cartola": 0, "idx_libro": 0, "tipo_match": "exacto",
             "motivo": None, "idx_libro_cercano": None}
        ]
        with patch("main.leer_cartola",               return_value=df_cartola), \
             patch("main.leer_libro",                 return_value=df_libro), \
             patch("main.normalizar_cartola",         return_value=df_cartola), \
             patch("main.normalizar_libro",           return_value=df_libro), \
             patch("main.hacer_matching",             return_value=resultados_mock), \
             patch("main.clasificar",                 return_value=df_resultado), \
             patch("main.calcular_diferencia_saldo",  return_value=saldo_mock), \
             patch("main.escribir_resultado"), \
             patch("main.escribir_sin_conciliar"), \
             patch("main.escribir_hallazgos"):        # ← agregado
            main()

    def test_main_llama_todos_los_pasos(
        self, df_cartola, df_libro, df_resultado, saldo_mock
    ):
        """Los 6 pasos deben llamarse exactamente una vez."""
        resultados_mock = [
            {"idx_cartola": 0, "idx_libro": 0, "tipo_match": "exacto",
             "motivo": None, "idx_libro_cercano": None}
        ]
        with patch("main.leer_cartola",               return_value=df_cartola) as p1, \
             patch("main.leer_libro",                 return_value=df_libro)   as p2, \
             patch("main.normalizar_cartola",         return_value=df_cartola) as p3, \
             patch("main.normalizar_libro",           return_value=df_libro)   as p4, \
             patch("main.hacer_matching",             return_value=resultados_mock) as p5, \
             patch("main.clasificar",                 return_value=df_resultado) as p6, \
             patch("main.calcular_diferencia_saldo",  return_value=saldo_mock) as p7, \
             patch("main.escribir_resultado")         as p8, \
             patch("main.escribir_sin_conciliar")     as p9, \
             patch("main.escribir_hallazgos")         as p10:  # ← agregado
            main()

        for mock in [p1, p2, p3, p4, p5, p6, p7, p8, p9, p10]:
            mock.assert_called_once()

    def test_saldo_se_pasa_a_escribir_resultado(
        self, df_cartola, df_libro, df_resultado, saldo_mock
    ):
        """El saldo calculado debe pasarse como argumento a escribir_resultado."""
        resultados_mock = [
            {"idx_cartola": 0, "idx_libro": 0, "tipo_match": "exacto",
             "motivo": None, "idx_libro_cercano": None}
        ]
        with patch("main.leer_cartola",               return_value=df_cartola), \
             patch("main.leer_libro",                 return_value=df_libro), \
             patch("main.normalizar_cartola",         return_value=df_cartola), \
             patch("main.normalizar_libro",           return_value=df_libro), \
             patch("main.hacer_matching",             return_value=resultados_mock), \
             patch("main.clasificar",                 return_value=df_resultado), \
             patch("main.calcular_diferencia_saldo",  return_value=saldo_mock), \
             patch("main.escribir_resultado")         as mock_escribir, \
             patch("main.escribir_sin_conciliar"), \
             patch("main.escribir_hallazgos"):        # ← agregado
            main()

        args, kwargs = mock_escribir.call_args
        saldo_recibido = args[1] if len(args) > 1 else kwargs.get("saldo")
        assert saldo_recibido == saldo_mock


# ─── Manejo de errores ────────────────────────────────────────────────────────

class TestManejoErrores:

    def test_archivo_no_encontrado_lanza_system_exit(self):
        with patch("main.leer_cartola",
                   side_effect=ArchivoNoEncontradoError("cartola.xlsx")):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1

    def test_error_inesperado_lanza_system_exit(self):
        with patch("main.leer_cartola",
                   side_effect=RuntimeError("error inesperado")):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1