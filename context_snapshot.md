# Context Snapshot — Conciliador Bancario v2.2
**Fecha:** 2026-03-06
**Stack:** Python 3.12 · pandas 2.x · openpyxl 3.x · pytest · Git (ramas por módulo)
**Autor:** Gabriel Neumann — github.com/gaboneumann

---

## Arquitectura del proyecto

```
conciliador_bancario/
├── config/config.py          # TOLERANCIA_DIAS = 5 (era 3)
├── utils/
│   ├── logger.py
│   ├── exceptions.py
│   └── rut_utils.py
├── ingestion/
│   ├── reader.py
│   └── normalizer.py
├── conciliation/
│   ├── rules.py
│   ├── matcher.py            # ACTUALIZADO v2.1 — IVA→Sugerido, materialidad→Sugerido
│   └── classifier.py         # ACTUALIZADO v2.1 — textos accion_recomendada cortos
├── reporting/
│   ├── formatter.py          # ACTUALIZADO v2.2 — colores hallazgos (rojo concentración, naranja crítico)
│   └── writer.py             # ACTUALIZADO v2.2 — hoja Hallazgos_Criticos
├── data/
│   ├── input/
│   │   ├── cartola_bancaria.xlsx
│   │   └── libro_auxiliar.xlsx
│   └── output/
│       ├── conciliacion_resultado.xlsx   # 3 pestañas: Conciliación, Resumen, Hallazgos_Criticos
│       └── partidas_sin_conciliar.xlsx
├── tests/                    # TDD — 231+ tests
└── main.py

Excel → reader → normalizer → matcher → classifier → writer → Excel output
```

---

## Estado de módulos

| Módulo | Estado | Tests | Notas |
|---|---|---|---|
| `config/config.py` | ✅ | — | TOLERANCIA_DIAS = 5 (era 3) |
| `utils/rut_utils.py` | ✅ | 22 | sin cambios |
| `ingestion/reader.py` | ✅ | — | sin cambios |
| `ingestion/normalizer.py` | ✅ | — | sin cambios |
| `conciliation/rules.py` | ✅ | — | sin cambios |
| `conciliation/matcher.py` | ✅ | 17 | v2.1 — IVA→Sugerido, materialidad→Sugerido, ±5 días |
| `conciliation/classifier.py` | ✅ | — | v2.1 — textos accion_recomendada ≤50 chars |
| `reporting/formatter.py` | ✅ | — | v2.2 — colores hallazgos pendientes (PRD) |
| `reporting/writer.py` | ✅ | 20/20 | v2.2 — hoja Hallazgos_Criticos pendiente (PRD) |
| `main.py` | ✅ | — | sin cambios |

---

## Git — estado al cierre de sesión 2026-03-06

```
main
├── fix/matcher-v2.1
│   ├── fix(config): TOLERANCIA_DIAS 3 → 5
│   ├── fix(matcher): IVA→Sugerido, materialidad→Sugerido, ventana fecha ±5d
│   └── fix(classifier): acortar textos accion_recomendada
└── fix/synthetic-data-adjustments   ← repo generador
    └── fix(generators): RUT asimétrico, materialidad y cut-off para Sugerido ~10%
```

Convención de commits:
```
feat(módulo): descripción
fix(módulo):  descripción
docs(módulo): descripción
merge(rama-destino): integrar rama-origen
```

---

## Decisiones de diseño — acumuladas

- **RUT como llave maestra:** descarte inmediato si RUT no coincide.
- **Certeza en 3 niveles:** `Exacto / Sugerido / Manual`.
- **Cap materialidad $5.000 CLP:** `tolerancia = min(2%, $5.000)`.
- **IVA → Sugerido (v2.1):** si `detectar_iva()` es True en `_evaluar_candidato()`, certeza Sugerido + flag_iva. Antes iba a Manual.
- **Materialidad → Sugerido (v2.1):** si `montos_coinciden()` True y diff > 0, certeza_monto = Sugerido. Antes era Exacto.
- **Tolerancia fecha ±5 días (v2.1):** ampliada desde ±3. Casos a 4-5 días → Sugerido.
- **Partida en Conciliación:** flag independiente de certeza, activa cuando fecha_valor y fecha_contable son de meses distintos.
- **Prioridad de color en formatter:** azul (`#BDD7EE`) > verde agua (`#E2EFDA`) > color de certeza.
- **`separar_sin_conciliar()`** filtra por `"Manual"`.
- **Textos accion_recomendada ≤50 chars (v2.1):** mapa de motivos cortos para evitar desborde en Excel.

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
    "regla_aplicada":    str,   # "RUT + Monto + Fecha + Referencia + IVA ×1.19" etc.
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

## Resultados con datos sintéticos v2.1 (2026-03-06)

```
Total transacciones : 1.008
Exacto   :  719  (71.3%)
Sugerido :  166  (16.5%)   ← subió de 2.5% con fixes de IVA + materialidad
Manual   :  123  (12.2%)   ← bajó de 15.2%

Flag Partida Conciliación : 35 filas
Flag IVA (Sugerido)       : 31 filas   ← antes iban a Manual
Tramo Vigente             : 623
Tramo En Observación      : 253
Tramo Crítico             : 132

Saldo cartola  : -818,200,509
Saldo libro    :  [a recalcular con nueva ejecución]
Diferencia     :  -78,783,135   ← bajó de -564M con fixes de matcher
```

---

## PRD v2.2 — Módulo Hallazgos_Criticos (PENDIENTE DE IMPLEMENTAR)

**Origen:** diagnóstico del contador — sesión 2026-03-06
**Archivo de salida:** hoja adicional `Hallazgos_Criticos` en `conciliacion_resultado.xlsx`

### Columnas de la hoja
| # | Columna | Descripción |
|---|---|---|
| 1 | RUT | Identificador del tercero |
| 2 | Nombre/Glosa Frecuente | Glosa más frecuente del RUT |
| 3 | Cantidad Partidas | Nº de transacciones sin conciliar |
| 4 | Monto Total Pendiente | Suma de montos cartola |
| 5 | Motivo Principal | Predominancia Omisión vs Corte |
| 6 | Antigüedad Máxima | Días desde la partida más antigua |
| 7 | % sobre Total Error | Peso relativo del RUT en el descuadre |
| 8 | Alerta | "⚠️ Concentración >20%" si aplica |

### Lógica de colores
- **Rojo** `#FFC7CE` → RUT con alerta concentración >20%
- **Naranja** `#FFCC99` → Partida Crítica (>90 días) sin alerta de concentración
- **Sin color** → resto

### Criterios de aceptación
- Sumatoria `Monto Total Pendiente` debe cuadrar con `Diferencia` del Resumen
- Ordenado por `Antigüedad Máxima` DESC (Críticos primero)
- Tres pestañas en `conciliacion_resultado.xlsx`: `Conciliación`, `Resumen`, `Hallazgos_Criticos`

---

## Pendiente próxima sesión

1. Implementar `_escribir_hallazgos_criticos()` en `writer.py`
2. Agregar color naranja `#FFCC99` en `formatter.py` para hallazgos Críticos
3. Agregar `escribir_hallazgos_criticos()` al flujo de `escribir_resultado()` en `writer.py`
4. Tests para la nueva hoja
5. Commit: `feat(writer): hoja Hallazgos_Criticos con ranking por RUT y alertas`