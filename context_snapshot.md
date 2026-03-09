# Context Snapshot — Conciliador Bancario v2.3b
**Fecha:** 2026-03-09
**Stack:** Python 3.12 · pandas 2.x · openpyxl 3.x · pytest · Git (ramas por módulo)
**Autor:** Gabriel Neumann — github.com/gaboneumann

---

## Arquitectura del proyecto

```
conciliador_bancario/
├── config/config.py          # TOLERANCIA_DIAS = 5 | ARCHIVO_HALLAZGOS agregado
├── utils/
│   ├── logger.py
│   ├── exceptions.py
│   └── rut_utils.py
├── ingestion/
│   ├── reader.py
│   └── normalizer.py
├── conciliation/
│   ├── rules.py
│   ├── matcher.py            # v2.1 — IVA→Sugerido, materialidad→Sugerido, ±5 días
│   └── classifier.py         # v2.1 — textos accion_recomendada ≤50 chars
├── reporting/
│   ├── formatter.py          # v2.3 — estilo_texto_naranja() agregado
│   └── writer.py             # v2.3b — archivo independiente hallazgos, Opción B contador
├── data/
│   ├── input/
│   │   ├── cartola_bancaria.xlsx
│   │   └── libro_auxiliar.xlsx
│   └── output/
│       ├── conciliacion_resultado.xlsx        # 2 pestañas: Conciliación, Resumen
│       ├── partidas_sin_conciliar.xlsx
│       └── hallazgos_criticos_auditoria.xlsx  # NUEVO — archivo independiente
├── tests/                    # TDD — 231+ tests
└── main.py                   # escribir_hallazgos() agregado al paso 6

Excel → reader → normalizer → matcher → classifier → writer → Excel output
```

---

## Estado de módulos

| Módulo | Versión | Tests | Notas |
|---|---|---|---|
| `config/config.py` | v2.3 | — | TOLERANCIA_DIAS=5, ARCHIVO_HALLAZGOS agregado |
| `utils/rut_utils.py` | v2.0 | 22 | sin cambios |
| `ingestion/reader.py` | v2.0 | — | sin cambios |
| `ingestion/normalizer.py` | v2.0 | — | sin cambios |
| `conciliation/rules.py` | v2.0 | — | sin cambios |
| `conciliation/matcher.py` | v2.1 | 17 | IVA→Sugerido, materialidad→Sugerido, ±5 días |
| `conciliation/classifier.py` | v2.1 | — | textos accion_recomendada ≤50 chars |
| `reporting/formatter.py` | v2.3 | — | estilo_texto_naranja() agregado |
| `reporting/writer.py` | v2.3b | 20/20 | archivo hallazgos independiente, Opción B |
| `main.py` | v2.3 | — | escribir_hallazgos() en paso 6 |

---

## Git — estado al cierre de sesión 2026-03-09

```
Rama activa: feat/hallazgos-v2.3

main
├── feat/reporting (v2.2 — formatter y writer base)   ← commiteado
└── feat/hallazgos-v2.3                               ← EN PROGRESO (sin commitear aún)
    ├── config/config.py       → ARCHIVO_HALLAZGOS
    ├── reporting/formatter.py → estilo_texto_naranja()
    ├── reporting/writer.py    → escribir_hallazgos(), Opción B, fixes formato
    └── main.py                → escribir_hallazgos() en paso 6
```

**Commit pendiente (validar primero con python main.py):**
```bash
git add config/config.py reporting/formatter.py reporting/writer.py main.py
git commit -m "feat(writer): hallazgos_criticos_auditoria.xlsx independiente — Opción B contador"
```

**Luego merge a main:**
```bash
git checkout main
git merge feat/hallazgos-v2.3
git commit -m "merge(main): integrar feat/hallazgos-v2.3"
git push
```

Convención de commits:
```
feat(módulo): descripción
fix(módulo):  descripción
docs(módulo): descripción
merge(rama-destino): integrar rama-origen
```

---

## Cambios sesión 2026-03-09

### config/config.py
```python
ARCHIVO_HALLAZGOS = OUTPUT_DIR / "hallazgos_criticos_auditoria.xlsx"
```

### reporting/formatter.py
Nueva función agregada después de `estilo_hallazgo()`:
```python
def estilo_texto_naranja() -> dict:
    """Estilo de texto naranja para partidas Críticas en hallazgos."""
    return {
        "font": Font(name=FUENTE, size=TAMANO, color="FF6600"),
        "fill": PatternFill(fill_type="solid", start_color=COLORES["blanco"]),
        "alignment": Alignment(vertical="center"),
        "border": _borde_fino(),
    }
```

### reporting/writer.py — 3 fixes (v2.3b)
1. **Opción B (contador):** `_construir_hallazgos()` incluye dos familias:
   - `"Omisión Total"` → partidas Manual (monto_cartola completo)
   - `"Diferencia Parcial"` → partidas Sugerido (solo diff_monto)
   - Suma de ambas = diferencia de saldo exacta ✅
   - Nueva columna `"Familia"` en el reporte

2. **Header completo:** `BLOQUES_HALLAZGOS col_fin=10` cubre todas las columnas incluyendo "Plan de Acción"

3. **Bordes en Resumen:** `_escribir_resumen()` aplica `_borde_fino()` a todas las celdas

### main.py
```python
from reporting.writer import escribir_resultado, escribir_sin_conciliar, escribir_hallazgos
# paso 6:
escribir_hallazgos(df_resultado, saldo)
```

---

## Archivos de salida (3 archivos)

| Archivo | Pestañas | Contenido |
|---|---|---|
| `conciliacion_resultado.xlsx` | Conciliación, Resumen | Todas las transacciones + totales |
| `partidas_sin_conciliar.xlsx` | Sin Conciliar | 123 partidas Manual con diagnóstico |
| `hallazgos_criticos_auditoria.xlsx` | Hallazgos_Criticos | Ranking por RUT — tablero de control |

### Columnas hallazgos_criticos_auditoria.xlsx
| # | Columna | Descripción |
|---|---|---|
| 1 | RUT | Identificador del tercero |
| 2 | Glosa Frecuente | Glosa más frecuente del RUT |
| 3 | Cantidad Partidas | Nº de transacciones agrupadas |
| 4 | Monto Pendiente | Suma monto_cartola (Manual) + diff_monto (Sugerido) |
| 5 | Familia | "Omisión Total" o "Diferencia Parcial" |
| 6 | Motivo Principal | Omisión / Corte / IVA / Ausente / Materialidad |
| 7 | Días de Atraso | Antigüedad máxima del RUT |
| 8 | % sobre Total Error | Peso relativo del RUT en el descuadre |
| 9 | Alerta | "⚠️ Riesgo de Concentración Alto" si >20% |
| 10 | Plan de Acción | Vacío — para el responsable de área |

### Lógica de colores hallazgos
- **Fondo Rojo** `#FFC7CE` → RUT con alerta concentración >20%
- **Texto Naranja** `#FF6600` → Partidas Críticas (>90 días) sin alerta de concentración
- **Sin color** → resto

---

## Decisiones de diseño — acumuladas

- **RUT como llave maestra:** descarte inmediato si RUT no coincide.
- **Certeza en 3 niveles:** `Exacto / Sugerido / Manual`.
- **Cap materialidad $5.000 CLP:** `tolerancia = min(2%, $5.000)`.
- **IVA → Sugerido (v2.1):** `detectar_iva()` True → certeza Sugerido + flag_iva.
- **Materialidad → Sugerido (v2.1):** `montos_coinciden()` True y diff > 0 → certeza Sugerido.
- **Tolerancia fecha ±5 días (v2.1):** ampliada desde ±3.
- **Partida en Conciliación:** flag independiente de certeza. Activa cuando fecha_valor y fecha_contable son de meses distintos.
- **Prioridad de color en formatter:** azul (`#BDD7EE`) > verde agua (`#E2EFDA`) > color de certeza.
- **`separar_sin_conciliar()`** filtra por `"Manual"`.
- **Textos accion_recomendada ≤50 chars (v2.1):** mapa de motivos cortos para evitar desborde en Excel.
- **Opción B hallazgos (v2.3b):** hallazgos incluye Manuales + Sugeridos para cuadrar con diferencia de saldo. Decisión del contador: "la cuadratura es intransable".
- **Archivo hallazgos independiente (v2.3):** separado de conciliacion_resultado.xlsx para enviar a responsables de área sin exponer cartola completa.

---

## Esquemas de datos internos

### Salida de `normalizer.py`
```
cartola: fecha_operacion, fecha_valor, glosa, rut, monto, nro_documento, banco
libro  : fecha_contable, glosa, rut, monto, nro_referencia, nro_comprobante, codigo_tx
```

### Salida de `matcher.py` (lista de dicts)
```python
{
    "idx_cartola":       int,
    "idx_libro":         int | None,
    "tipo_match":        "Exacto" | "Sugerido" | "Manual",
    "certeza":           "Exacto" | "Sugerido" | "Manual",
    "motivo":            str | None,
    "flag_conciliacion": str,   # "Partida en Conciliación" o ""
    "flag_iva":          str,   # "Posible Neto vs Bruto (×1.19)" o ""
    "regla_aplicada":    str,
    "idx_libro_cercano": int | None,
}
```

### Salida de `classifier.py` (DataFrame — 24 columnas)
```
Cartola (7): fecha_operacion_cartola, fecha_valor_cartola, glosa_cartola,
             rut_cartola, monto_cartola, nro_documento_cartola, banco_cartola

Libro (7):   fecha_contable_libro, glosa_libro, rut_libro, monto_libro,
             nro_referencia_libro, nro_comprobante_libro, codigo_tx_libro

Match (10):  tipo_match, certeza, regla_aplicada, diff_monto, diff_dias,
             flag_conciliacion, flag_iva, dias_antiguedad, tramo_antiguedad,
             accion_recomendada

Diagnóstico (solo Manual): motivo, fecha_cercana, monto_cercano,
                            glosa_cercana, diff_monto_cercano
```

---

## Resultados con datos sintéticos (última ejecución 2026-03-09)

```
Total transacciones : 1.008
Exacto   :  719  (71.3%)
Sugerido :  166  (16.5%)
Manual   :  123  (12.2%)

Flag Partida Conciliación : 35 filas
Flag IVA (Sugerido)       : 31 filas
Tramo Vigente             : 623
Tramo En Observación      : 253
Tramo Crítico             : 132

Saldo cartola  : -779,660,376
Saldo libro    : -700,877,241
Diferencia     :  -78,783,135
```

---

## Pendiente próxima sesión

1. **[VALIDAR]** `python main.py` → confirmar `Hallazgos cuadra con diferencia de saldo ✅`
2. **[VALIDAR]** Revisar Excel hallazgos: header cubre A→J, bordes en Resumen, columna Familia visible
3. **[TESTS]** Escribir tests para `escribir_hallazgos()` y `_construir_hallazgos()` antes del merge
4. **[COMMIT]** Si todo OK:
   ```bash
   git add config/config.py reporting/formatter.py reporting/writer.py main.py
   git commit -m "feat(writer): hallazgos_criticos_auditoria.xlsx independiente — Opción B contador"
   git checkout main
   git merge feat/hallazgos-v2.3
   git commit -m "merge(main): integrar feat/hallazgos-v2.3"
   git push
   ```
5. **[SIGUIENTE PRD]** Confirmar con contador si hay nuevos requerimientos post v2.3b