Context Snapshot — Conciliador Bancario v2
Fecha: 2026-03-05
Stack: Python 3.12 · pandas 2.x · openpyxl 3.x · pytest · Git (ramas por módulo)

conciliador_bancario/
├── config/config.py          # Rutas, columnas v2, tolerancias, flags, certezas
├── utils/
│   ├── logger.py
│   ├── exceptions.py
│   └── rut_utils.py          # NUEVO v2 — normalización y validación RUT chileno
├── ingestion/
│   ├── reader.py             # Actualizado columnas v2
│   └── normalizer.py         # Actualizado — agrega RUT, fecha_valor, glosa
├── conciliation/
│   ├── rules.py              # Actualizado — cap $5.000, mismo_mes(), detectar_iva()
│   ├── matcher.py            # REESCRITO — jerarquía RUT→Monto→Fecha→Referencia
│   └── classifier.py         # Actualizado — antigüedad, tramo, acción recomendada
├── reporting/
│   ├── formatter.py          # Sin cambios v2
│   └── writer.py             # EN PROGRESO — columnas y colores v2
├── tests/                    # TDD — test antes que módulo
└── main.py                   # Pendiente actualización

Excel → reader → normalizer → matcher → classifier → writer → Excel output

Archivos clave

config/config.py — columnas v2, CERTEZA_*, FLAG_*, ANTIGUEDAD_*, TOLERANCIA_MONTO_ABS_MAX
utils/rut_utils.py — normalizar_rut(), _calcular_dv(), ruts_coinciden()
ingestion/normalizer.py — esquema salida cartola: fecha_operacion, fecha_valor, glosa, rut, monto, nro_documento, banco / libro: fecha_contable, glosa, rut, monto, nro_referencia, nro_comprobante, codigo_tx
conciliation/matcher.py — retorna lista de dicts con: idx_cartola, idx_libro, tipo_match, certeza, motivo, flag_conciliacion, flag_iva, regla_aplicada, idx_libro_cercano
conciliation/classifier.py — retorna DataFrame con columnas v2 incluyendo dias_antiguedad, tramo_antiguedad, accion_recomendada
reporting/writer.py — EN PROGRESO


Decisiones tomadas

RUT como llave maestra: ningún candidato del libro es aceptado si el RUT no coincide, sin importar monto o fecha.
Certeza en 3 niveles: Exacto / Sugerido / Manual — reemplaza exacto/parcial/sin_match de v1.
Cap de materialidad $5.000 CLP: tolerancia = min(2% del monto, $5.000) — evita que diferencias de millones pasen el filtro.
Partida en Conciliación: flag independiente de certeza, se activa cuando fecha_valor y fecha_contable pertenecen a meses distintos.
Git por módulo: una rama por módulo (feat/v2-config, feat/v2-rut-utils, etc.) mergeadas a feat/v2-base. main intacto con v1.
TDD estricto en lógica nueva: tests antes del módulo en rut_utils, rules, matcher, classifier. Paralelo en modificaciones sin lógica nueva.
separar_sin_conciliar() filtra por "Manual" — no "sin_match" como en v1.


Estado actual
✅ config/config.py — columnas y constantes v2
✅ utils/rut_utils.py — módulo completo con 22 tests
✅ ingestion/reader.py — columnas v2
✅ ingestion/normalizer.py — RUT, fecha_valor, glosa
✅ conciliation/rules.py — cap $5.000, mismo_mes(), detectar_iva()
✅ conciliation/matcher.py — jerarquía completa, 17 tests
✅ conciliation/classifier.py — antigüedad, tramo, acción recomendada
🔄 EN PROGRESO: reporting/writer.py — 1 test fallando

Tarea en curso
tests/test_writer.py — 19/20 tests pasan. El fallo es:

FAILED TestEscribirSinConciliar::test_solo_contiene_filas_sin_match
assert 2 == 3  →  Partidas sin conciliar: 0

Causa: la fixture df_resultado en test_writer.py usa valores v1 ("exacto", "parcial", "sin_match") pero separar_sin_conciliar() ya filtra por "Manual". El fix requiere dos cambios:

En test_writer.py — fixture: cambiar "sin_match" → "Manual", "exacto" → "Exacto", "parcial" → "Sugerido"
En writer.py — _escribir_resumen(): cambiar conteo a "Exacto", "Sugerido", "Manual"


Próximos pasos

Aplicar fix en test_writer.py y writer.py → correr tests → commit
Actualizar test_writer.py con fixtures y columnas v2 completas (nuevas columnas del classifier)
Merge feat/v2-reporting → feat/v2-base
Actualizar main.py para orquestar flujo v2
Correr main.py con archivos reales y validar métricas
Merge final feat/v2-base → main