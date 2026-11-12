# Gramática ejecutable propuesta — Grupo 40

La propuesta inicial se implementó como un parser **SLY LALR(1)**. Se puede
ejecutar desde un archivo, inspeccionar el árbol y ver los errores. Las reglas
cubren las formas generales y los temas asignados bajo las interpretaciones
provisionales de [implementacion.md](implementacion.md).

No es una confirmación de las reglas ambiguas por parte de la cátedra. Las
opciones y preguntas originales se conservan en [decisiones.md](decisiones.md).
Este documento describe el prototipo, no una entrega final aprobada.

## 1. Dónde leer las reglas reales

- [parser.py](../../compiler_frontend/parser.py): producciones y acciones Python.
- [gramatica.bnf](gramatica.bnf): todas las producciones exportadas del parser.
- [lexer.py](../../compiler_frontend/lexer.py): categorías y patrones de tokens.
- [Ejemplo completo](../../examples/grupo40.src): construcciones de nuestro grupo.
- [Pruebas](../../tests/test_grammar.py): entradas admitidas/rechazadas y estructura del árbol.

`parser.py` es la fuente ejecutable de las reglas. Para mantener la BNF alineada:

```sh
python scripts/export_grammar.py
python scripts/export_grammar.py --check
```

La BNF usa nombres de terminales o caracteres literales. `<empty>` representa
una secuencia vacía. `error` es el símbolo de recuperación de SLY y no un token
que el programador escriba. `S'` es el inicio aumentado agregado por el generador.

## 2. Cómo leer una producción

```text
program -> ID declarations BEGIN global_statements END
```

Un programa contiene un nombre, declaraciones y un bloque ejecutable.
`ID`, `BEGIN` y `END` son terminales que entrega el léxico. `declarations` y
`global_statements` son estructuras definidas por otras producciones.

```text
declarations -> <empty>
declarations -> declarations declaration
```

Se permiten cero o más declaraciones. En cambio, `global_statements` y
`function_statements` requieren al menos una sentencia.

Las palabras reservadas se reconocen sin distinguir mayúsculas/minúsculas;
los identificadores deben escribirse en minúsculas. La columna del token refiere
al texto normalizado de entrada, con líneas y columnas que comienzan en 1.

## 3. Familias de no terminales

| Familia / no terminales | Responsabilidad |
|---|---|
| `program`, `declarations`, `declaration` | Raíz y zona declarativa, incluida recursión para funciones/clases locales. |
| `basic_type`, `parameter_type` | Tipos básicos y nombres de clase admitidos en parámetros. |
| `id_list`, `variable_declaration`, `object_declaration`, `comptime_declaration` | Listas de variables y formas de declaración. |
| `function_declaration`, `parameters`, `parameter` | Funciones, al menos un formal y declaraciones locales. |
| `class_declaration`, `import_opt`, `members`, `member` | Clases con importación opcional y uno o más miembros. |
| `attribute_declaration`, `method_declaration` | Atributos básicos y métodos, estos últimos sin FUNCTION. |
| `export_opt`, `method_export_opt`, `inheritance` | Exportación y declaración de herencia múltiple. |
| `global_statements`, `global_statement`, `global_block`, `global_if`, `global_else`, `global_repeat` | Sentencias y bloques que no admiten RET. |
| `function_statements`, `function_statement`, `function_block`, `function_if`, `function_else`, `function_repeat`, `return_statement` | Contextos que admiten RET y lo propagan a bloques anidados. |
| `simple_statement`, `assignment`, `output` | Sentencias comunes, incluida recuperación con `error ;`. |
| `condition`, `comparator` | Una comparación entre dos expresiones. |
| `expression`, `term`, `factor` | Precedencia y asociatividad aritmética. |
| `conversion`, `inline_assignment` | TOI y asignación del tema 17 como operando. |
| `plain_expression`, `plain_term`, `plain_factor`, `plain_conversion`, `plain_invocation`, `plain_arguments` | Expresiones que no permiten ninguna asignación interna, directa o indirecta. |
| `attribute`, `index` | Acceso posicional con índice variable o constante. |
| `invocation`, `arguments`, `order`, `order_items` | Llamadas a función/método y orden obligatorio sin sufijos numéricos. |
| `number` | Constantes positivas/negativas y control final del límite INTEGER. |

Cada no terminal tiene producciones explícitas en la BNF exportada. El glosario
de familias es una guía para leerlas, no otra gramática independiente.

## 4. Cobertura de los temas

| Tema | Forma implementada |
|---|---|
| 3 | INTEGER, constantes con `$i` y rango con signo. |
| 7 | SINGLEF, punto decimal obligatorio, exponente `s` opcional y rango provisional documentado. |
| 10 | CADENA multilínea; se eliminan saltos de su valor. |
| 12 | REPEAT con UNTIL y condición entre paréntesis. |
| 15 | Comentarios `//` tratados por el léxico. |
| 17 | `ID = (plain_expression)` como operando; no anidable. |
| 19 | Orden obligatorio en funciones y métodos: `[1,2,...]`. |
| 22 | COMPTIME con tipo básico y lista de variables. |
| 26 | IMPORT FROM en cabecera y EXPORT TO en atributos/métodos. |
| 29 | Acceso posicional `objeto[indice]`, también como destino con `=`. |
| 32 | Sintaxis común EXTENDS; desambiguación semántica opción 3 pendiente de TP3. |
| 34 | TOI como factor dentro de cualquier expresión permitida. |

También se incluyen declaraciones generales, funciones anidadas, clases,
objetos, métodos, IF/ELSE/END_IF, POUT y RET. Los chequeos semánticos de esos temas
se difieren; por ejemplo, una llamada puede tener aridad incorrecta aunque su
forma sea reconocida por este parser.

## 5. Ejemplo y recorrido

```text
demo
integer precio;
begin
    precio := 7$i + 2$i * 3$i;
    pout(precio);
end
```

El léxico produce ID, INTEGER, ID, `;`, BEGIN, etc. El parser reconoce la
declaración y la asignación. El nivel `term` agrupa `2$i * 3$i` antes de la suma.
El árbol conserva esa agrupación: la expresión de la asignación es un nodo
`binary` de suma cuyo segundo operando es otro `binary` de multiplicación.

```sh
python -m compiler_frontend examples/minimo.src --tokens
python -m compiler_frontend examples/minimo.src --json
```

La asignación no se ejecuta: la TS no cambia el valor de ejecución de `precio`.
Se guardan los identificadores y constantes reconocidos y sus referencias.

## 6. Verificación y próximos pasos

Las tablas generadas tienen **256 estados y cero conflictos shift/reduce y
reduce/reduce**. La suite incluye 30 pruebas con subcasos; revisa también el árbol,
no sólo que el parser acepte entradas. La BNF exportada contiene todas las reglas,
incluida recuperación y el inicio aumentado del generador.

Pendiente para una entrega final:

1. Ratificar o corregir las interpretaciones con el grupo/docente.
2. Confirmar léxico SLY frente a matrices.
3. Ampliar recuperación de cabeceras/cierres y mensajes específicos.
4. Probar el entorno en las tres computadoras y preparar la distribución pedida.
5. Completar informe y revisión humana de la generación asistida por IA.

Las fuentes de las consignas están en [el índice de documentación](../README.md).
