# 🏦 Conciliador Bancario

> Sistema automatizado de conciliación bancaria desarrollado en Python.  
> Compara transacciones entre una cartola bancaria y un libro auxiliar contable, detecta diferencias, clasifica resultados y genera tres reportes Excel con formato profesional y cuadratura matemática validada.  
> ⚠️ Todos los datos incluidos en este repositorio son 100% sintéticos.

<div align="center">

![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-2.x-150458?logo=pandas&logoColor=white)
![openpyxl](https://img.shields.io/badge/openpyxl-3.x-217346?logo=microsoftexcel&logoColor=white)
![customtkinter](https://img.shields.io/badge/customtkinter-5.2.2-1F6AA5?logo=python&logoColor=white)
![Tests](https://img.shields.io/badge/Tests-265%20passed-brightgreen?logo=pytest&logoColor=white)
![Conciliación](https://img.shields.io/badge/Conciliaci%C3%B3n%20autom%C3%A1tica-87.8%25-success)
![License](https://img.shields.io/badge/License-MIT-lightgrey)

</div>

---

## 📋 Tabla de contenidos

- [¿Qué problema resuelve?](#-qué-problema-resuelve)
- [Demostración](#-demostración)
- [Arquitectura](#-arquitectura)
- [Algoritmo de matching](#-algoritmo-de-matching)
- [Reportes generados](#-reportes-generados)
- [Instalación](#-instalación)
- [Uso como ejecutable (.exe)](#-uso-como-ejecutable-exe)
- [Tests](#-tests)
- [Configuración](#-configuración)
- [Stack técnico](#-stack-técnico)
- [Autor](#-autor)

---

## ❓ ¿Qué problema resuelve?

La conciliación bancaria manual es un proceso repetitivo, propenso a errores y costoso en tiempo. Este sistema automatiza el proceso completo: desde la lectura de archivos Excel hasta la generación de reportes listos para auditoría, con tolerancias configurables, diagnóstico automático de discrepancias y cuadratura matemática total.

| Métrica | Resultado |
| :--- | ---: |
| Transacciones procesadas | 1.008 |
| Match Exacto | 719 (71.3%) |
| Match Sugerido | 166 (16.5%) |
| Sin Match (Manual) | 123 (12.2%) |
| Tasa de conciliación automática | **87.8%** |
| Diferencia de saldo | -$78.783.135 |
| Cuadratura hallazgos | ✅ exacta |

---

## 🚀 Demostración

**Modo GUI (recomendado):**
```bash
python gui/app.py
```

**Modo consola:**
```bash
python main.py
```

```
INFO | [1/6] Leyendo archivos de entrada...
INFO | [2/6] Normalizando datos...
INFO | [3/6] Ejecutando matching...
INFO | Matching completado → exactos: 719 | sugeridos: 166 | manuales: 123
INFO | [4/6] Clasificando resultados...
INFO | [5/6] Calculando diferencia de saldo...
INFO | Saldo cartola : -779,660,376
INFO | Saldo libro   : -700,877,241
INFO | Diferencia    :  -78,783,135
INFO | [6/6] Escribiendo archivos de salida...
INFO | Libro sin par: 99 filas → MI = 25,992,233
INFO | Hallazgos cuadra con diferencia de saldo ✅ (-78,783,135)
INFO |   Proceso completado exitosamente
```

---

## 🏗️ Arquitectura

El proyecto sigue el principio de **separación de responsabilidades**: cada módulo tiene una única función y puede modificarse sin afectar al resto.

```
conciliador_bancario/
│
├── config/
│   └── config.py              # Rutas, columnas y tolerancias configurables
│
├── utils/
│   ├── logger.py              # Logging dual: consola + archivo
│   ├── exceptions.py          # Jerarquía de excepciones propias
│   └── rut_utils.py           # Validación y normalización de RUT chileno
│
├── ingestion/
│   ├── reader.py              # Lectura y validación de Excel
│   └── normalizer.py          # Limpieza y estandarización de datos
│
├── conciliation/
│   ├── rules.py               # Reglas de tolerancia (±2% monto, ±5 días)
│   ├── matcher.py             # Algoritmo de matching v2.2 — O(n) índice por RUT
│   └── classifier.py          # Ensamblado del resultado final + idx_libro
│
├── reporting/
│   ├── formatter.py           # Estilos y colores openpyxl
│   └── writer.py              # 3 archivos Excel — output_dir configurable
│
├── gui/
│   ├── __init__.py
│   └── app.py                 # GUI customtkinter — dark mode, threading, progreso
│
├── tests/                     # 265 tests con pytest (TDD)
├── main.py                    # Orquestador — modo consola y GUI
├── conciliador_bancario.spec  # PyInstaller — build .exe
└── build.bat                  # Script de build Windows
```

---

## 🔍 Algoritmo de matching

Para cada transacción de la cartola busca en el libro en orden de prioridad:

```
Jerarquía: RUT → Monto → Fecha → Referencia

1. Exacto   → RUT + monto ±2% + fecha ±5 días + referencia (6+ chars)
2. Sugerido → RUT + monto ±2% + fecha ±5 días (o diferencia por IVA ×1.19)
3. Manual   → sin par — diagnóstico automático del motivo
```

Cada transacción del libro solo puede usarse una vez, evitando matches duplicados. El índice por RUT reduce la complejidad de O(n²) a O(n).

**Diagnóstico automático de partidas sin conciliar:**

| Motivo | Significado |
| :--- | :--- |
| Fecha coincide pero monto no encontrado | Movimiento en esa fecha pero monto muy distinto |
| Monto coincide pero fecha fuera de rango | Transacción existe pero desfase > 5 días |
| Posible Neto vs Bruto (×1.19) | Diferencia exacta de IVA — match Sugerido |
| Transacción ausente en libro auxiliar | No existe ningún registro similar |

---

## 📊 Reportes generados

### 1. `conciliacion_resultado.xlsx`
Todas las transacciones con su match. Columnas: datos de cartola, datos del libro matcheado, tipo de match, certeza, diferencias, flags y antigüedad.

### 2. `partidas_sin_conciliar.xlsx`
Las 123 transacciones sin par en el libro, con diagnóstico del motivo y monto más cercano encontrado.

### 3. `hallazgos_criticos_auditoria.xlsx`
Ranking por RUT con cuadratura matemática total. Incluye tres familias de impacto:

| Familia | MI | ID de trazabilidad |
| :--- | :--- | :--- |
| Manual | `monto_cartola` | `nro_documento` |
| Sugerido | `monto_cartola - monto_libro` | `nro_documento` |
| Libro sin Par | `-monto_libro` | `nro_comprobante` |

`sum(MI) == saldo_cartola - saldo_libro` ✅

**Lógica de colores:**
- 🔴 Fondo rojo `#FFC7CE` → RUT concentra más del 20% del error total
- 🟠 Texto naranja `#9C5600` → Antigüedad mayor a 90 días
- **Bold** → RUT NO IDENTIFICADO (prioridad máxima)

---

## ⚙️ Instalación

```bash
# 1. Clonar el repositorio
git clone https://github.com/gaboneumann/conciliador-bancario.git
cd conciliador-bancario

# 2. Crear entorno virtual
python -m venv .venv
source .venv/bin/activate        # macOS / Linux
.venv\Scripts\activate           # Windows

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Ejecutar GUI
python gui/app.py

# 5. O ejecutar en modo consola con datos sintéticos
# (agregar tus propios archivos a data/input/ primero)
python main.py
```

---

## 🖥️ Uso como ejecutable (.exe)

El proyecto incluye configuración para generar un ejecutable Windows que no requiere Python instalado.

**Generar el .exe:**
```bash
.\build.bat
```

El ejecutable se genera en `dist\ConciliadorBancario.exe`.

**Uso:** doble clic en el `.exe`, seleccionar los dos archivos Excel de entrada y la carpeta de destino, y ejecutar. Los 3 reportes se generan en la carpeta elegida.

---

## 🧪 Tests

El proyecto fue desarrollado con **TDD (Test-Driven Development)**. Los tests se escriben antes que el código de producción.

```bash
# Suite completa
pytest tests/ -v

# Con reporte de cobertura
pytest tests/ --cov=. --cov-report=term-missing
```

```
265 passed in 10.44s
```

---

## 🔧 Configuración

Todas las tolerancias son configurables en `config/config.py`:

```python
TOLERANCIA_MONTO_PCT     = 0.02    # ±2% de diferencia en monto
TOLERANCIA_MONTO_ABS_MAX = 5_000   # cap absoluto en CLP
TOLERANCIA_DIAS          = 5       # ±5 días de diferencia en fecha
TOLERANCIA_REFERENCIA    = 6       # primeros 6 caracteres de referencia
FACTOR_IVA               = 1.19    # ratio para detección neto vs bruto
```

---

## 🛠️ Stack técnico

| Tecnología | Versión | Uso |
| :--- | :---: | :--- |
| Python | 3.12 | Lenguaje principal |
| pandas | 2.x | Manipulación y transformación de datos |
| openpyxl | 3.x | Lectura y escritura de Excel con formato |
| customtkinter | 5.2.2 | GUI dark mode |
| pytest | latest | Suite de 265 tests con TDD |
| PyInstaller | 6.19.0 | Empaquetado a .exe Windows |
| unicodedata / re | stdlib | Normalización de texto y RUT |
| logging | stdlib | Trazabilidad dual consola + archivo |

---

## 👤 Autor

**Gabriel Neumann**  
[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-0A66C2?logo=linkedin&logoColor=white)](https://www.linkedin.com/in/gaboneumann/)
[![GitHub](https://img.shields.io/badge/GitHub-Follow-181717?logo=github&logoColor=white)](https://github.com/gaboneumann)

---

## 📄 Licencia

Distribuido bajo licencia MIT. Ver [`LICENSE`](LICENSE) para más información.