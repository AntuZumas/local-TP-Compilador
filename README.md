# Compiladores e Intérpretes — Grupo 40

Compilador completo para los **TP1, TP2, TP3 y TP4** de la cursada 2026. Desarrollado en **Python + SLY 0.5**, integra análisis léxico, análisis sintáctico LALR(1), validaciones semánticas con manejo de ámbitos (*name mangling*), generación de representación intermedia en **Polaca Inversa** y traducción a **Assembler 80x86/80x87 de 32 bits (MASM32)** con controles en tiempo de ejecución.

Las decisiones de diseño del lenguaje están documentadas en [decisiones del prototipo](docs/gramatica/implementacion.md).

## Temas Asignados al Grupo 40

- **TP1 y TP2 (Léxico y Sintáctico):** Temas **3** (`integer`), **7** (`singlef`), **10** (cadenas multilínea `""`), **12** (`repeat ... until`), **15** (comentarios de una línea `//`), **17** (asignaciones de expresiones en expresiones `=`), **19** (invocación con orden obligatorio de parámetros `[...]`), **22** (`comptime`), **26** (`import from` / `export to`), **29** (acceso posicional a atributos `obj[idx]`), **32** (herencia múltiple con desambiguado Opción 3) y **34** (conversión explícita `toi`).
- **TP3 (Representación Intermedia):** **Polaca Inversa** en estructura dinámica y Tabla de Símbolos con atributos `Tipo`, `Uso` y ámbitos mediante *name mangling*.
- **TP4 (Código Destino y Controles de Runtime):** Assembler Pentium 32 bits (MASM32) con variables auxiliares (`@auxN`) y chequeos en tiempo de ejecución **a)** división por cero, **c)** overflow en suma de punto flotante, **d)** overflow en producto de enteros y **g)** pérdida de información en conversión `toi`.

## Preparar y ejecutar

Verificado con Python **3.12+** y SLY **0.5** en Windows y Linux. Desde la raíz del repositorio:

###En Linux / macOS:
```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

### En Windows (PowerShell):
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

### Ejecución del compilador:
```sh
# Salida estándar (TP3/TP4): Diagnósticos, Polaca Inversa, Tabla de Símbolos y generación de .asm
python -m compiler_frontend examples/minimo.src
python -m compiler_frontend examples/grupo40.src
python -m compiler_frontend examples/errores.src

# Opciones adicionales de inspección (TP1/TP2, ruta .asm y exportación JSON)
python -m compiler_frontend examples/grupo40.src --tokens --structures
python -m compiler_frontend examples/grupo40.src --asm examples/grupo40.asm
python -m compiler_frontend examples/grupo40.src --json
```

- Código de salida **0**: análisis léxico, sintáctico y semántico válido (puede incluir warnings); genera el archivo `.asm`.
- **1**: errores léxicos, sintácticos o semánticos detectados; se informan junto con su línea y no se genera código objeto.
- **2**: problema de uso o lectura del archivo fuente.

Por defecto se informan todos los diagnósticos (léxicos, sintácticos y semánticos), la **Polaca Inversa** numerada y la **Tabla de Símbolos**, escribiendo el archivo `.asm` junto al archivo fuente. Los flags `--tokens` y `--structures` permiten habilitar las salidas de los TP1 y TP2. `--json` exporta la estructura completa en formato JSON.

## Pruebas y gramática

```sh
python scripts/export_grammar.py
python scripts/export_grammar.py --check
python -m compiler_frontend --grammar-report
python -m unittest discover -v
```

La gramática LALR(1) construye sus estados **sin conflictos shift/reduce ni reduce/reduce**. La suite automatizada ejecuta **43 pruebas** que incluyen casos unitarios parametrizados y la validación de los **24 programas fuente `.src`** ubicados en `tests/casos_prueba/` (cubriendo casos léxicos, sintácticos, semánticos y de tiempo de ejecución).

La [BNF completa](docs/gramatica/gramatica.bnf) se exporta directamente desde el parser:

```sh
python scripts/export_grammar.py
```

## Recorrido del código

| Archivo | Responsabilidad |
|---|---|
| [lexer.py](compiler_frontend/lexer.py) | Patrones léxicos, ubicaciones, validación de formato/magnitud y registro de cadenas en TS. |
| [parser.py](compiler_frontend/parser.py) | Gramática LALR(1), alta de constantes con signo en TS, recuperación en declaraciones/sentencias y diagnósticos contextuales. |
| [intermediate.py](compiler_frontend/intermediate.py) | TP3: Resolución de ámbitos (*name mangling*), chequeos semánticos (alcance, aridad, orden de evaluación, `comptime`, `import/export`, herencia múltiple Opción 3) y generación de Polaca Inversa. |
| [assembler.py](compiler_frontend/assembler.py) | TP4: Chequeo de compatibilidad de tipos sobre la Polaca Inversa (`toi`) y traducción a Assembler 80x86/80x87 (MASM32) con variables auxiliares y controles de runtime `a, c, d, g`. |
| [model.py](compiler_frontend/model.py) | Tokens con atributos, Tabla de Símbolos enriquecida (`Tipo`, `Uso`, `attrs`), diagnósticos y nodos con orden de finalización. |
| [__init__.py](compiler_frontend/__init__.py) | `analyze(texto)`: pipeline completo por archivo (léxico, sintáctico, semántico, Polaca Inversa y Assembler). |
| [__main__.py](compiler_frontend/__main__.py) | Interfaz por línea de comandos, salida estándar TP3/TP4, generación de archivo `.asm` y salida JSON. |
| [test_grammar.py](tests/test_grammar.py) | 43 pruebas automatizadas (léxicas, sintácticas, semánticas, Polaca Inversa, Assembler, CLI y `tests/casos_prueba/*.src`). |

La notación y las familias de reglas se explican en [la propuesta de gramática](docs/gramatica/propuesta.md).
Los catálogos de [decisiones léxicas](docs/analizador-lexico/decisiones.md) y [decisiones sintácticas](docs/gramatica/decisiones.md) conservan la trazabilidad del diseño.

Material y declaración de uso de IA en [docs](docs/README.md).