# Gramática: decisiones y preguntas para el diseño

Grupo 40 — 14/09/2026. Complementa las
[decisiones del léxico](../analizador-lexico/decisiones.md). Las fuentes se detallan
al final de este documento. Todas las elecciones de esta tabla están pendientes
de ratificación; las obligaciones expresas se identifican como requisitos.

## Estado de implementación

Ya existe un prototipo ejecutable con las opciones adoptadas en
[implementacion.md](implementacion.md). El catálogo de abajo conserva las
alternativas iniciales; «pendiente» se refiere a ratificación del grupo/cátedra,
no a ausencia de código. Ver [propuesta.md](propuesta.md) para leer la gramática.

## 1. Qué estamos decidiendo

La cátedra ya especificó el lenguaje. Tenemos que formalizarlo, combinar las
reglas generales con los temas asignados y aclarar ejemplos contradictorios.
El prototipo implementa esas construcciones, funciones, métodos, clases y
asignaciones internas bajo decisiones provisionales registradas por separado.

La gramática implementada se generó con 256 estados y sin conflictos LALR(1).
Las interpretaciones pendientes y la recuperación limitada impiden tratar el
prototipo como entrega final validada por la cátedra.

## 2. Programa, bloques y declaraciones

| ID | Decisión / opciones | Propuesta inicial | Evidencia / pregunta |
|---|---|---|---|
| G01 | Estructura principal y terminador. | `ID declaraciones BEGIN sentencias END`, sin `;` final. | TP2 p. 1: ejemplo del programa. Confirmar si se admite también `END;`. |
| G02 | Cardinalidad de declaraciones y sentencias. | Cero o más declaraciones; una o más sentencias en bloques ejecutables. | La consigna no precisa todos los vacíos. Preguntar por programa, cuerpo de función y clase vacíos. |
| G03 | Qué producción consume cada `;`. | Las sentencias simples consumen su `;`; IF y REPEAT el suyo; bloque BEGIN/END no añade uno; funciones y clases terminan en `END;`. | TP2 pp. 1–3. Revisar casos anidados y exportación. |
| G04 | Tipos de variables. | INTEGER/SINGLEF para básicos; `ID lista_ids;` para objetos cuando se agreguen clases. | Temas 3 y 7, declaración de objetos TP2 p. 2. El léxico no necesita token ID_CLASE. |
| G05 | Posiciones de declaraciones. | Antes del BEGIN ejecutable de programa y función; miembros en cuerpo de clase. No introducir declaraciones en cualquier bloque ejecutable. | Estructura general TP2 pp. 1–2; aclarar clases anidadas y declarativas admitidas dentro de funciones. |
| G06 | COMPTIME. | `COMPTIME tipo_basico lista_ids ;` en zonas declarativas permitidas. | Tema 22. Consultar si también aplica a objetos o atributos; no implementarlo ejecutando código en TP2. |

## 3. Expresiones, condiciones y asignaciones

| ID | Decisión / opciones | Propuesta inicial | Evidencia / pregunta |
|---|---|---|---|
| G07 | Precedencia y asociatividad aritmética. | `*` y `/` antes de `+` y `-`; asociatividad izquierda mediante niveles expresión/término/factor. | Propuesta convencional que debe registrarse. Revisar `a-b-c` y `a+b*c`. |
| G08 | Paréntesis de agrupación libre. | No agregar `factor → (expresion)` en la propuesta inicial. | TP2 p. 2 prohíbe anidamiento y tema 17 dice usar paréntesis para esa asignación. Aclarar si se admite alguna agrupación libre sin anidar. |
| G09 | Signos unarios. | Menos ante constantes; resta como operador binario. No agregar `-ID` ni `+CTE` sin regla expresa. | TP1/TP2 distinguen signo de constante y resta. Rango final de 32768 depende del signo (TP2 p. 9). |
| G10 | Operador de asignación por contexto. | `ID := expresion;` exterior; `ID = (expresion)` interior tema 17; escritura posicional con `=` según tema 29. | Preguntar si `:=` también escribe atributos y si `=` exterior admite ID en algún caso. No aceptar ambos en todas partes. |
| G11 | Destino de una asignación interna. | Inicialmente ID, como los ejemplos del tema 17. | Consultar si también puede ser un atributo posicional. |
| G12 | Restricción «sin anidamiento» del tema 17. | Dos familias de expresión: general y sin asignaciones internas; el lado derecho de la asignación interna usa la segunda. | Aclarar si la prohibición se propaga a argumentos y TOI dentro de ese lado derecho. Una regla recursiva indiscriminada reintroduciría el anidamiento. |
| G13 | Condiciones. | Una comparación entre dos expresiones; comparador entre `> < >= <= == !=`. | TP2 p. 3. No agregar comparaciones encadenadas, AND, OR ni booleanos como nuevas construcciones. |
| G14 | TOI. | Factor `TOI ( expresion )` y, por lo tanto, utilizable dentro de expresiones. | Tema 34. El control/conversión de tipos corresponde a etapas posteriores; revisar G12. |

### Ejemplos para precisar G08–G12

Son fragmentos; cuando corresponda, rodearlos de un programa completo para probar.

| Fragmento | Estado esperado / duda |
|---|---|
| `a := b=(2$i+c);` | Forma del tema 17: propuesta válida. |
| `a := b+c=(4$i);` | Tema 17 incluye asignación como operando dentro de una expresión. |
| `a := b=(c+d)*e=(c/3$i);` | Dos asignaciones internas al mismo nivel: ejemplos del tema 17 permiten esta forma. |
| `a := b=2$i;` | Corresponde al tema 18, no al grupo; rechazar. |
| `a := b:=(2$i);` | Inválido explícito del tema 17. |
| `a = b=(2$i);` | Inválido explícito del tema 17 para asignación exterior a ID. |
| `a := b=(c=(1$i));` | Anidamiento directo que la propuesta rechaza. |
| `a := b=(toi(c=(1.0)));` | Consultar alcance de prohibición transitiva a través de conversiones. |
| `a := (b+c);` | No admitido por la base provisional; consultar G08 antes de fijar el lenguaje final. |
| `a := -32768$i;` | Sintaxis válida; verificación final de rango debe admitirla. |
| `a := 32768$i;` | Forma reconocible, pero falla el control de rango positivo exigido en TP2. |

Al formalizar «expresión sin asignaciones internas», también deben existir
versiones compatibles de llamadas, argumentos y conversiones si se acuerda
prohibir asignaciones internas indirectas. El nombre del no terminal por sí solo
no hace cumplir la restricción.

## 4. Control, funciones y llamadas

| ID | Decisión / opciones | Propuesta inicial | Evidencia / pregunta |
|---|---|---|---|
| G15 | IF y REPEAT. | Rama/cuerpo de una sentencia o BEGIN/END; ELSE opcional y END_IF obligatorio; REPEAT/UNTIL del tema 12. | TP2 p. 3. Retener el cierre explícito de IF y probar anidamiento. |
| G16 | Funciones y formales. | `<tipo> FUNCTION ID(<formales>) <declaraciones> BEGIN <cuerpo> END;`; al menos un formal; permitir funciones anidadas. | Requisitos TP2 pp. 1–2. Diferenciar función de método, que se muestra sin FUNCTION. |
| G17 | Tipos de parámetros. | Básicos para funciones; admitir tipo clase en métodos según ejemplos del tema 26; consultar unificación de ambos. | TP2 p. 6 incluye `m2(A a1)`; usar identificadores minúsculos al adaptar ejemplos al grupo. |
| G18 | RET y contextos. | Dos familias de sentencias/bloques: globales y de función/método. Sólo las segundas incluyen RET y propagan el permiso a IF/REPEAT. | Funciones pueden tener cero, uno o varios retornos (TP2 pp. 1–2). No incorporar requisito AUTO del tema 21. |
| G19 | Orden obligatorio de argumentos. | Toda llamada a función debe tener su lista de orden posterior entre corchetes. | Tema 19, TP2 p. 4. Consultar sintaxis exacta de constantes y aplicación a métodos. |
| G20 | Sintaxis del orden. | Mantener `<lista_orden>` como decisión separada hasta aclarar `[1,2]` frente a `[1$i,2$i]`. | TP1 exige sufijos; ejemplos del tema 19 no los usan. Afecta L07 y catálogo léxico. |
| G21 | Listas de argumentos y orden: forma frente a significado. | Expresiones separadas por coma; fijar cardinalidad mínima. Chequeos de correspondencia con formales, permutación y valores del orden requieren definición de etapa. | El tema difiere su semántica a etapas posteriores; no inventar esas reglas ni rechazos en AL. |
| G22 | Llamadas como sentencias independientes. | Admitir métodos solos por el ejemplo del tema 26; consultar funciones solas y sus terminadores. | Descripción general muestra principalmente llamadas como operandos, pero TP2 p. 6 muestra `a1.m1(...);`. |

El ejemplo `f2(a=1$i,...)[2,3,1]` del tema 19 usa la forma del tema 18. Al combinar
nuestros temas 17 y 19, la asignación interna del argumento requiere paréntesis,
por ejemplo `f2(a=(1$i),b+3$i,5$i)[<orden>]`. El marcador `<orden>` no es código
válido: evita decidir silenciosamente la grafía pendiente de los índices.

## 5. Clases, objetos y temas particulares

| ID | Decisión / opciones | Propuesta inicial | Evidencia / pregunta |
|---|---|---|---|
| G23 | Cuerpo de clase. | `CLASS ID [importacion] BEGIN miembros END;`, con importación opcional en este esquema. | Algunos ejemplos generales omiten BEGIN de clase; los del tema 26 lo incluyen. Confirmar obligatoriedad. |
| G24 | Miembros permitidos. | Atributos, métodos, declaración de herencia y formas import/export correspondientes. | Formalizar orden y repetición; no agregar clases anidadas o FUNCTION para métodos por analogía. |
| G25 | Exportación y punto y coma. | Proponer atributos `tipo lista_ids [EXPORT TO lista_clases] ;`; métodos terminan con `END;` y una exportación opcional `EXPORT TO lista_clases;`. | TP2 p. 6 alterna exportación antes/después de `;` para atributos. Requiere consulta, no gramática que acepte todo por defecto. |
| G26 | Importación. | `IMPORT FROM lista_clases` después del nombre de clase y antes de BEGIN, sin `;` adicional según ejemplo. | Tema 26. Referencias a clases se verifican semánticamente después. |
| G27 | Acceso posicional a atributos. | `ID [ indice ]`, con índice ID o constante; el texto no autoriza cualquier expresión como índice. | Tema 29 permite constantes o variables. Consultar tipos/signo del índice y etapa de sus controles. |
| G28 | Acceso a métodos. | `ID . ID(<argumentos>)`, con el posible sufijo de orden pendiente de G19. | El tema 29 cambia acceso a atributos; no dice reemplazar el punto de métodos. |
| G29 | Herencia. | Incluir `EXTENDS lista_clases ;` dentro de la clase; postergar desambiguación opción 3. | Parte común de temas 30–32, TP2 p. 7. Descripción dice `extend`, ejemplo `extends`: confirmar grafía. |
| G30 | Funcionalidades no asignadas. | No incorporar atributos por nombre del tema 28, prefijado del tema 31, amigos, AUTO, typedef u otras variantes salvo regla general aplicable aclarada. | Respetar combinación del grupo; TP2 p. 8 difiere la opción 32 a TP3. |

Los corchetes usados para **opcionalidad en los esquemas de G23/G25** no son
caracteres del programa. En G27 y en llamadas con orden sí son delimitadores
literales. La gramática formal usará notación que distinga ambos usos.

## 6. Construcción y validación del parser

| ID | Decisión / opciones | Propuesta inicial | Criterio de cierre |
|---|---|---|---|
| G31 | BNF, EBNF y traducción al generador. | BNF legible en el diseño; convertir listas/opcionales a reglas explícitas para la herramienta elegida. | Todos los no terminales definidos, alcanzables y descritos en el informe. |
| G32 | Precedencia estructural o declaraciones del generador. | Niveles expresión/término/factor para que la agrupación sea visible. | No resolver conflictos arbitrariamente con precedencia sin entender qué lenguaje/árbol resulta. |
| G33 | Manejo de conflictos. | Generar reportes, identificar ejemplos que los disparan y corregir gramática/precedencia según decisiones. | Cero conflictos shift/reduce y reduce/reduce pendientes, como exige TP2 p. 9. |
| G34 | Resultado del reconocimiento. | Registrar estructuras detectadas con su línea. AST completo es opción de diseño futuro, no requisito explícito de esta entrega. | Capturar línea de comienzo de la estructura, no la línea global del último token leído. |
| G35 | Recuperación sintáctica. | Definir puntos de sincronización por contexto: `;`, END, ELSE, END_IF, UNTIL u otros que correspondan. | Continuar sin consumir ciegamente cierres de estructuras externas; diagnosticar varios errores. |
| G36 | Pruebas y no regresión. | Cada producción/restricción con ejemplo válido e inválido, más interacciones entre temas. | Probar entrada completa y EOF, diagnósticos, líneas, referencias TS y ausencia de conflictos. |

Ejemplos mínimos para revisar la interpretación de precedencia:

```text
a := 1$i + 2$i * 3$i;
a := 8$i - 3$i - 1$i;
a := 8$i / 2$i / 2$i;
```

La agrupación propuesta corresponde a `1+(2*3)`, `(8-3)-1`, `(8/2)/2`.
Esos paréntesis son explicación de estructura, no sintaxis fuente admitida.
En TP2 se necesita reconocer dicha estructura; no es necesario ejecutar esas
operaciones para considerar probada la sintaxis.

## 7. Agenda de cierre

1. Prioridad alta: G08, G10, G12, G19–G20, G25 y G29, porque afectan formas
   válidas, tokens o interacciones difíciles de cambiar tarde.
2. Resolver vacíos, formales, tipos de parámetros y contextos declarativos.
3. Ratificar la base y añadir funciones/retornos/llamadas.
4. Integrar tema 17 y después clases con temas 26/29/32.
5. Generar parser, eliminar conflictos y agregar recuperación con pruebas.

Al registrar una respuesta del docente, conservar fecha, pregunta concreta y
ejemplo que cambia; actualizar la producción y el catálogo léxico afectados.
No hace falta bloquear todas las partes del diseño mientras quedan preguntas
independientes pendientes. Ninguna de estas consultas se envió a terceros.

## Fuentes de referencia

Las páginas mencionadas corresponden al PDF contado desde 1. Los materiales
se identifican por su nombre para consultar las copias proporcionadas por la cátedra.

- **TP1:** `Tp01-2026.pdf` (3 páginas), consigna léxica de 2026.
- **TP2:** `Tp02-2026.pdf` (9 páginas), sintaxis y temas particulares de 2026.
- **T:** `03.Análisis Léxico.pdf` (77 páginas), teoría de la cátedra.
- **P:** `Presentacion TP1- Compiladores 2026.pdf` (40 páginas).
- **Grupo:** [Informe del grupo 40](https://docs.google.com/document/d/1BkzEz_rgfqBG1hilX8VvjYJVZF7BAFCQrXNVjToD9vk/edit), temas 3, 7, 10, 12, 15, 17, 19, 22, 26, 29, 32 y 34.

Los ejemplos de teoría enseñan mecanismos; las consignas de 2026 y los temas
asignados determinan el lenguaje del proyecto. Las discrepancias están registradas
como consultas pendientes.
