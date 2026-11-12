# Compiladores e Intérpretes — Grupo 40

Prototipo ejecutable de la gramática para TP1/TP2 de 2026. Usa **Python + SLY
0.5** y permite inspeccionar tokens, tabla de símbolos, estructuras reconocidas,
árbol sintáctico y diagnósticos. No ejecuta los programas ni genera código máquina.

Es una propuesta de implementación para discutir. Las interpretaciones adoptadas
ante ambigüedades están en [decisiones del prototipo](docs/gramatica/implementacion.md).
La aceptación de un archivo sólo indica validez léxica/sintáctica bajo esas decisiones,
no corrección semántica ni aprobación de la cátedra.

## Preparar y ejecutar

Verificado con Python **3.12.14** y SLY **0.5**. Desde la raíz del repositorio:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt

python -m compiler_frontend examples/minimo.src --tokens
python -m compiler_frontend examples/grupo40.src
python -m compiler_frontend examples/grupo40.src --json
python -m compiler_frontend examples/errores.src
```

En Windows, activar con `.venv\Scripts\Activate.ps1` en PowerShell, o ejecutar
directamente `.venv\Scripts\python.exe`. No se verificó este prototipo en Windows.

- Código de salida **0**: análisis aceptado (puede incluir warnings).
- **1**: errores léxicos/sintácticos; el procesamiento intenta continuar.
- **2**: problema de uso o lectura del archivo.

`--json` incluye el árbol completo, los tokens y la TS. `--tokens` agrega el
listado legible de tokens/TS. Sin esas opciones se muestran estructuras y
diagnósticos. La ruta fuente es argumento; no hace falta modificar código.

## Pruebas y gramática

```sh
python -m unittest discover -v
python -m compiler_frontend --grammar-report
python scripts/export_grammar.py --check
```

El reporte se calcula con SLY al cargar las reglas. La versión inicial construye
**256 estados sin conflictos shift/reduce ni reduce/reduce**. Las 30 pruebas
incluyen casos parametrizados válidos e inválidos y pruebas de consola.

La [BNF completa](docs/gramatica/gramatica.bnf) se exporta del parser:

```sh
python scripts/export_grammar.py
```

## Recorrido del código

| Archivo | Responsabilidad |
|---|---|
| [lexer.py](compiler_frontend/lexer.py) | Patrones, ubicaciones, reglas léxicas de apoyo y registro en TS. |
| [parser.py](compiler_frontend/parser.py) | Producciones y acciones que construyen el árbol; control de signo INTEGER. |
| [model.py](compiler_frontend/model.py) | Tokens con atributos, TS, diagnósticos y nodos. |
| [__init__.py](compiler_frontend/__init__.py) | `analyze(texto)`: análisis independiente por archivo. |
| [__main__.py](compiler_frontend/__main__.py) | Interfaz por consola y salida JSON. |
| [test_grammar.py](tests/test_grammar.py) | Casos sobre sintaxis, restricciones, datos y recuperación. |

La notación y las familias de reglas se explican en
[la propuesta de gramática](docs/gramatica/propuesta.md).
Los catálogos previos de [decisiones léxicas](docs/analizador-lexico/decisiones.md)
y [decisiones sintácticas](docs/gramatica/decisiones.md) conservan las alternativas
para la discusión del equipo.

## Límites actuales

- El léxico SLY permite probar la gramática; queda confirmar la alternativa de
  expresiones regulares frente a matrices exigidas por la consigna.
- Los temas de TP3/TP4 no se implementan semánticamente: tipos, ámbitos, aridad,
  orden de evaluación, visibilidad, herencia y ejecución de COMPTIME/TOI.
- La recuperación sincroniza sentencias con `;`. Un error estructural en una
  cabecera o cierre puede impedir recuperar el árbol completo. Los mensajes
  sintácticos son genéricos, no un catálogo final de errores específicos.
- SLY fue retirado por su autor; se fija la dependencia para hacer reproducible
  el prototipo. [Aviso oficial](https://github.com/dabeaz/sly).

Material y trazabilidad de IA en [docs](docs/README.md).
