# Analizador léxico: decisiones, opciones y contrato propuesto

Grupo 40 — revisión inicial del 14/09/2026. No hay decisiones de implementación
ratificadas por el grupo. **Requisito** viene de la consigna; **propuesta** es
una recomendación; **consulta** necesita aclaración. Las fuentes se detallan al
final de este documento. La gramática y su catálogo léxico deben evolucionar juntas.

## Estado del prototipo

Se implementó un léxico SLY de apoyo a la gramática. Las opciones concretas y
sus límites están en [implementación](../gramatica/implementacion.md). Las tablas
siguientes conservan el catálogo original para ratificación; no todas sus
opciones pendientes implican falta de implementación. La consulta sobre matrices
sigue abierta.

## 1. Requisitos que delimitan las opciones

- Entrada desde un archivo cuya ruta recibe la aplicación por consola (TP1 p. 1).
- Líneas numeradas desde 1; tokens en orden; errores y warnings con ubicación;
  tabla de símbolos dinámica con identificadores, constantes y cadenas.
- Identificadores de hasta 22 caracteres; comienzan por letra y continúan con
  letras, dígitos o `_`; sólo letras minúsculas. Exceso: truncamiento con warning.
- INTEGER de 16 bits con sufijo `$i` y SINGLEF del tema 7.
- Cadenas multilínea entre comillas dobles; guardar su contenido sin saltos de línea.
- Comentarios `//`, blancos, tabs y saltos de línea fuera de cadenas se descartan
  del flujo de tokens, manteniendo el conteo de líneas.
- Reconocer símbolos y reservadas generales y los que agregan nuestros temas.
- Para TP2: referencias a la TS en tokens con atributos, manejo de signo/rango
  con el parser y continuación después de errores (TP2 p. 9).
- Entrega: código, ejecutable/forma ejecutable con dependencias necesarias,
  informe y casos de prueba. Si se usa GitHub, el repositorio debe ser privado.
- Matrices de estados/acciones exigidas por TP1 p. 1; TP1 p. 2 y P 30/34 también
  contemplan expresiones regulares con SLY. Resolver esa aplicación con el docente.

Los ejemplos teóricos con `/* */`, `<>`, THEN, WHILE o identificadores con
mayúsculas no amplían el lenguaje de nuestro grupo.

## 2. Herramienta y organización

| ID | Decisión y opciones | Propuesta inicial | Estado / forma de cierre |
|---|---|---|---|
| L01 | Python + SLY; Java + BYACC/J; C + Bison. | Python + SLY por familiaridad y rapidez. Java + BYACC/J es alternativa directa para matrices. | Pendiente: acuerdo del grupo y resolución de L02. |
| L02 | Léxico mediante matrices o patrones/acciones de SLY. | Si SLY sustituye las matrices según la cátedra, usar esa alternativa. Si matrices son obligatorias, implementar explícitamente el autómata y adaptar su salida al parser elegido. | Consulta prioritaria sobre TP1 p. 1 frente a TP1 p. 2/P 30. |
| L03 | Versiones y distribución de dependencias. | Fijar Python/SLY o JDK/generador; probar un ejemplo mínimo en las tres computadoras y registrar el comando reproducible. | Pendiente. SLY fue retirado en 2025; no asumir compatibilidad sin probar. |
| L04 | Archivo completo en memoria o lectura por bloques. | Leer completo para este TP; simplifica cursor, retroceso y ubicaciones. | Pendiente: tamaño de entrada y codificación. |
| L05 | Tira completa antes del parser o entrega incremental. | Iterador que conserva estado y entrega tokens; consumidor de prueba para TP1. Se puede materializar para depurar si es útil. | Pendiente: compatibilidad con herramienta y modalidad pedida. |
| L06 | Responsabilidades de los módulos. | Separar lector/ubicaciones, léxico, TS, diagnósticos y ejecutable de consola. Evitar estado global persistente entre compilaciones. | Pendiente: definir interfaces antes de dividir tareas. |

SLY soporta Lexer y Parser separados, LALR(1), precedencia y recuperación;
ver [documentación oficial](https://github.com/dabeaz/sly/blob/master/docs/sly.rst).
El [repositorio](https://github.com/dabeaz/sly) anuncia retiro el 21/12/2025.
El prototipo usa SLY 0.5 en una .venv local. La recomendación sigue siendo
específica para este TP y está sujeta a revisión de la cátedra.

### L36. Representación de las reglas y vínculo con las acciones

**Pendiente:** decidir dónde se definen las reglas ejecutables y cómo se
asocian con el código que trata los símbolos. Depende de L01 y L02.

| Alternativa | Dónde se representa el reconocimiento | Cómo se ejecutan las acciones |
|---|---|---|
| Matrices explícitas | Tablas de transición por estado/clase de carácter. | Matriz de referencias a funciones o mecanismo equivalente; se ejecuta la acción elegida para cada transición. |
| SLY | Patrones de tokens en la clase Lexer. | Métodos asociados a reglas cuando se necesitan validación, registro o diagnóstico; los símbolos simples pueden tener sólo un patrón. |

Propuesta: mantener juntas las reglas de reconocimiento del léxico y delegar
registro/consulta a la TS y diagnósticos a sus componentes. En el caso manual,
se pueden separar las matrices en otro módulo si facilita revisarlas.

La documentación Markdown y el PDF especifican el comportamiento para los
humanos; no son configuración que el lexer lea automáticamente al ejecutar.
El programa fuente es una entrada diferente de la especificación del compilador.
La gramática sintáctica se implementa en el parser, no en el motor del léxico.

Ejemplo de contrato: el patrón de CTE_ENTERA reconoce `[0-9]+\$i`; su acción
valida la magnitud provisional de TP2, registra/recupera la constante y transmite
la referencia. Reconocer el patrón no resuelve el rango, el signo inicial ni la
validez de la sentencia que contiene esa constante.

Cierre: elegir representación, ubicación y responsables; mostrar un recorrido
`7$i;` desde reconocimiento hasta referencia TS, con `;` disponible para el
siguiente token. En matrices, conservar la exigencia de que estado/entrada
seleccionen transición y acción, evitando condiciones externas ocultas.

## 3. Catálogo de tokens candidato

Los nombres de token son una propuesta. Mantener una definición compartida con
el parser; no copiar los códigos numéricos de los ejemplos teóricos.

| Familia | Lexemas / tokens | Origen |
|---|---|---|
| Identificadores | ID | TP1. |
| Constantes | CTE_ENTERA, CTE_SINGLE | Temas 3 y 7; se propone distinguir tipos. |
| Cadenas | CADENA | Tema 10; una cadena entera produce un token. |
| Reservadas generales | IF, ELSE, END_IF, BEGIN, END, POUT, RET, CLASS, FUNCTION | TP1/TP2. |
| Tipos | INTEGER, SINGLEF | Temas 3 y 7. |
| Control | REPEAT, UNTIL | Tema 12. |
| Declaración | COMPTIME | Tema 22. |
| Clases | IMPORT, FROM, EXPORT, TO | Tema 26. |
| Herencia | EXTENDS, grafía pendiente | Parte común de temas 30–32. |
| Conversión | TOI | Tema 34 con INTEGER. |
| Aritméticos | `+`, `-`, `*`, `/` | General. |
| Asignación | `:=`, `=` | Ambos se reconocen; su distribución es sintáctica. |
| Comparadores | `>=`, `<=`, `>`, `<`, `==`, `!=` | General. |
| Delimitadores | `(`, `)`, `,`, `;`, `[`, `]` | General y temas 19/29. |
| Punto | `.` | Acceso a métodos; comparte prefijo con flotantes como `.6`. |
| Fin | Mecanismo EOF del generador | No usar el carácter `$` como centinela. |

Consulta: el orden de argumentos aparece como `[1,2]` en TP2 p. 4, sin sufijos.
No agregar enteros sin sufijo al lenguaje general sin resolverlo. Si se acuerda
un token NUM_ORDEN, el léxico puede reconocer dígitos sin sufijo y la gramática
restringir dónde son válidos; sería un cambio explícito del catálogo.

Los comentarios y los separadores no generan tokens para el AS. No agregar
SHORTINT, DOUBLEF, TYPEDEF, AUTO, PRIVATE, FRIEND u otras opciones de grupos ajenos.

## 4. Reconocimiento, prioridad y ubicaciones

| ID | Decisión y opciones | Propuesta inicial | Estado / comprobación |
|---|---|---|---|
| L07 | Código numérico, enum o nombre para cada categoría. | Adaptarse al generador manteniendo nombres únicos compartidos. No fijar números manuales divergentes. | Pendiente: L01. |
| L08 | Atributos de cada aparición. | Tipo, referencia TS cuando corresponda, posición de inicio; conservar lexema original para diagnóstico. | Pendiente: cerrar contrato de sección 7. |
| L09 | Reservadas en mayúsculas, minúsculas o cualquier mezcla. | Consultar una TPR normalizando sólo para la búsqueda; reconocer primero la palabra completa. | Confirmar variantes mixtas; ejemplos como END_if sugieren esa admisión. |
| L10 | Alfabeto de ID: ASCII o Unicode. | Proponer ASCII `[a-z]`, documentarlo y consultar qué entiende la cátedra por letra. | Consulta: no ampliar silenciosamente a letras Unicode por usar `isalpha`. |
| L11 | Identificador largo. | Consumir completo, truncar nombre efectivo a 22, emitir warning con original y efectivo. Nunca tokenizar el resto como otro ID. | Truncamiento es requisito; representación pendiente. |
| L12 | Colisión de dos nombres tras truncamiento. | Hacer explícita la colisión: mismo nombre efectivo en el registro léxico, diagnósticos con originales; revisar política de duplicados en etapas siguientes. | Consulta si se exige diagnóstico adicional. No desambiguar inventando sufijos. |
| L13 | Líneas, columnas, tabs, CRLF y CR. | Líneas desde 1. Añadir columna por carácter y offsets; tab cuenta un carácter en esa convención. Normalizar CRLF/CR a LF para análisis y documentarlo. | Pendiente: distinguir posiciones originales si se necesitan offsets del archivo bruto. |
| L14 | Codificación, BOM y bytes inválidos. | UTF-8; acordar si se tolera BOM inicial y reportar errores de decodificación claramente. | Pendiente: ejemplos reales en las tres máquinas. |
| L15 | Prefijos comunes: `>=`/`>`, `==`/`=`, `/`/`//`, `.`/`.6`. | Diagramar o priorizar la alternativa más larga válida antes de la corta y probarlas juntas. | Revisión obligatoria de reglas, no asumir prioridad automática. |
| L16 | Mirar sin consumir o retroceder. | En reconocimiento manual, usar cursor consistente; en SLY, respetar su gestión de índices. | Probar delimitadores contiguos y saltos de línea; no contar dos veces. |
| L17 | Fronteras de palabras y números mal formados. | Consumir candidatos suficientes para no aceptar accidentalmente un prefijo válido y ocultar el resto inválido. | Decidir comportamiento de `7$ix`, `1.2s`, `123abc`, `a@b` con mensajes esperados. |

## 5. Constantes, cadenas y tabla de símbolos

| ID | Decisión y opciones | Propuesta inicial | Estado / comprobación |
|---|---|---|---|
| L18 | Token único CTE con atributo de tipo o tokens separados. | CTE_ENTERA y CTE_SINGLE; simplifica restricciones y diagnósticos. La teoría permite ambas (T 63). | Pendiente de acuerdo con gramática. |
| L19 | Enteros y signo. | AL entrega `-` separado y magnitud con `$i`; acepta 0…32768 provisionalmente. AS rechaza 32768 positivo y admite −32768. | Requisito de TP2 p. 9; probar también 32769 y menos aritmético sin espacios. |
| L20 | Representación y validación SINGLEF. | Conservar lexema, analizar mantisa/exponente sin perder información y validar con representación decimal/rango explícito antes de redondear si hiciera falta. | Aclarar extremos abiertos del enunciado, redondeo, subnormales y cero. |
| L21 | Signo de exponente. | Parte del token numérico: `-1.2s-3` se separa en MENOS y CTE_SINGLE(`1.2s-3`). | No usar un patrón que absorba indiscriminadamente el menos inicial. |
| L22 | Igualdad y claves de constantes. | Inicialmente `(categoría, tipo, lexema normalizado documentado)`; evitar equiparar por float del host `1.0` y `1.00` sin decidirlo. | Definir ceros iniciales, signo, notaciones equivalentes y estabilidad de referencias. |
| L23 | Cadenas y normalización. | Guardar contenido sin delimitadores ni saltos, conservando espacios/tabs; contar todas las líneas consumidas y mantener inicio del token. | Quitar saltos es requisito; contenido frente a lexema bruto es propuesta. |
| L24 | Escapes en cadenas. | No agregar `\"`, `\n` u otros escapes sin especificación. Consultar cómo representar comillas literales, si se requiere. | Consulta: cadenas vacías y alfabeto permitido tampoco están detallados. |
| L25 | TPR separada o precargada en TS. | TPR separada y TS para ID, constantes y cadenas. Ambas alternativas existen en T 59–60. | Pendiente. |
| L26 | Estructura de TS. | Diccionario para búsqueda y entradas con referencias estables; operaciones de registro/consulta; tabla nueva por compilación. | Pendiente: enteros de referencia, claves o referencias a objetos. |
| L27 | Reutilización de entradas y ámbitos futuros. | Reutilizar registros léxicos, conservar ubicación por aparición y prever atributos semánticos/ámbitos sin resolverlos en AL. | No confundir igualdad del nombre con misma declaración. |
| L28 | Constantes negativas y referencias compartidas. | Crear/reutilizar entrada firmada y actualizar el atributo de esa aparición, sin mutar globalmente la magnitud que usan otros tokens. | Coordinar con AS antes de implementar L22. |

### Formas numéricas que debemos implementar

Patrones orientativos, no reglas de SLY ya verificadas:

```text
CTE_ENTERA: [0-9]+\$i
CTE_SINGLE: [0-9]*\.[0-9]+(s[+-]?[0-9]+)?
```

El segundo patrón permite omitir la parte entera, pero exige punto y al menos
un dígito decimal. No incluye el signo inicial; sí incluye el del exponente.
La detección de candidatos mal formados y sus fronteras se debe diseñar además
del patrón que reconoce entradas válidas.

TP1 p. 3 expresa el rango SINGLEF como:

```text
1.17549435s-38 < x < 3.40282347s+38
o -3.40282347s+38 < x < -1.17549435s-38
o x = 0.0
```

Se transcriben los intervalos abiertos del enunciado; L20 requiere aclarar sus
fronteras y relación con redondeo/representación antes de elegir aceptación
de valores límite. No sustituirlos por los límites de un float del host.

## 6. Errores, salida y entrega

| ID | Decisión y opciones | Propuesta inicial | Estado / comprobación |
|---|---|---|---|
| L29 | Detenerse, descartar o reparar frente a cada error. | Continuar con diagnóstico y avance controlado. Reparar sólo cuando el comportamiento esté especificado, como truncamiento. | Continuar es requisito; mecanismo pendiente por error. |
| L30 | Recuperación de números inválidos. | No entregar como válida una constante parcial. Elegir frontera y decidir qué carácter se conserva para el token siguiente. | Casos: sufijo incompleto, exponente incompleto, rango excedido. |
| L31 | EOF dentro de cadena y comentario. | Cadena sin cerrar: error con ubicación de apertura; comentario `//` puede terminar en EOF. | EOF normal tras un token no debe perder ese token. |
| L32 | Tokens inválidos en el flujo. | No enviar tokens normales para fragmentos inválidos; diagnosticar y continuar. Si se propone un token ERROR, acordarlo con AS. | Registrar errores aunque luego se reconozca el resto. |
| L33 | Diagnóstico estructurado. | Fase, severidad, código estable, línea/columna, descripción, fragmento y acción tomada. | Línea/descripción son requisito; resto propuesta. |
| L34 | Listados, archivos de salida y estado de proceso. | Reportes legibles y deterministas; consola inicialmente. Si se generan archivos, ubicarlos junto al fuente según TP1. Salida no exitosa si hay errores. | Elegir nombres, política para warnings y código de salida. |
| L35 | Evidencia e informe. | Conservar diagrama, matrices o patrones/acciones, errores, pruebas y decisiones; registrar IA/prompts/partes de código cuando se genere código. | Probar ejecución en otra PC; verificar privacidad de GitHub. |

«Modo pánico» y reparación de T 74 son técnicas posibles. Una reparación no
prescrita no se convierte en regla del TP por aparecer en la teoría. El léxico
debe avanzar o finalizar en cada iteración, incluso en una entrada inválida.

## 7. Contrato propuesto entre componentes

Modelo conceptual, a adaptar a la herramienta:

```text
Token:
    tipo
    referencia_ts opcional
    lexema_original opcional para diagnóstico
    linea_inicio
    columna_inicio opcional
    offset_inicio y offset_fin opcionales

EntradaTS:
    referencia estable
    categoria (identificador / constante / cadena)
    lexema_efectivo o contenido
    tipo_literal opcional
    valor_literal opcional
    estado_validacion opcional (p. ej., magnitud pendiente de signo)
    atributos_semanticos futuros
```

No asignar el tipo de una declaración a un ID desde AL por haber visto INTEGER
antes: eso mezcla estructura con reconocimiento. No guardar el valor de ejecución
de las variables durante el léxico. En SLY se puede transportar la referencia en
`value`; en la interfaz Yacc, mediante `yylval`. Confirmar el adaptador elegido.

Invariantes para revisar:

1. El orden de tokens coincide con la fuente; no se agrupan por línea.
2. Cada referencia apunta a una entrada existente y estable.
3. Identificadores, constantes y cadenas reciben atributos; los símbolos fijos
   no necesitan entradas nuevas en la TS.
4. Los diagnósticos conservan la ubicación de cada aparición.
5. Una nueva compilación no reutiliza por accidente estado de la anterior.
6. Continuar después de un error no transforma el resultado global en éxito.

## 8. Matriz mínima de pruebas a preparar

| Área | Casos y resultado que debe acordarse |
|---|---|
| Entrada | Archivo vacío, inexistente, UTF-8 inválido, BOM, LF/CRLF/CR; con/sin salto final. |
| Identificadores | Longitudes 1, 21, 22 y 23; minúsculas/dígitos/`_`; inicio inválido; mayúsculas; dos originales que colisionan al truncarse. |
| Reservadas | Mayúsculas/minúsculas/mezcla; prefijos como `ifvariable`; no normalizar ID inválidos. |
| Enteros | 0, 32767, 32768, 32769; −32768 y −32769 con AS; ceros iniciales; sufijos incompletos/ajenos. |
| Flotantes | `1.0`, `.6`, `1.`, `.`, `1.0s2`, `1.0s+2`, `1.0s-2`, exponente incompleto; fronteras de rango, cero y magnitudes muy pequeñas. |
| Operadores | `:=`, `=`, `==`, `!=`, `!`, `:`, `<`, `<=`, `>`, `>=`; contiguos a nombres/números. |
| Comentarios | `//` vacío, comentario en EOF, `/` división, comillas dentro de comentario, `//` dentro de cadena. |
| Cadenas | Vacía pendiente, una/múltiples líneas, espacios conservados, saltos eliminados, EOF antes de cierre, escapes pendientes. |
| Temas particulares | Corchetes de orden y de atributos; punto de método frente a flotante; TOI, COMPTIME, IMPORT/EXPORT y herencia. |
| Recuperación | Error seguido de tokens válidos, varios errores, no bucle infinito, preservación de delimitadores y líneas. |
| TS | Reutilización consistente, cadenas frente a constantes, nombres repetidos, signo sin alterar otras apariciones, reinicio entre archivos. |

Son especificaciones de pruebas, no pruebas ejecutadas. Los extremos SINGLEF
deben obtenerse de la política acordada, no de una aritmética de float que cambie
el valor que se pretendía comprobar.

## 9. Orden de decisiones para la reunión

1. Resolver L01–L03 y consultas de gramática que cambian tokens.
2. Cerrar L07–L10 y el contrato con TS/parser.
3. Acordar números, cadenas, prioridad de patrones y fronteras inválidas.
4. Fijar recuperación y resultados esperados de pruebas.
5. Repartir componentes con una interfaz común y un consumidor mínimo de tokens.

Registrar al cerrar cada decisión: opción elegida, motivo, responsable, fecha,
ejemplo que la demuestra y fuente/aclaración del docente si aplica. No marcar
una recomendación como acordada sólo por estar escrita en este archivo.

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
