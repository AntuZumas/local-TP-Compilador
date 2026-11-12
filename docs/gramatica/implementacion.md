# Decisiones adoptadas para el prototipo ejecutable

Fecha: 14/09/2026. El usuario pidió implementar con la información disponible,
documentar las decisiones y publicar para revisión. Estas opciones están
**implementadas provisionalmente**: no se presentan como respuestas confirmadas
por la cátedra ni como consenso previo del grupo.

Código de referencia: [parser.py](../../compiler_frontend/parser.py),
[lexer.py](../../compiler_frontend/lexer.py). Las alternativas originales siguen
en [decisiones.md](decisiones.md) y [léxico](../analizador-lexico/decisiones.md).

## 1. Plataforma y alcance

- Python 3.12.14, SLY 0.5 fijado en `requirements.txt`, `.venv` local y pip.
- Parser LALR(1), con producciones explícitas y acciones Python.
- Léxico SLY de apoyo para ejecutar archivos completos. Su elección corresponde
  al prototipo y no resuelve la consulta sobre matrices del TP1.
- Flujo batch: se materializa la tira de tokens para poder mostrarla junto con
  el árbol y la TS; el parser consume un iterador de esa tira.
- Árbol sintáctico de inspección con nodos nombrados, terminales y posiciones.
  No se construye todavía una representación intermedia ejecutable.
- Gramática generada: 256 estados, sin conflictos shift/reduce ni reduce/reduce.
  La evidencia se obtiene con `python -m compiler_frontend --grammar-report`.

## 2. Interpretaciones sintácticas

| Decisiones previas | Opción implementada | Qué conviene confirmar |
|---|---|---|
| G01–G03 | Programa `ID declaraciones BEGIN sentencias END` sin `;` después del END final. Declaraciones pueden faltar; cuerpos ejecutables y clases no vacíos. Sentencias simples terminan en `;`; bloques BEGIN/END no agregan otro. | Vacíos y terminador de programa. |
| G04–G06 | Variables INTEGER/SINGLEF, objetos por nombre de clase y COMPTIME sólo para tipos básicos. Declaraciones en programa/funciones/métodos; se permiten clases en esas zonas declarativas. Los miembros de clase son atributos básicos, métodos y EXTENDS. | Clases locales y COMPTIME de objetos/atributos. |
| G07–G09 | `*`/`/` antes de `+`/`-`, asociatividad izquierda. Sin paréntesis libres de agrupación. Menos unario sólo ante constantes. | Si la cátedra permite agrupación simple o negación de variables. |
| G10–G11 | `ID := expresion;` exterior. `ID = (plain_expression)` interior. Escritura de atributo `obj[indice] = expresion;`. Destino interno sólo ID. | Operadores admitidos para atributos y destinos internos. |
| G12 | Ninguna asignación interna puede contener otra, tampoco dentro de llamadas o conversiones que estén en su lado derecho. Dos asignaciones al mismo nivel sí se admiten. | Alcance transitivo de «sin anidamiento». |
| G13–G15 | Una comparación por condición; IF/ELSE/END_IF, REPEAT/UNTIL y TOI como factor. Bloques simples o compuestos. | Sin ampliaciones de AND/OR ni comparaciones encadenadas. |
| G16–G18 | Funciones anidadas con FUNCTION y métodos sin FUNCTION. Al menos un formal. Tipos de parámetros básicos o nombres de clase en ambos. Cero o más RET, sólo dentro de función/método, propagando permiso en IF/REPEAT. | Parámetros de clase en funciones además de métodos. |
| G19–G22 | Orden obligatorio en funciones y métodos. Índices de orden sin sufijo, como `[2,1]`. Al menos un argumento e índice. Llamadas a función o método también pueden ser sentencias independientes. | Aplicación del orden a métodos, sufijos y llamadas independientes. |
| G23–G26 | BEGIN obligatorio en clases. IMPORT FROM en cabecera sin `;`. EXPORT de atributo antes de su `;`; EXPORT de método después de `END;`, con su propio `;`. | Resolver ejemplos contradictorios del tema 26. |
| G27–G30 | Atributos sólo por posición; índice ID o constante con signo permitido. Tipos/rango del índice se difieren. Métodos con punto. `extends` como palabra reservada; sin prefijos de desambiguación del tema 31. | Grafía extends/extend y controles semánticos de índices. |

Ejemplos que distinguen decisiones:

```text
a := f(b=(2$i), c)[2,1];              // Admitido.
a := b=(f(c)[1]+toi(1.5));            // Admitido, sin asignación dentro de llamada.
a := b=(f(c=(1$i))[1]);               // Rechazado: asignación interna anidada.
a := f(b,c);                         // Rechazado: falta orden.
a := f(b,c)[2$i,1$i];                 // Rechazado: orden usa números sin sufijo.
obj[0$i] = a;                        // Admitido.
obj[0$i] := a;                       // Rechazado bajo la decisión provisional.
```

Los índices del orden no se verifican como permutación ni contra la cantidad de
argumentos. Por ejemplo, `f(a)[0,0,999]` tiene forma aceptada por este prototipo;
su significado deberá validarse cuando se especifiquen las reglas semánticas.
Lo mismo sucede con índices de atributo de tipo flotante o negativos: la gramática
admite «constante» y no decide si ese acceso tiene sentido.

## 3. Por qué hay familias de reglas duplicadas

### Contexto de RET

`global_statement` no incluye retorno. `function_statement` sí lo incluye y
propaga esa capacidad mediante `function_block`, `function_if` y
`function_repeat`. La restricción se comprueba en el parser y no mediante un
contador externo que inspecciona el árbol al final.

### Asignaciones internas

`expression` permite `inline_assignment`. Su lado derecho requiere
`plain_expression`, cuyos factores no incluyen asignación interna. La familia
`plain_*` se extiende a argumentos, invocaciones y conversiones: no se puede
reintroducir una asignación anidada indirectamente con `f(...)` o `toi(...)`.

### Precedencia

`expression` y `term` son niveles separados y recursivos a izquierda. No se usan
declaraciones de precedencia para ocultar conflictos; los tests inspeccionan la
agrupación real de suma/multiplicación y de resta/división repetidas.

## 4. Reglas léxicas de apoyo adoptadas

| Área | Decisión |
|---|---|
| Entrada | UTF-8; BOM inicial tolerado; CRLF/CR normalizados a LF. Líneas/columnas desde 1; tab cuenta un carácter. |
| Identificadores | ASCII minúsculo, primer carácter letra, resto letras/dígitos/`_`. Se consume el nombre completo, se trunca a 22 y se emite warning. |
| Reservadas | Insensibles a mayúsculas/minúsculas; TPR separada. No se convierten identificadores inválidos a minúsculas. |
| Constantes | Tokens INT y FLOAT separados. El patrón numérico captura también candidatos con sufijos/exponentes inválidos para diagnosticarlos completos. |
| INTEGER | Magnitud léxica 0…32768; el parser admite −32768 y rechaza +32768. Una magnitud mayor se rechaza en AL. |
| SINGLEF | Validación con Decimal usando literalmente los intervalos abiertos de TP1 p. 3; cero permitido. Sin redondeo IEEE-754 ni aceptación de subnormales fuera del intervalo. |
| Orden | Token ORDER_INDEX para dígitos sin sufijo, aceptado sintácticamente sólo en la lista de orden. No habilita enteros sin sufijo en otras expresiones. |
| Cadenas | Comillas dobles, multilinea, vacías admitidas, sin escapes especiales. Se quitan saltos del valor y se preservan espacios; ubicación en la apertura. |
| Comentarios | `//` hasta salto o EOF; no se interpreta dentro de una cadena. |
| TS | Registro por categoría/tipo/texto efectivo. No normaliza constantes equivalentes como `1.0` y `1.00`; sí reutiliza identificadores truncados y contenido de cadenas. |
| Signo y TS | Una constante negativa usa una entrada firmada distinta. No muta la entrada de magnitud compartida por otros tokens. La tira léxica conserva el menos separado. |
| Estado | Nueva TS, lexer, parser y diagnósticos por cada llamada a `analyze`. |

Las entradas de magnitud pueden permanecer en la TS después del reconocimiento
de una constante negativa: mantienen válidas las referencias del listado léxico.
El nodo sintáctico contiene la referencia firmada. La TS todavía no liga usos a
declaraciones por ámbito ni mantiene valores de ejecución de variables.

## 5. Recuperación y diagnóstico

- Carácter inválido: diagnóstico y avance de un carácter.
- Candidato numérico inválido o fuera de rango: diagnóstico y descarte del candidato.
- Cadena sin cerrar: diagnóstico en la apertura; consume hasta EOF.
- Sintaxis: SLY utiliza `error ';'` para sincronizar sentencias. Se conserva el
  estado previo que acepte ese símbolo y se descarta hasta el delimitador.
- Se registran errores incluso si se logra construir un árbol recuperado.
  `Analysis.ok` sólo es verdadero si hay árbol y no existen diagnósticos de error.
- Los warnings de truncamiento no convierten por sí solos el análisis en fallo.

La recuperación no está completa para todas las cabeceras/cierres. Un error allí
puede consumir parte de la estructura y dejar `tree = null`; no se garantiza
encontrar todos los errores del archivo. Falta un catálogo de mensajes específicos
(«falta paréntesis», «falta END_IF», etc.) y recuperación por contexto más precisa.

## 6. Evidencia y límites

Comandos ejecutados:

```sh
python -m unittest discover -v
python -m compiler_frontend --grammar-report
python scripts/export_grammar.py --check
```

La suite inicial tiene 30 pruebas con subcasos: precedencia, todos los temas,
restricciones, rangos, posiciones, referencias TS, recuperación de dos errores,
entradas grandes y CLI con códigos de salida/JSON. El ejemplo `grupo40.src` permite
recorrer el conjunto de construcciones; `errores.src` conserva dos POUT posteriores
a dos errores distintos.

El éxito no demuestra semántica correcta. Tampoco resuelve interpretaciones de
la consigna ni reemplaza la defensa del código. La versión de Python verificada
es 3.12.14 en macOS; falta probar instalación/ejecución en las otras computadoras.
