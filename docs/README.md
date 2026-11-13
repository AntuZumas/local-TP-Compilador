# Documentación de diseño — Grupo 40

Estado actualizado a noviembre de 2026 (Segunda Entrega — TP1 a TP4): compilador
ejecutable en Python + SLY 0.5, verificado con 43 pruebas automatizadas, 24 casos
de prueba `.src`, tablas LALR(1) sin conflictos, generación de **Polaca Inversa** y
traducción a **Assembler 80x86/80x87 de 32 bits (MASM32)** con controles en tiempo de
ejecución (`a`, `c`, `d`, `g`).

- [Cómo ejecutarlo](../README.md).
- [Decisiones implementadas y límites](gramatica/implementacion.md).
- [BNF exportada del parser](gramatica/gramatica.bnf).
- [Registro de uso de IA](ia.md).

- [Decisiones del analizador léxico](analizador-lexico/decisiones.md): requisitos,
  alternativas, recomendaciones, contrato con el parser y pruebas necesarias.
- [Propuesta de gramática](gramatica/propuesta.md): notación, reglas ejecutables y cobertura
  de los temas asignados.
- [Decisiones de gramática](gramatica/decisiones.md): preguntas iniciales,
  ejemplos y criterios ratificados tras la devolución de la primera entrega.

## Fuentes

Los PDF son material de referencia y no se copian al repositorio con estos
documentos. Las páginas citadas son páginas del PDF, contadas desde 1.

| Código | Material |
|---|---|
| T | `03.Análisis Léxico.pdf`, 77 páginas: teoría de la cátedra. |
| TP1 | `Tp01-2026.pdf`, 3 páginas: requisitos léxicos de 2026. |
| TP2 | `Tp02-2026.pdf`, 9 páginas: sintaxis y temas particulares de 2026. |
| DEV | `Grupo 40 - Devolución TP1-2.docx`: correcciones de la cátedra sobre la primera entrega. |
| TP3 | `Tp03-2026.pdf`, 12 páginas: semántica, ámbitos (*name mangling*) y Polaca Inversa. |
| RCI | `Resumen Generación código intermedio.pdf`, 39 páginas: teoría de Polaca Inversa, Tercetos y Árbol Sintáctico. |
| TP4 | `Tp04-2026.pdf`, 4 páginas: generación de Assembler 80x86/80x87 y controles en tiempo de ejecución (`acdg`). |
| G | [Informe del grupo 40](https://docs.google.com/document/d/1BkzEz_rgfqBG1hilX8VvjYJVZF7BAFCQrXNVjToD9vk/edit): temas 3, 7, 10, 12, 15, 17, 19, 22, 26, 29, 32 y 34. |

## Resoluciones adoptadas tras la devolución de TP1/TP2 e integración de TP3/TP4

- **Alta de constantes con signo en TS:** el lexer valida el formato y tope absoluto (`<= 32768` en `INTEGER`, rango IEEE 754 en `SINGLEF`), difiriendo la inserción en la Tabla de Símbolos al parser para evitar que constantes negativas (`-1$i`, `-1.2`) dejen registrada su magnitud positiva si esta no figura en el programa.
- **Orden de evaluación (Tema 19) y atributos posicionales (Tema 29):** se unificó el uso de constantes enteras del grupo (`$i`) dentro de los corchetes de orden (`[2$i, 1$i]`), eliminando el token `ORDER_INDEX`, y se adoptó `:=` para la asignación a atributos posicionales (`obj[0$i] := expr;`).
- **Informe de estructuras y salida por consola:** las estructuras `IF` y `REPEAT` se registran en orden de finalización conservando su línea de inicio. La salida por defecto muestra diagnósticos unificados, Polaca Inversa y Tabla de Símbolos, generando el archivo `.asm` correspondiente.

## Convenciones de estado

- **Requisito:** está expresado en la consigna o en la devolución de la cátedra.
- **Implementado:** resuelto y verificado mediante pruebas unitarias y casos `.src`.
