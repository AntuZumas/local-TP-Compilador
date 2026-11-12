# Declaracion sobre el Uso de Herramientas de Inteligencia Artificial (IA)

**Asignatura:** Compiladores e Interpretes (Cursada 2026)  
**Trabajos Practicos:** TP N° 1 (Analisis Lexico) y TP N° 2 (Analisis Sintactico)  
**Grupo:** N° 40  
**Integrantes:**  
- Agustin Luciano Espil (agustin20101@gmail.com)  
- Joaquin Fromm (joaquinfromm994@gmail.com)  
- Agustin Domingo Lo Fiego (agustindlofiego@gmail.com)  

---

## Herramientas Utilizadas y Alcance

Durante la resolucion del proyecto integrador se conto con la asistencia de herramientas de Inteligencia Artificial Generativa (**OpenAI Codex**, **ChatGPT** y **Gemini Notebook**) como apoyo conversacional para la aceleracion del prototipado, el diseño de patrones regulares y la estructuracion del analizador sintactico en Python mediante la libreria SLY 0.5.

### Modulos del Proyecto Asistidos:
* **`compiler_frontend/model.py`**: Modelos de datos para tokens, entradas de la Tabla de Simbolos, diagnosticos y nodos del arbol sintactico abstracto (AST).
* **`compiler_frontend/lexer.py`**: Formulacion de expresiones regulares en SLY para el reconocimiento de tokens generales y los 12 temas particulares (ej. sufijos `$i`, reales `singlef` con `s`, cadenas multilinea y comentarios `//`).
* **`compiler_frontend/parser.py`**: Construccion y estratificacion de las producciones gramaticales LALR(1), resolucion de ambigüedades y diseño de reglas de resincronizacion de errores sintacticos.
* **`compiler_frontend/__main__.py` e `__init__.py`**: Orquestacion del analizador CLI, formateo de salidas por consola (tokens, diagnostico, tabla de simbolos y estructuras) y serializacion JSON.
* **`scripts/export_grammar.py` y `tests/test_grammar.py`**: Scripts auxiliares para la verificacion de los 256 estados LALR(1), la certificacion de 0 conflictos Shift/Reduce y Reduce/Reduce, y la suite de pruebas unitarias.

---

## Prompts Representativos Utilizados

A continuacion se registran los prompts clave utilizados durante las sesiones de asistencia tecnica:

1. **Prompts sobre Analisis Lexico:**
   > *"¿Como defino en SLY (Python) una expresion regular para cadenas multilinea delimitadas por comillas dobles `"` que acumule saltos de linea sin cerrar hasta encontrar la comilla final o alcance el fin de archivo (EOF), guardando el valor limpio en la Tabla de Simbolos?"*
   >
   > *"Necesito validar constantes enteras con el sufijo `$i` para 16 bits. ¿Como puedo gestionar el rango entre -32768 y 32767 dividiendo la responsabilidad entre el lexico y el sintactico cuando hay un signo menos unario?"*

2. **Prompts sobre Analisis Sintactico y Eliminacion de Conflictos:**
   > *"Tengo un conflicto Shift/Reduce al intentar permitir asignaciones internas del tipo `a := b = (2$i)`. ¿Como puedo estratificar las producciones de expresiones en BNF para restringir que la asignacion con `=` solo se use entre parentesis sin anidamiento y sin generar conflictos LALR(1) en SLY?"*
   >
   > *"¿Como puedo estructurar la gramatica para garantizar sintacticamente que la sentencia `RET` solo sea permitida dentro del cuerpo de funciones (`function_statements`) y se rechace si aparece en el bloque principal (`global_statements`)?"*

3. **Prompts sobre Recuperacion de Errores y Diagnostico:**
   > *"¿Cual es la estrategia recomendada en SLY para resincronizar el parser tras un error sintactico usando el token `error` delimitado por punto y coma `;`, garantizando que se consuma el token defectuoso y la compilacion continue en la siguiente instruccion?"*

---

## Justificacion Tecnica de las Soluciones Adoptadas

Toda propuesta sugerida por las herramientas de IA fue sometida a una revision critica y adaptada minuciosamente a los requerimientos de la catedra:

1. **Estratificacion Gramatical (`plain_*` y `function_*`)**:
   - Para evitar anidamientos de asignaciones internas (`=`) se crearon las familias de producciones `plain_expression`, `plain_term` y `plain_factor`. Esta solucion tecnica fue adoptada porque resuelve la restriccion del Tema 17 directamente a nivel sintactico, eliminando la necesidad de validaciones semanticas complejas en fases posteriores.
   - La separacion entre `global_statements` y `function_statements` garantiza en tiempo de parsing que la instruccion de retorno `RET` pertenezca exclusivamente a un ambito subrutinario.

2. **Gestion Coordinada de Rangos Numericos de 16 Bits**:
   - En lugar de saturar el lexico con la deteccion de signos unarios, se acordo que el lexer acepte magnitudes absolutas de hasta 32768, delegando al parser la inspeccion del prefijo `-`. Esto permite aceptar el valor de frontera `-32768` y rechazar `+32768` emitiendo el diagnostico `S_INTEGER_RANGE`.

3. **Garantia de Cero Conflictos LALR(1)**:
   - Se valido que la gramatica final generada en `parser.py` produzca **256 estados LALR(1) con 0 conflictos Shift/Reduce y 0 conflictos Reduce/Reduce**, verificado mediante la ejecucion del script `export_grammar.py`.

---

## Auditoria y Preparacion para la Defensa Oral

El grupo declara que **ninguna solucion generada por IA fue incorporada sin verificacion humana previa**:
* **Verificacion de Pruebas:** Se ejecutaron los casos de prueba `grupo40.src`, `errores.src` y `minimo.src` en distintos entornos para validar la precision del analizador y la recuperacion ante errores.
* **Dominio del Codigo:** Todos los integrantes del grupo comprenden la totalidad de las clases, metodos y producciones gramaticales desarrolladas, y estan plenamente capacitados para explicar y defender de manera individual y grupal cada decision de diseño implementada en la evaluacion oral.