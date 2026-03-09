# Context Snapshot — Conciliador Bancario v2.3f
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
│   └── classifier.py         # v2.1+ — idx_libro agregado al dict de resultado
├── reporting/
│   ├── formatter.py          # v2.3 — estilo_texto_naranja() agregado
│   └── writer.py             # v2.3f — 3 familias MI, IDs Referencia, cuadratura total
├── data/
│   ├── input/
│   │   ├── cartola_bancaria.xlsx
│   │   └── libro_auxiliar.xlsx
│   └── output/
│       ├── conciliacion_resultado.xlsx        # 2 pestañas: Conciliación, Resumen
│       ├── partidas_sin_conciliar.xlsx
│       └── hallazgos_criticos_auditoria.xlsx  # 9 columnas — ranking por RUT
├── tests/                    # TDD — 265 tests
└── main.py                   # escribir_hallazgos(df_resultado, saldo, libro) en paso 6

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
| `conciliation/rules.py` | v2.1 | — | TOLERANCIA_DIAS=5 (tests actualizados) |
| `conciliation/matcher.py` | v2.1 | 17 | IVA→Sugerido, materialidad→Sugerido, ±5 días |
| `conciliation/classifier.py` | v2.1+ | — | idx_libro agregado al dict de resultado |
| `reporting/formatter.py` | v2.3 | — | estilo_texto_naranja() agregado |
| `reporting/writer.py` | v2.3f | 265/265 | 3 familias MI + IDs Referencia + cuadratura ✅ |
| `main.py` | v2.3 | — | escribir_hallazgos(df_resultado, saldo, libro) |

---

## Git — estado al cierre de sesión 2026-03-09

```
Rama activa: feat/hallazgos-v2.3

Commits en rama:
  feat(writer): hallazgos_criticos_auditoria.xlsx — cuadratura total TRD v2.3
  feat(writer): columna IDs Referencia — trazabilidad auditoría TRD v2.3f   ← HEAD
```

**Merge a main pendiente:**
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

## Cambios acumulados esta sesión (2026-03-09)

### conciliation/classifier.py
Agregado `idx_libro` al dict de resultado en `clasificar()`:
```python
# Con match:
"idx_libro": idx_l,   # int — índice de la fila del libro que matcheó

# Sin match:
"idx_libro": None,
```
Propósito: permitir al writer identificar exactamente qué filas del libro están sin par,
usando índices en lugar de comprobantes (que tienen duplicados).

### reporting/writer.py — v2.3f
**3 familias de MI para cuadratura total:**

| Familia | MI | ID |
|---|---|---|
| Manual | `monto_cartola` | `nro_documento_cartola` |
| Sugerido (diff≠0) | `monto_cartola - monto_libro` | `nro_documento_cartola` |
| Libro sin Par | `-monto_libro` | `nro_comprobante` |

`sum(MI) == saldo_cartola - saldo_libro` ✅

**Ecuación de cuadratura:**
```
MI = Manuales + Sugeridos - Libro_sin_Par
   = -82,072,126 + (-22,703,242) - (-25,992,233)
   = -78,783,135 ✅
```

**Nueva columna IDs Referencia (col F):**
- Concatena todos los IDs del RUT con separador ` | `
- `wrap_text=True` en la celda para legibilidad
- Ancho columna F: 45

### Tests actualizados
| Test | Cambio |
|---|---|
| `test_tolerancia_dias_es_tres` | → `test_tolerancia_dias_es_cinco` (valor 5) |
| `test_diferencia_fuera_de_tolerancia` | fecha 19→21 (6 días, fuera de ±5) |
| `test_diferencia_exactamente_en_limite` | fecha 18→20 (límite exacto ±5) |
| `test_accion_iva` | texto actualizado v2.1 |
| `test_anchos_resultado_tiene_13_columnas` | → 24 columnas v2 |
| `test_bloques_resultado_cubren_13_columnas` | → col_fin=24 |
| `test_cartola_tiene_claves_requeridas` | claves v2 |
| `test_libro_tiene_claves_requeridas` | claves v2 |

---

## Archivos de salida (3 archivos)

| Archivo | Pestañas | Contenido |
|---|---|---|
| `conciliacion_resultado.xlsx` | Conciliación, Resumen | Todas las transacciones + totales |
| `partidas_sin_conciliar.xlsx` | Sin Conciliar | 123 partidas Manual con diagnóstico |
| `hallazgos_criticos_auditoria.xlsx` | Hallazgos_Criticos | Ranking por RUT — tablero de control |

### Columnas hallazgos_criticos_auditoria.xlsx (v2.3f — 9 columnas)
| # | Col | Encabezado | Descripción |
|---|---|---|---|
| 1 | A | RUT | Identificador del tercero |
| 2 | B | Glosa Frecuente | Glosa más frecuente del RUT |
| 3 | C | Cant. Partidas | Nº de transacciones agrupadas |
| 4 | D | Monto de Impacto | sum(MI) por RUT |
| 5 | E | Motivo Principal | Omisión / Corte / IVA / Ausente / Materialidad / Libro sin Par |
| 6 | F | IDs Referencia | nro_documento o nro_comprobante concatenados con ` \| ` |
| 7 | G | Antigüedad Máxima (días) | max(hoy - fecha_valor) |
| 8 | H | % sobre Error | abs(MI_rut) / abs(diferencia_total) × 100 |
| 9 | I | Plan de Acción | Vacío — editable por responsable de área |

### Lógica de colores hallazgos
- **Fondo Rojo** `#FFC7CE` → % sobre Error > 20%
- **Texto Naranja** `#9C5600` → Antigüedad > 90 días (sin alerta concentración)
- **RUT NO IDENTIFICADO** → bold, aparece primero en el ranking
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
- **Opción A hallazgos (v2.3):** hallazgos incluye Manuales + Sugeridos + Libro sin Par para cuadrar con diferencia de saldo. Decisión del contador: "la cuadratura es intransable".
- **Archivo hallazgos independiente (v2.3):** separado de conciliacion_resultado.xlsx para enviar a responsables de área sin exponer cartola completa.
- **idx_libro en classifier (v2.3):** columna interna que guarda el índice de la fila del libro matcheada. Permite identificar libro sin par por índice (no por comprobante, que tiene duplicados).
- **IDs Referencia concatenados (v2.3f):** Opción A del contador — mantiene visión estratégica por RUT con trazabilidad suficiente para ir al ERP. Separador ` | ` para parseo futuro.
- **MI con signo (v2.3f):** Libro sin Par usa `-monto_libro` para contribuir positivamente a la ecuación de cuadratura.

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

### Salida de `classifier.py` (DataFrame — 25 columnas)
```
Cartola (7):  fecha_operacion_cartola, fecha_valor_cartola, glosa_cartola,
              rut_cartola, monto_cartola, nro_documento_cartola, banco_cartola

Libro (7):    fecha_contable_libro, glosa_libro, rut_libro, monto_libro,
              nro_referencia_libro, nro_comprobante_libro, codigo_tx_libro

Match (11):   tipo_match, certeza, regla_aplicada, diff_monto, diff_dias,
              flag_conciliacion, flag_iva, dias_antiguedad, tramo_antiguedad,
              accion_recomendada, idx_libro   ← NUEVO v2.3

Diagnóstico (solo Manual): motivo, fecha_cercana, monto_cercano,
                            glosa_cercana, diff_monto_cercano
```

---

## Resultados con datos sintéticos (última ejecución 2026-03-09 19:44)

```
Total transacciones : 1.008
Exacto   :  719  (71.3%)
Sugerido :  166  (16.5%)
Manual   :  123  (12.2%)

Saldo cartola  : -779,660,376
Saldo libro    : -700,877,241
Diferencia     :  -78,783,135

Libro sin par  :   99 filas → MI = 25,992,233
Hallazgos      :  184 RUTs
Cuadratura     :  ✅ (-78,783,135)
Tests          :  265 passed, 0 failed
```

---

## Pendiente próxima sesión

1. **[MERGE]** Completar integración a main:
   ```bash
   git checkout main
   git merge feat/hallazgos-v2.3
   git commit -m "merge(main): integrar feat/hallazgos-v2.3"
   git push
   ```
2. **[TESTS]** Escribir tests para `_construir_hallazgos()` — cobertura de las 3 familias de MI y cuadratura.
3. **[SIGUIENTE PRD]** Confirmar con contador si hay nuevos requerimientos post v2.3f.