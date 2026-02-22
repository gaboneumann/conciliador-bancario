"""
test_formatter.py — Tests para reporting/formatter.py
"""
import pytest
from openpyxl.styles import Font, PatternFill, Alignment, Border
from reporting.formatter import (
    estilo_encabezado,
    estilo_encabezado_bloque,
    estilo_fila,
    estilo_numero,
    estilo_fecha,
    COLORES,
    COLORES_BLOQUE,
    ANCHOS_RESULTADO,
    ANCHOS_SIN_CONCILIAR,
    BLOQUES_RESULTADO,
    BLOQUES_SIN_CONCILIAR,
)


# ─── estilo_encabezado ────────────────────────────────────────────────────────

class TestEstiloEncabezado:

    def test_retorna_dict(self):
        assert isinstance(estilo_encabezado(), dict)

    def test_tiene_claves_requeridas(self):
        for clave in ["font", "fill", "alignment", "border"]:
            assert clave in estilo_encabezado()

    def test_font_es_instancia_correcta(self):
        assert isinstance(estilo_encabezado()["font"], Font)

    def test_fill_es_instancia_correcta(self):
        assert isinstance(estilo_encabezado()["fill"], PatternFill)

    def test_alignment_es_instancia_correcta(self):
        assert isinstance(estilo_encabezado()["alignment"], Alignment)

    def test_border_es_instancia_correcta(self):
        assert isinstance(estilo_encabezado()["border"], Border)

    def test_fuente_es_blanca(self):
        assert estilo_encabezado()["font"].color.rgb[-6:] == "FFFFFF"

    def test_fuente_es_negrita(self):
        assert estilo_encabezado()["font"].bold is True

    def test_fondo_es_azul_oscuro(self):
        fill = estilo_encabezado()["fill"]
        assert fill.start_color.rgb[-6:] == COLORES["encabezado"]


# ─── estilo_encabezado_bloque ─────────────────────────────────────────────────

class TestEstiloEncabezadoBloque:

    def test_retorna_dict(self):
        assert isinstance(estilo_encabezado_bloque("cartola"), dict)

    def test_tiene_claves_requeridas(self):
        estilo = estilo_encabezado_bloque("cartola")
        for clave in ["font", "fill", "alignment", "border"]:
            assert clave in estilo

    def test_bloque_cartola_usa_color_correcto(self):
        fill = estilo_encabezado_bloque("cartola")["fill"]
        assert fill.start_color.rgb[-6:] == COLORES_BLOQUE["cartola"]

    def test_bloque_libro_usa_color_correcto(self):
        fill = estilo_encabezado_bloque("libro")["fill"]
        assert fill.start_color.rgb[-6:] == COLORES_BLOQUE["libro"]

    def test_bloque_resultado_usa_color_correcto(self):
        fill = estilo_encabezado_bloque("resultado")["fill"]
        assert fill.start_color.rgb[-6:] == COLORES_BLOQUE["resultado"]

    def test_bloque_diagnostico_usa_color_correcto(self):
        fill = estilo_encabezado_bloque("diagnostico")["fill"]
        assert fill.start_color.rgb[-6:] == COLORES_BLOQUE["diagnostico"]

    def test_fuente_es_blanca_y_negrita(self):
        font = estilo_encabezado_bloque("cartola")["font"]
        assert font.color.rgb[-6:] == "FFFFFF"
        assert font.bold is True

    def test_bloque_desconocido_no_falla(self):
        """Un bloque desconocido debe retornar estilo sin crashear."""
        estilo = estilo_encabezado_bloque("desconocido")
        assert isinstance(estilo, dict)


# ─── estilo_fila ──────────────────────────────────────────────────────────────

class TestEstiloFila:

    def test_retorna_dict(self):
        assert isinstance(estilo_fila("exacto"), dict)

    def test_tiene_claves_requeridas(self):
        for clave in ["font", "fill", "alignment", "border"]:
            assert clave in estilo_fila("exacto")

    def test_exacto_usa_color_verde(self):
        fill = estilo_fila("exacto")["fill"]
        assert fill.start_color.rgb[-6:] == COLORES["exacto"]

    def test_parcial_usa_color_amarillo(self):
        fill = estilo_fila("parcial")["fill"]
        assert fill.start_color.rgb[-6:] == COLORES["parcial"]

    def test_sin_match_usa_color_rojo(self):
        fill = estilo_fila("sin_match")["fill"]
        assert fill.start_color.rgb[-6:] == COLORES["sin_match"]

    def test_tipo_desconocido_usa_blanco(self):
        fill = estilo_fila("desconocido")["fill"]
        assert fill.start_color.rgb[-6:] == COLORES["blanco"]

    def test_fuente_no_es_negrita(self):
        assert not estilo_fila("exacto")["font"].bold


# ─── estilo_numero y estilo_fecha ─────────────────────────────────────────────

class TestEstilosAdicionales:

    def test_estilo_numero_tiene_number_format(self):
        assert "number_format" in estilo_numero()

    def test_estilo_fecha_tiene_number_format(self):
        assert "number_format" in estilo_fecha()

    def test_estilo_numero_alineacion_derecha(self):
        assert estilo_numero()["alignment"].horizontal == "right"

    def test_estilo_fecha_alineacion_centro(self):
        assert estilo_fecha()["alignment"].horizontal == "center"


# ─── Anchos de columna ────────────────────────────────────────────────────────

class TestAnchos:

    def test_anchos_resultado_tiene_13_columnas(self):
        assert len(ANCHOS_RESULTADO) == 13

    def test_anchos_sin_conciliar_tiene_10_columnas(self):
        """Ahora tiene 5 cartola + 5 diagnóstico."""
        assert len(ANCHOS_SIN_CONCILIAR) == 10

    def test_todos_los_anchos_son_positivos(self):
        for col, ancho in ANCHOS_RESULTADO.items():
            assert ancho > 0, f"Columna {col} tiene ancho inválido"


# ─── Bloques de encabezados ───────────────────────────────────────────────────

class TestBloques:

    def test_resultado_tiene_tres_bloques(self):
        assert len(BLOQUES_RESULTADO) == 3

    def test_sin_conciliar_tiene_dos_bloques(self):
        assert len(BLOQUES_SIN_CONCILIAR) == 2

    def test_bloques_resultado_cubren_13_columnas(self):
        """Los bloques deben cubrir exactamente las columnas 1 a 13."""
        col_inicio = BLOQUES_RESULTADO[0]["col_inicio"]
        col_fin    = BLOQUES_RESULTADO[-1]["col_fin"]
        assert col_inicio == 1
        assert col_fin    == 13

    def test_bloques_sin_conciliar_cubren_10_columnas(self):
        col_inicio = BLOQUES_SIN_CONCILIAR[0]["col_inicio"]
        col_fin    = BLOQUES_SIN_CONCILIAR[-1]["col_fin"]
        assert col_inicio == 1
        assert col_fin    == 10

    def test_cada_bloque_tiene_claves_requeridas(self):
        for bloque in BLOQUES_RESULTADO + BLOQUES_SIN_CONCILIAR:
            assert "nombre"     in bloque
            assert "bloque"     in bloque
            assert "col_inicio" in bloque
            assert "col_fin"    in bloque

    def test_bloques_resultado_son_contiguos(self):
        """Cada bloque debe empezar donde termina el anterior."""
        for i in range(1, len(BLOQUES_RESULTADO)):
            assert BLOQUES_RESULTADO[i]["col_inicio"] == BLOQUES_RESULTADO[i-1]["col_fin"] + 1