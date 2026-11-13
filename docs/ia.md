# Declaracion sobre el Uso de Herramientas de Inteligencia Artificial (IA)

**Asignatura:** Compiladores e Interpretes (Cursada 2026)  
**Trabajos Practicos:** TP N° 1 (Analisis Lexico), TP N° 2 (Analisis Sintactico), TP N° 3 (Representacion Intermedia y Semantica) y TP N° 4 (Generacion de Codigo Assembler)  
**Grupo:** N° 40  
**Integrantes:**  
- Agustin Luciano Espil (agustin20101@gmail.com)  
- Joaquin Fromm (joaquinfromm994@gmail.com)  
- Agustin Domingo Lo Fiego (agustindlofiego@gmail.com)  

---

## Herramientas Utilizadas y Alcance

Durante la resolucion del proyecto integrador se conto con la asistencia de herramientas de Inteligencia Artificial Generativa (**OpenAI Codex**, **ChatGPT** y **Google Gemini**) como apoyo conversacional para la aceleracion del prototipado, el diseño de patrones regulares, la estructuracion del analizador sintactico en Python mediante la libreria SLY 0.5, la generacion de codigo intermedio en Polaca Inversa y la traduccion a Assembler 80x86/80x87 (MASM32).

### Modulos del Proyecto Asistidos:
* **`compiler_frontend/model.py`**: Modelos de datos para tokens, entradas de la Tabla de Simbolos (enriquecidas con `Tipo`, `Uso` y metadatos de ambitos/clases), diagnosticos y nodos del arbol sintactico con orden de finalizacion.
* **`compiler_frontend/lexer.py`**: Formulacion de expresiones regulares en SLY para el reconocimiento de tokens generales y los 12 temas particulares (sufijos `$i`, reales `singlef` con `s`, cadenas multilinea y comentarios `//`), difiriendo el alta de constantes numericas en TS al parser.
* **`compiler_frontend/parser.py`**: Construccion y estratificacion de las producciones gramaticales LALR(1), alta de constantes positivas y negativas en TS, orden de evaluacion con constantes `$i`, asignacion posicional con `:=`, recuperacion en declaraciones/sentencias y diagnosticos contextuales especificos.
* **`compiler_frontend/intermediate.py` (TP3)**: Gestion de ambitos mediante *name mangling* (`:programa:funcion`), chequeos semanticos de declaracion, alcance, aridad, orden de evaluacion (Tema 19), variables `comptime` (Tema 22), visibilidad `import/export` (Tema 26), atributos posicionales (Tema 29), desambiguacion de herencia multiple Opcion 3 (Tema 32) y generacion de **Polaca Inversa** en estructura dinamica.
* **`compiler_frontend/assembler.py` (TP4)**: Verificacion de compatibilidad de tipos sobre la Polaca Inversa (incluyendo conversion explicita `toi` del Tema 34) y traduccion a Assembler Pentium de 32 bits (MASM32) utilizando variables auxiliares (`@auxN`), registros de 16 bits (`AX, BX, DX`), coprocesador `80x87` y los controles en tiempo de ejecucion `a`, `c`, `d` y `g`.
* **`compiler_frontend/__main__.py` e `__init__.py`**: Orquestacion del pipeline completo, formateo de salidas para TP3/TP4 (diagnosticos unificados, Polaca Inversa, Tabla de Simbolos y escritura de `.asm`) y serializacion JSON.
* **`scripts/export_grammar.py`, `tests/test_grammar.py` y `tests/casos_prueba/*.src`**: Scripts auxiliares para la verificacion de estados LALR(1) con 0 conflictos Shift/Reduce y Reduce/Reduce, 43 pruebas unitarias y 24 programas de prueba `.src`.

---

## Prompts Representativos Utilizados

A continuacion se registran los prompts clave utilizados durante las sesiones de asistencia tecnica:

1. **Prompts sobre Analisis Lexico y Correcciones de Devolucion (TP1/TP2):**
   > *"¿Como defino en SLY (Python) una expresion regular para cadenas multilinea delimitadas por comillas dobles `"` que acumule saltos de linea sin cerrar hasta encontrar la comilla final o alcance el fin de archivo (EOF), guardando el valor limpio en la Tabla de Simbolos?"*
   >
   > *"En la devolucion del TP1-2 nos marcaron que si en el codigo esta `-1$i` o `-1.2` pero no `1$i` ni `1.2`, las constantes positivas no deben aparecer en la Tabla de Simbolos. ¿Como desacoplamos la validacion de rango en el lexer respecto del alta en la TS dentro del parser?"*

2. **Prompts sobre Analisis Sintactico, Eliminacion de Conflictos y Recuperacion:**
   > *"Tengo un conflicto Shift/Reduce al intentar permitir asignaciones internas del tipo `a := b = (2$i)`. ¿Como puedo estratificar las producciones de expresiones en BNF para restringir que la asignacion con `=` solo se use entre parentesis sin anidamiento y sin generar conflictos LALR(1) en SLY?"*
   >
   > *"Necesitamos agregar recuperacion en la zona declarativa cuando falta una coma entre variables (`integer a b;`) sincronizando en el `;`, emitir un mensaje especifico cuando se omite el orden obligatorio `[...]` en una invocacion, e informar las estructuras `IF` y `REPEAT` al finalizar su reconocimiento."*

3. **Prompts sobre Semantica, Ambitos y Polaca Inversa (TP3):**
   > *"Implementar el generador de Polaca Inversa en estructura dinamica y los chequeos semanticos del TP3 para el Grupo 40: name mangling de ambitos (`nombre:main:funcion`), atributos Tipo y Uso en la TS, bifurcaciones `BF`/`BI` con backpatching para `IF` y `repeat ... until` (Tema 12), copia de parametros en el orden indicado por `[2$i, 1$i]` (Tema 19) combinada con asignaciones en expresiones (Tema 17), reemplazo de variables `comptime` por su valor constante (Tema 22), visibilidad `import/export` (Tema 26), atributos posicionales (Tema 29) y desambiguado de herencia multiple Opcion 3 (Tema 32)."*

4. **Prompts sobre Chequeo de Tipos y Generacion de Assembler (TP4):**
   > *"A partir de la Polaca Inversa generada en el TP3, implementar la traduccion a Assembler 80x86/80x87 de 32 bits (MASM32) usando una pila de operandos y variables auxiliares `@auxN`. Incorporar el chequeo de compatibilidad de tipos y la conversion explicita `toi` (Tema 34), junto con los 4 controles en tiempo de ejecucion asignados al Grupo 40: a) division por cero entera y flotante, c) overflow en suma de `singlef`, d) overflow en producto de `integer`, y g) perdida de informacion en `toi`."*

---

## Justificacion Tecnica de las Soluciones Adoptadas

Toda propuesta sugerida por las herramientas de IA fue sometida a una revision critica y adaptada minuciosamente a los requerimientos de la catedra:

1. **Estratificacion Gramatical (`plain_*` y `function_*`) y 0 Conflictos LALR(1)**:
   - Las familias `plain_expression`, `plain_term` y `plain_factor` resuelven la prohibicion de anidar asignaciones internas (`=`) a nivel sintactico, mientras que la separacion `global_statements` / `function_statements` restringe `RET` a funciones y metodos con 0 conflictos Shift/Reduce y Reduce/Reduce.

2. **Alta Diferida de Constantes con Signo en la Tabla de Simbolos**:
   - El lexer verifica que la magnitud entera no supere `32768` y que el flotante respete el rango IEEE 754, pero el alta en la Tabla de Simbolos se ejecuta al reducir `number` y `order_items` en el parser. Esto garantiza que `-32768$i` sea aceptado, `+32768$i` sea rechazado con `S_INTEGER_RANGE`, y las constantes negativas no ensucien la TS con entradas positivas inexistentes.

3. **Polaca Inversa con Backpatching y Evaluacion Estatica de `comptime`**:
   - La estructura dinamica `list[RpnStep]` permite resolver en una unica pasada los saltos hacia adelante del `IF` y los saltos hacia atras del `REPEAT ... UNTIL` desapilando los pasos incompletos. Para las variables `comptime` (Tema 22), el generador calcula su valor en compilacion y emite directamente la constante resultante en la Polaca Inversa.

4. **Traduccion por Pila a MASM32 y Controles de Runtime (`a, c, d, g`)**:
   - El traductor recorre la Polaca Inversa validando tipos y emitiendo instrucciones de 16 bits (`AX, BX, DX`, `IMUL` + `JO`, `CMP` + `JE` + `CWD` + `IDIV`) para `INTEGER` e instrucciones del coprocesador `80x87` (`FLD`, `FADD`, `FABS` + `FCOMP`, `FTST`, `FISTP` + `FILD` + `FCOMPP`) para `SINGLEF` y `toi`, garantizando la deteccion exacta de division por cero, overflow y perdida de parte fraccionaria o de rango en tiempo de ejecucion.

---

## Auditoria y Preparacion para la Defensa Oral

El grupo declara que **ninguna solucion generada por IA fue incorporada sin verificacion humana previa**:
* **Verificacion de Pruebas:** Se ejecutaron las 43 pruebas automatizadas (`python -m unittest discover -v`) y los 24 programas de `tests/casos_prueba/` junto con `grupo40.src`, `minimo.src` y `errores.src`.
* **Dominio del Codigo:** Todos los integrantes del grupo comprenden la totalidad de las clases, metodos, producciones gramaticales, generacion de Polaca Inversa y rutinas Assembler desarrolladas, y estan plenamente capacitados para explicar y defender de manera individual y grupal cada decision de diseño implementada en la evaluacion oral.
