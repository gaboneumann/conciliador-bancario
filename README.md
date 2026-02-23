# 🏦 Conciliador Bancario

> Sistema automatizado de conciliación bancaria desarrollado en Python.  
> Compara transacciones entre una cartola personal y un libro del banco, detecta diferencias, clasifica resultados y genera reportes Excel con formato profesional.  
>⚠️ Todos los datos incluidos en este repositorio son 100% sintéticos.

<div align="center">

![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-2.x-150458?logo=pandas&logoColor=white)
![openpyxl](https://img.shields.io/badge/openpyxl-3.x-217346?logo=microsoftexcel&logoColor=white)
![Tests](https://img.shields.io/badge/Tests-231%20passed-brightgreen?logo=pytest&logoColor=white)
![Conciliación](https://img.shields.io/badge/Conciliaci%C3%B3n%20autom%C3%A1tica-94.2%25-success)
![License](https://img.shields.io/badge/License-MIT-lightgrey)

</div>

---

## 📋 Tabla de contenidos

- [¿Qué problema resuelve?](#-qué-problema-resuelve)
- [Demostración](#-demostración)
- [Arquitectura](#-arquitectura)
- [Algoritmo de matching](#-algoritmo-de-matching)
- [Instalación](#-instalación)
- [Tests](#-tests)
- [Configuración](#-configuración)
- [Stack técnico](#-stack-técnico)
- [Autor](#-autor)

---

## ❓ ¿Qué problema resuelve?

La conciliación bancaria manual es un proceso repetitivo, propenso a errores y costoso en tiempo. Este sistema automatiza el proceso completo: desde la lectura de archivos Excel hasta la generación de reportes listos para auditoría, con tolerancias configurables y diagnóstico automático de discrepancias.

**Resultado en producción: 94.2% de conciliación automática sobre 996 transacciones sintéticas, reduciendo el tiempo de análisis de horas a segundos. Los datos de entrada incluidos en el repositorio (data/input/) fueron generados con un script que crea datos sintéticos — no contienen información bancaria real.

| Métrica                         | Resultado   |
| :------------------------------ | ----------: |
| Transacciones procesadas        | 996         |
| Matches exactos                 | 937         |
| Matches parciales               | 1           |
| Sin match                       | 58          |
| Tasa de conciliación automática | **94.2%**   |

---

## 🚀 Demostración

```bash
python main.py
```

```
INFO | [1/6] Leyendo archivos de entrada...
INFO | [2/6] Normalizando datos...
INFO | [3/6] Ejecutando matching...
INFO | Matching completado → exactos: 937 | parciales: 1 | sin match: 58
INFO | [4/6] Clasificando resultados...
INFO | [5/6] Calculando diferencia de saldo...
INFO | [6/6] Escribiendo archivos de salida...
INFO |   Proceso completado exitosamente
```

**Outputs generados:**

| Archivo                        | Contenido                                                             |
| :----------------------------- | :-------------------------------------------------------------------- |
| `conciliacion_resultado.xlsx`  | Todas las transacciones con su match, diferencias y tipo de resultado |
| `partidas_sin_conciliar.xlsx`  | Transacciones sin match con diagnóstico del motivo                    |

---

## 🏗️ Arquitectura

El proyecto sigue el principio de **separación de responsabilidades**: cada módulo tiene una única función y puede modificarse sin afectar al resto.

```
conciliador_bancario/
│
├── config/
│   └── config.py               # Rutas, columnas y tolerancias configurables
│
├── utils/
│   ├── logger.py               # Logging dual: consola + archivo
│   └── exceptions.py           # Jerarquía de excepciones propias
│
├── ingestion/
│   ├── reader.py               # Lectura y validación de Excel
│   └── normalizer.py           # Limpieza y estandarización de datos
│
├── conciliation/
│   ├── rules.py                # Reglas de tolerancia (±2% monto, ±3 días)
│   ├── matcher.py              # Algoritmo de matching con diagnóstico
│   └── classifier.py           # Ensamblado del resultado final
│
├── reporting/
│   ├── formatter.py            # Estilos y colores openpyxl
│   └── writer.py               # Escritura de Excel con encabezados agrupados
│
├── data/
│   ├── input/                  # Archivos de entrada 
│   │   ├── cartola_personal.xlsx                # Datos sintéticos
│   │   └── libro_banco.xlsx                     # Datos sintéticos    
│   ├── output/                 # Reportes generados          
│   └── ├── conciliacion_resultado.xlsx
│       └── partidas_sin_conciliar.xlsx
│   
│
├── tests/                      # 231 tests con pytest (TDD)
├── main.py                     # Orquestador del flujo completo
└── README.md
```

---

## 🔍 Algoritmo de matching

Para cada transacción de la cartola busca en el libro en orden de prioridad:

```
1. Match exacto  → monto ±2% + fecha ±3 días + referencia (4+ chars)
2. Match parcial → monto ±2% + fecha ±3 días
3. Sin match     → diagnóstico automático del motivo
```

Cada transacción del libro solo puede usarse una vez, evitando matches duplicados.

**Diagnóstico automático de partidas sin conciliar:**

| Motivo                                   | Significado                                                               |
| :--------------------------------------- | :------------------------------------------------------------------------ |
| Monto coincide pero fecha fuera de rango | La transacción existe pero fue registrada con más de 3 días de diferencia |
| Fecha coincide pero monto no encontrado  | Hay movimiento en esa fecha pero por un monto muy distinto                |
| Transacción ausente en libro             | No existe ningún registro similar en el libro del banco                   |

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

# 4. (Opcional) Dependencias de desarrollo
pip install -r requirements-dev.txt
```

**Colocar los archivos de entrada en:**

```
data/input/cartola_personal.xlsx
data/input/libro_banco.xlsx
```

> ℹ️ Puedes usar los archivos en `data/input/cartola_personal.xlsx` y 'data/input/libro_banco.xlsx' para probar el sistema sin datos reales. Fueron generados con script externo — ejecútalo para crear nuevos conjuntos con distintos volúmenes o parámetros.

**Ejecutar:**

```bash
python main.py
```

---

## 🧪 Tests

El proyecto fue desarrollado con **TDD (Test-Driven Development)**: los tests se escriben antes que el código de producción, garantizando cobertura desde el inicio.

```bash
# Correr suite completa
pytest tests/ -v

# Con reporte de cobertura
pytest tests/ --cov=. --cov-report=term-missing
```

```
231 passed in X.XXs
```

---

## 🔧 Configuración

Todas las tolerancias son configurables en `config/config.py`:

```python
TOLERANCIA_MONTO_PCT  = 0.02   # ±2% de diferencia en monto
TOLERANCIA_DIAS       = 3      # ±3 días de diferencia en fecha
TOLERANCIA_REFERENCIA = 4      # primeros 4 caracteres de referencia
```

---

## 🛠️ Stack técnico

| Tecnología       | Versión | Uso                                      |
| :--------------- | :-----: | :--------------------------------------- |
| Python           | 3.12    | Lenguaje principal                       |
| pandas           | 2.x     | Manipulación y transformación de datos   |
| openpyxl         | 3.x     | Lectura y escritura de Excel con formato |
| pytest           | latest  | Suite de 231 tests con TDD               |
| unicodedata / re | stdlib  | Normalización de texto y referencias     |
| logging          | stdlib  | Trazabilidad dual consola + archivo      |

---

## 👤 Autor

**Gabriel Neumann**  
[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-0A66C2?logo=linkedin&logoColor=white)](https://www.linkedin.com/in/gaboneumann/)
[![GitHub](https://img.shields.io/badge/GitHub-Follow-181717?logo=github&logoColor=white)](https://github.com/gaboneumann)

---

## 📄 Licencia

Distribuido bajo licencia MIT. Ver [`LICENSE`](LICENSE) para más información.